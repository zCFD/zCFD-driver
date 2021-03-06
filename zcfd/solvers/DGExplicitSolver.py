"""
Copyright (c) 2012-2017, Zenotech Ltd
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Zenotech Ltd nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL ZENOTECH LTD BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from zcfd.utils import config
from zcfd.solvers.ExplicitSolver import ExplicitSolver
from zcfd.solvers.ExplicitSolver import InvalidSolution
from zcfd.solvers.utils.RuntimeLoader import load_solver_runtime
import math


class DGExplicitSolver(ExplicitSolver):

    """DG Explicit Solver"""

    def initialise(self):

        precond = config.parameters[self.equations]['precondition']

        if self.equations == 'DGeuler':
            config.logger.info('DG Euler Solver Initialise')
            config.solver_native = 0
            solver_type = "DGEULER"

        if self.equations == 'DGviscous':
            config.logger.info("DG Viscous Solver Initialise")
            config.solver_native = 0
            solver_type = "DGVISCOUS"

        if self.equations == 'DGLES':
            config.logger.info("DG LES Solver Initialise")
            config.solver_native = 0
            solver_type = "DGLESWALE"

        if self.equations == 'DGRANS':
            if config.parameters['DGRANS']['turbulence']['model'] == 'sst':
                config.logger.info("DG RANS SST Solver Initialise")
                config.solver_native = 0
                solver_type = "DGMENTER"
            if config.parameters['DGRANS']['turbulence']['model'] == 'sa-neg':
                config.logger.info("DG RANS SA-Neg Solver Initialise")
                config.solver_native = 0
                solver_type = "DGSANEG"

        precond = False

        self.parameter_update()

        self.solver = load_solver_runtime({"dg": True,
                                           "space_order": self.space_order,
                                           "type": solver_type,
                                           "medium": "air",
                                           "device": config.options.device,
                                           "precond": precond
                                           },
                                          config.parameters)

        if 'Nodal Locations' not in config.parameters:
            from zcfd.solvers.utils.DGNodalLocations import nodal_locations_default
            config.parameters.update(nodal_locations_default)

        num_mesh = config.parameters['time marching']['multigrid']
        self.solver.read_mesh(config.options.problem_name,
                              config.options.case_name, num_mesh)
        num_mesh = self.solver.init_storage()
        config.parameters['time marching']['multigrid'] = num_mesh
        config.cycle_info = self.solver.init_solution(config.options.case_name)

    def parameter_update(self):
        super(DGExplicitSolver, self).parameter_update()

        self.space_order = config.get_space_order(self.equations)

        if 'kind' in config.parameters['time marching']['scheme']:
            if config.parameters['time marching']['scheme']['kind'] == 'global timestepping':
                self.local_timestepping = False

        if 'multipoly' in config.parameters['time marching']:
            if config.parameters['time marching']['multipoly'] and not self.lusgs:
                self.PMG = True

        if 'cfl for pmg levels' in config.parameters['time marching']:
            tmp_list = config.parameters[
                'time marching']['cfl for pmg levels']
            if len(tmp_list) > self.space_order:
                self.cfl.cfl_pmg = tmp_list
                self.cfl.max_cfl = self.cfl.cfl_pmg[0]

        if 'cfl transport for pmg levels' in config.parameters['time marching']:
            tmp_list = config.parameters[
                'time marching']['cfl transport for pmg levels']
            if len(tmp_list) > self.space_order:
                self.cfl.transport_cfl_pmg = tmp_list
                self.cfl.transport_cfl = self.cfl.transport_cfl_pmg[0]

        if 'multipoly cycle pattern' in config.parameters['time marching']:
            self.pmg_pattern = config.parameters['time marching']['multipoly cycle pattern']

            for cycle in self.pmg_pattern:
                if cycle > self.space_order:
                    raise ValueError("Cycle pattern defined by \'multipoly cycle pattern\' incompatible with \'order\' - Please correct")

            if len(self.pmg_pattern) > 1:
                if self.pmg_pattern[0] > self.pmg_pattern[1]:
                    raise ValueError("\'multipoly cycle pattern\' does not appear to be correctly defined.  E.g. for a V-cycle with P2 as finest level use [0,1,2,1,0]")
        else:
            # Default is a V-cycle
            self.pmg_pattern = []
            for index in xrange(self.space_order + 1):
                self.pmg_pattern.append(index)
            for index in xrange(self.space_order - 1, -1, -1):
                self.pmg_pattern.append(index)

        self.finite_volume_solver = False

    def advance_solution(self, cfl, real_time_step, time_order, mesh_level):
        """
        """
        if (self.PMG and self.solve_cycle <= self.multigrid_cycles):

            # Perform time step at highest order (1)
            self.copy_solution()
            for rk_index in xrange(len(self.rk.coeff())):
                # Runge-Kutta loop
                valid = self.march(rk_index, self.rk.coeff()[rk_index], self.rk.rkstage_scaling()[rk_index], self.rk.time_leveln_scaling()[
                                   rk_index], cfl.pmg_cfl(0), cfl.pmg_transport(0), real_time_step, time_order, self.safe_mode, 0)
                if self.safe_mode and not valid:
                    raise InvalidSolution

            computeForcing = True
            for pmg_cycle in xrange(len(self.pmg_pattern) - 1):
                if self.pmg_pattern[pmg_cycle] < self.pmg_pattern[pmg_cycle + 1] and computeForcing:
                    # Restrict solution and residual to poly level below
                    # Compute force terms
                    self.solver.restrictToPolynomialLevel(self.pmg_pattern[pmg_cycle], self.pmg_pattern[pmg_cycle + 1], real_time_step, time_order, cfl.pmg_cfl(0))

                    # March lower level (4)
                    self.copy_solution()
                    for rk_index in xrange(len(self.rk.coeff())):
                        # Runge-Kutta loop
                        valid = self.march(rk_index, self.rk.coeff()[rk_index], self.rk.rkstage_scaling()[rk_index], self.rk.time_leveln_scaling()[rk_index], cfl.pmg_cfl(pmg_cycle), cfl.pmg_transport(pmg_cycle), real_time_step, time_order, self.safe_mode, self.pmg_pattern[pmg_cycle + 1])
                        if self.safe_mode and not valid:
                            raise InvalidSolution

                elif self.pmg_pattern[pmg_cycle] < self.pmg_pattern[pmg_cycle + 1] and not computeForcing:
                    self.solver.restrictSolutionOnlyToPolynomialLevel(self.pmg_pattern[pmg_cycle], self.pmg_pattern[pmg_cycle + 1])
                    # March lower level (4)
                    self.copy_solution()
                    self.update_halos(self.pmg_pattern[pmg_cycle + 1])
                    for rk_index in xrange(len(self.rk.coeff())):
                        # Runge-Kutta loop
                        valid = self.march(rk_index, self.rk.coeff()[rk_index], self.rk.rkstage_scaling()[rk_index], self.rk.time_leveln_scaling()[rk_index], cfl.pmg_cfl(pmg_cycle), cfl.pmg_transport(pmg_cycle), real_time_step, time_order, self.safe_mode, self.pmg_pattern[pmg_cycle + 1])
                        if self.safe_mode and not valid:
                            raise InvalidSolution

                elif self.pmg_pattern[pmg_cycle] > self.pmg_pattern[pmg_cycle + 1]:
                    self.solver.addPolyCorrections(self.pmg_pattern[pmg_cycle], self.pmg_pattern[pmg_cycle + 1])
                    if self.pmg_pattern[pmg_cycle + 1] != 0:
                        computeForcing = False
                        # March lower level (4)
                        self.copy_solution()
                        self.update_halos(self.pmg_pattern[pmg_cycle + 1])
                        for rk_index in xrange(len(self.rk.coeff())):
                            # Runge-Kutta loop
                            valid = self.march(rk_index, self.rk.coeff()[rk_index], self.rk.rkstage_scaling()[rk_index], self.rk.time_leveln_scaling()[rk_index], cfl.pmg_cfl(pmg_cycle), cfl.pmg_transport(pmg_cycle), real_time_step, time_order, self.safe_mode, self.pmg_pattern[pmg_cycle + 1])
                            if self.safe_mode and not valid:
                                raise InvalidSolution

                elif self.pmg_pattern[pmg_cycle] == self.pmg_pattern[pmg_cycle + 1]:
                    self.copy_solution()
                    self.update_halos(self.pmg_pattern[pmg_cycle + 1])
                    for rk_index in xrange(len(self.rk.coeff())):
                        # Runge-Kutta loop
                        valid = self.march(rk_index, self.rk.coeff()[rk_index], self.rk.rkstage_scaling()[rk_index], self.rk.time_leveln_scaling()[rk_index], cfl.pmg_cfl(pmg_cycle), cfl.pmg_transport(pmg_cycle), real_time_step, time_order, self.safe_mode, self.pmg_pattern[pmg_cycle + 1])
                        if self.safe_mode and not valid:
                            raise InvalidSolution

        else:
            self.copy_solution()
            for rk_index in xrange(len(self.rk.coeff())):
                # Runge-Kutta loop
                valid = self.march(rk_index, self.rk.coeff()[rk_index], self.rk.rkstage_scaling()[rk_index], self.rk.time_leveln_scaling()[
                                   rk_index], cfl.cfl, cfl.transport, real_time_step, time_order, self.safe_mode, 0)
                if self.safe_mode and not valid:
                    raise InvalidSolution

    def march(self, rk_index, rk_coeff, tk_scale, tn_scale, cfl, cfl_transport, real_time_step, time_order, safe_mode, polyLevel):
        config.logger.debug("Explicit March")
        valid = self.solver.march(rk_index, rk_coeff, tk_scale, tn_scale, cfl,
                                  cfl_transport,
                                  real_time_step, time_order, self.space_order, polyLevel, safe_mode)
        return valid

    def copy_solution(self):
        config.logger.debug("Copy solution")
        self.solver.copy_solution()

    def copy_time_history(self):
        self.solver.copy_time_history()

    def sync(self):
        self.solver.sync()

    def output(self, case_dir, case_name, surface_variable_list, volume_variable_list, real_time_cycle, solve_cycle, real_time, results_only):
        self.solver.output(case_name, surface_variable_list, volume_variable_list,
                           real_time_cycle, solve_cycle, real_time, results_only)

    def host_sync(self):
        self.solver.host_sync()

    def report(self):
        """
        """
        return self.solver.report()

    def calculate_rhs(self, real_time_step, time_order):
        self.solver.calculate_rhs(real_time_step, time_order, self.space_order)

    def add_stored_residual(self):
        self.solver.add_stored_residual()

    def store_residual(self):
        self.solver.store_residual()

    def add_const_time_derivative(self, real_time_step, time_order):
        self.solver.add_const_time_derivative(real_time_step, time_order)

    def restrict(self):
        self.solver.restrict()

    def update_halos(self, level):
        self.solver.update_halos(level, False)

    def prolongate(self, prolongation_factor, prolongation_transport_factor):
        self.solver.prolongate(prolongation_factor,
                               prolongation_transport_factor)

    def set_mesh_level(self, mesh_level):
        self.solver.set_mesh_level(mesh_level)
