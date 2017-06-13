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
from zcfd.solvers.utils.RuntimeLoader import load_solver_runtime


class MenterSSTSolver(ExplicitSolver):
    """Menter SST RANS Solver"""

    def initialise(self):
        config.solver_native = 0
        # Read in mesh
        #from libzCFDMeshEULERAIR import Mesh
        #m = Mesh()
        # m.read_mesh(config.options.problem_name)
        # Initialise solution (need ability for user to specify initialiser)

        # Initialise outputs
        transition = False
        if 'transition' in config.parameters['RANS']:
            if config.parameters['RANS']['transition'] == 'true':
                transition = True
        precondition = False
        if 'precondition' in config.parameters['RANS']:
            if config.parameters['RANS']['precondition'] == 'true':
                precondition = True
        sas = False
        if config.parameters['RANS']['turbulence']['model'] == 'sas':
            sas = True

        solver_name = "RANS Menter"
        solver_type = "MENTER"
        if sas:
            solver_name += " SAS"
            solver_type += "SAS"
        else:
            solver_name += " SST"
        if transition:
            solver_name += " Transition"
            solver_type += "TRANS"

        if precondition:
            solver_name += " (Low M Preconditioned)"
        solver_name += " Solver Initialise"

        config.logger.info(solver_name)

        self.parameter_update()
        self.solver = load_solver_runtime({"dg": False,
                                           "type": solver_type,
                                           "medium": "air",
                                           "device": config.options.device,
                                           "precond": precondition
                                           },
                                          config.parameters)

        num_mesh = config.parameters['time marching']['multigrid']
        self.solver.read_mesh(config.options.problem_name,
                              config.options.case_name, num_mesh)
        num_mesh = self.solver.init_storage()
        config.parameters['time marching']['multigrid'] = num_mesh

        config.cycle_info = self.solver.init_solution(config.options.case_name)

    def parameter_update(self):
        super(MenterSSTSolver, self).parameter_update()
        self.space_order = config.get_space_order('RANS')

    def march(self, rk_index, rk_coeff, cfl, cfl_transport, real_time_step,
              time_order, safe_mode, use_rusanov):
        config.logger.debug("Explicit March")
        valid = self.solver.march(rk_index, rk_coeff, cfl, cfl_transport,
                                  real_time_step,
                                  time_order, self.space_order, safe_mode, use_rusanov)
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

    def update_halos(self):
        self.solver.update_halos(True)

    def prolongate(self, prolongation_factor, prolongation_transport_factor):
        self.solver.prolongate(prolongation_factor,
                               prolongation_transport_factor)

    def set_mesh_level(self, mesh_level):
        self.solver.set_mesh_level(mesh_level)
