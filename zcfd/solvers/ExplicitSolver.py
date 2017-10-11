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
import os
import threading
import time
import pandas as pd
from mpi4py import MPI
from colorama import Fore
import numpy


from . import utils
from .cfl import CFL
from zcfd.utils import config, TimeSpent, Parameters


class InvalidSolution(Exception):
    pass


class ExplicitSolver(object):

    def __init__(self, equations):
        self.rk = []
        self.cfl = CFL(0.0)
        self.cfl_ramp_func = None
        self.cycles = 0
        self.num_mesh_levels = 1000
        self.multigrid_cycles = 0
        self.multigrid_ramp = 1.0
        self.prolongation_factor = 0.0
        self.prolongation_transport_factor = 0.0
        self.total_time = 0.0
        self.real_time_step = 0.0
        self.real_time_cycle = 0.0
        self.time_order = 0
        self.unsteady_start = 0.0
        self.surface_variable_list = 0.0
        self.volume_variable_list = 0.0
        self.output_frequency = 0.0
        self.unsteady_restart_output_frequency = 1
        self.report_frequency = 0.0
        self.safe_mode = False
        self.local_timestepping = True
        self.lusgs = False
        self.PMG = False
        self.equations = equations
        self.finite_volume_solver = True
        self.include_backward_sweep = True
        self.num_sgs_sweeps = 8
        self.lusgs_epsilon = 1.0E-08
        self.lusgs_add_relaxation = True
        self.lusgs_jacobian_update_frequency = 1
        self.filter_freq = 1000000
        self.lusgs_fd_jacobian = False
        self.lusgs_use_rusanov_jacobian = True
        self.start_output_real_time_cycle = 0
        self.output_real_time_cycle_freq = 1

    def parameter_update(self):
        self.cfl.max_cfl = config.parameters['time marching']['cfl']
        self.cfl.min_cfl = self.cfl.max_cfl
        self.cfl.transport_cfl = config.parameters[
            'time marching'].get('cfl transport', self.cfl.max_cfl)
        self.cfl.coarse_cfl = config.parameters[
            'time marching'].get('cfl coarse', self.cfl.max_cfl)
        if 'cfl ramp factor' in config.parameters['time marching']:
            self.cfl.cfl_ramp = config.parameters[
                'time marching']['cfl ramp factor'].get('growth', 1.0)
            self.cfl.min_cfl = config.parameters[
                'time marching']['cfl ramp factor']['initial']
        if 'ramp func' in config.parameters['time marching']:
            self.cfl_ramp_func = config.parameters[
                'time marching']['ramp func']

        # Default to 5 stage RK
        rk_scheme_data = '5'
        # Check for overrides
        if 'scheme' in config.parameters['time marching']:
            if 'name' in config.parameters['time marching']['scheme']:
                if config.parameters['time marching']['scheme']['name'] == 'euler':
                    rk_scheme_data = 'euler'
                else:
                    if 'stage' in config.parameters['time marching']['scheme']:
                        rk_scheme_data = str(
                            config.parameters['time marching']['scheme']['stage'])
                    elif 'class' in config.parameters['time marching']['scheme']:
                        rk_scheme_data = config.parameters[
                            'time marching']['scheme']['class']
                self.lusgs = config.parameters['time marching']['scheme']['name'] == 'lu-sgs'
            if 'kind' in config.parameters['time marching']['scheme']:
                if config.parameters['time marching']['scheme']['kind'] == 'global timestepping':
                    self.local_timestepping = False

        self.rk = utils.getRungeKutta(rk_scheme_data)

        self.cycles = config.parameters['time marching']['cycles']
        self.num_mesh_levels = min(self.num_mesh_levels, config.parameters[
                                   'time marching']['multigrid'])
        self.multigrid_cycles = self.cycles
        if 'multigrid cycles' in config.parameters['time marching']:
            self.multigrid_cycles = config.parameters[
                'time marching']['multigrid cycles']
        if 'multigrid ramp' in config.parameters['time marching']:
            self.multigrid_ramp = config.parameters[
                'time marching']['multigrid ramp']

        self.prolongation_factor = config.parameters[
            'time marching'].get('prolong factor', 0.75)
        self.prolongation_transport_factor = config.parameters[
            'time marching'].get('prolong transport factor', 0.3)

        if 'unsteady' in config.parameters['time marching']:
            self.total_time = config.parameters[
                'time marching']['unsteady']['total time']
            self.real_time_step = config.parameters[
                'time marching']['unsteady']['time step']
            if 'order' in config.parameters['time marching']['unsteady']:
                self.time_order = config.get_time_order(
                    config.parameters['time marching']['unsteady']['order'])
            self.unsteady_start = config.parameters[
                'time marching']['unsteady'].get('start', 0)

        self.surface_variable_list = config.parameters[
            'write output']['surface variables']
        self.volume_variable_list = config.parameters[
            'write output']['volume variables']

        self.output_frequency = min(config.parameters['write output'][
                                    'frequency'], max(self.cycles, 1))

        if 'unsteady restart file output frequency' in config.parameters['write output']:
            self.unsteady_restart_output_frequency = config.parameters['write output']['unsteady restart file output frequency']

        self.report_frequency = min(config.parameters['report'][
                                    'frequency'], max(self.cycles, 1))
        if 'start output real time cycle' in config.parameters['write output']:
            self.start_output_real_time_cycle = config.parameters[
                'write output']['start output real time cycle']

        if 'output real time cycle frequency' in config.parameters['write output']:
            self.output_real_time_cycle_freq = config.parameters[
                'write output']['output real time cycle frequency']

        if 'safe' in config.parameters:
            self.safe_mode = config.parameters['safe']

        if 'scheme' in config.parameters['time marching'] and 'name' in config.parameters['time marching']['scheme']:
            if config.parameters['time marching']['scheme']['name'] == 'lu-sgs':
                if 'lu-sgs' in config.parameters['time marching']:
                    if 'Include Backward Sweep' in config.parameters['time marching']['lu-sgs']:
                        self.include_backward_sweep = config.parameters[
                            'time marching']['lu-sgs']['Include Backward Sweep']
                    if 'Number Of SGS Cycles' in config.parameters['time marching']['lu-sgs']:
                        self.num_sgs_sweeps = config.parameters[
                            'time marching']['lu-sgs']['Number Of SGS Cycles']
                    if 'Jacobian Epsilon' in config.parameters['time marching']['lu-sgs']:
                        self.lusgs_epsilon = config.parameters[
                            'time marching']['lu-sgs']['Jacobian Epsilon']
                    if 'Include Relaxation' in config.parameters['time marching']['lu-sgs']:
                        self.lusgs_add_relaxation = config.parameters[
                            'time marching']['lu-sgs']['Include Relaxation']
                    if 'Jacobian Update Frequency' in config.parameters['time marching']['lu-sgs']:
                        self.lusgs_jacobian_update_frequency = config.parameters[
                            'time marching']['lu-sgs']['Jacobian Update Frequency']
                    if 'Finite Difference Jacobian' in config.parameters['time marching']['lu-sgs']:
                        self.lusgs_fd_jacobian = config.parameters['time marching'][
                            'lu-sgs']['Finite Difference Jacobian']
                    if 'Use Rusanov Flux For Jacobian' in config.parameters['time marching']['lu-sgs']:
                        self.lusgs_use_rusanov_jacobian = config.parameters['time marching'][
                            'lu-sgs']['Use Rusanov Flux For Jacobian']

        if 'High Order Filter Frequency' in config.parameters['time marching']:
            self.filter_freq = config.parameters[
                'time marching']['High Order Filter Frequency']

        # Ensure global timestepping state
        if not self.local_timestepping:
            self.num_real_time_cycle = 0
            self.unsteady_start = 0
            self.cycles = int(self.total_time / self.real_time_step)
            self.num_mesh_levels = 1

    def solve(self):
        """
        Explicit Solver loop
        """
        config.logger.debug("Solver solve")

        self.report_list = [[]]

        # Update parameters from control dictionary
        self.parameter_update()

        self.report_thread = 0
        output_name = config.options.case_name

        restart_realtime_cycle = config.cycle_info[0]
        restart_solve_cycle = config.cycle_info[1]

        total_cycles = restart_solve_cycle

        # if restart_realtime_cycle > 0:
        #    total_cycles = self.unsteady_start + restart_realtime_cycle*self.cycles + restart_solve_cycle

        # if restarting make sure the report file is appropriately truncated
        self.report_initialise(output_name, total_cycles,
                               restart_realtime_cycle)
        self.multigrid_cycles = max(self.multigrid_cycles, self.unsteady_start)

        # Disable unsteady start if not on first real time step
        if restart_realtime_cycle > 0:
            self.unsteady_start = 0

        config.logger.info("Starting Cycle info " +
                           str(restart_realtime_cycle) + " " + str(restart_solve_cycle))

        # Check if we are restarting from a solution at the end of a real time
        # step
        if restart_solve_cycle >= max(self.cycles, self.unsteady_start):
            restart_solve_cycle = 0
            restart_realtime_cycle = restart_realtime_cycle + 1
            config.logger.info(
                Fore.RED + "Starting real time cycle: %s" % (restart_realtime_cycle))
            self.copy_time_history()

        config.start_time = time.time()

        timeSpent = TimeSpent.TimeSpent()

        # Real time step loop
        self.real_time_cycle = restart_realtime_cycle
        self.num_real_time_cycle = int(self.total_time / self.real_time_step)
        # Check for steady run
        if self.total_time == self.real_time_step:
            self.num_real_time_cycle = 0
            self.unsteady_start = 0
        # Check for global timestep unsteady
        if not self.local_timestepping:
            self.num_real_time_cycle = 0
            self.unsteady_start = 0
            self.cycles = int(self.total_time / self.real_time_step)
            self.num_mesh_levels = 1

        while self.real_time_cycle < self.num_real_time_cycle + 1:
            # for self.real_time_cycle in xrange(config.cycle_info[0],int(self.total_time/self.real_time_step)):
            # Set volume for time step

            # Pseudo time step
            self.solve_cycle = restart_solve_cycle + 1
            while self.solve_cycle < max(self.cycles + 1, self.unsteady_start + 1):

                if self.solve_cycle > self.multigrid_cycles:
                    self.num_mesh_levels = 1

                if self.local_timestepping:
                    config.logger.info(Fore.RED + "Cycle %s (real time cycle: %s time: %s)" % (self.solve_cycle,
                                                                                               self.real_time_cycle,
                                                                                               self.real_time_cycle * self.real_time_step) + Fore.RESET)
                else:
                    config.logger.info(Fore.RED + "Cycle %s (time: %s)" % (self.solve_cycle,
                                                                           self.solve_cycle * self.real_time_step) + Fore.RESET)
                self.cfl.update(self.solve_cycle, self.real_time_cycle, self.cfl_ramp_func)
                config.logger.info(Fore.GREEN + "CFL %s (%s) - MG %s (coarse mesh: %s)" % (self.cfl.cfl, self.cfl.transport,
                                                                                   self.cfl.coarse,
                                                                                   self.num_mesh_levels - 1) + Fore.RESET)
                timeSpent.start("solving")

                try:
                    self.advance_multigrid(self.cfl, self.real_time_step,
                                           min(self.time_order,
                                               self.real_time_cycle), self.num_mesh_levels,
                                           self.prolongation_factor, self.prolongation_transport_factor)

                except InvalidSolution:
                    config.logger.info(
                        "Invalid solution detected: Writing out solution and terminating")
                    self.host_sync()
                    output_name = config.options.case_name + "_fail"
                    self.volume_variable_list.append('FailCell')
                    self.output(config.output_dir, output_name, self.surface_variable_list,
                                self.volume_variable_list, self.real_time_cycle, total_cycles,
                                self.local_timestepping and self.real_time_cycle * self.real_time_step or float(self.solve_cycle), False)
                    if isinstance(self.report_thread, threading.Thread):
                        self.report_thread.join()
                    self.sync()
                    config.logger.info("Terminating")
                    return

                timeSpent.stop("solving")

                total_cycles += 1

                timeSpent.start("update source terms")
                # Update source terms
                self.update_source_terms(self.solve_cycle, (self.solve_cycle >= max(self.cycles, self.unsteady_start)))
                timeSpent.stop("update source terms")

                timeSpent.start("output")
                # Sync to host for output and or reporting
                if self.solve_cycle == 1 or self.solve_cycle >= max(self.cycles, self.unsteady_start) or (self.solve_cycle % self.output_frequency == 0 or self.solve_cycle % self.report_frequency == 0):
                    self.host_sync()

                # Output restart results file
                if self.solve_cycle % self.output_frequency == 0 or self.solve_cycle >= max(self.cycles, self.unsteady_start):
                    if self.real_time_cycle % self.unsteady_restart_output_frequency == 0:
                        results_only = True
                        output_name = config.options.case_name
                        self.output(config.output_dir, output_name, self.surface_variable_list, self.volume_variable_list, self.real_time_cycle, total_cycles, self.local_timestepping and self.real_time_cycle * self.real_time_step or float(self.solve_cycle), results_only)
                    else:
                        config.logger.info(Fore.RED + "Restart file not written this real time step.  Reduce \'unsteady restart file output frequency\' if necessary. " + Fore.RESET)

                # Output
                if self.solve_cycle % self.output_frequency == 0 or self.solve_cycle >= max(self.cycles, self.unsteady_start):
                    # if self.solve_cycle > output_frequency:
                    #    self.output_thread.join()
                    output_name = config.options.case_name
                    # self.output_thread = threading.Thread(name='output', target=self.output,args=(output_name,surface_variable_list,volume_variable_list,real_time_cycle,))
                    # self.output_thread.start()

                    if self.real_time_cycle >= self.start_output_real_time_cycle and self.real_time_cycle % self.output_real_time_cycle_freq == 0:
                        results_only = False
                        self.output(config.output_dir, output_name, self.surface_variable_list, self.volume_variable_list, self.real_time_cycle, total_cycles, self.local_timestepping and self.real_time_cycle * self.real_time_step or float(self.solve_cycle), results_only)

                timeSpent.stop("output")

                # Reporting
                timeSpent.start("reporting")
                if ((self.real_time_cycle == 0) and (self.solve_cycle == 1)) or self.solve_cycle >= max(self.cycles, self.unsteady_start) or self.solve_cycle % self.report_frequency == 0 or self.solve_cycle == 1:
                    if (self.solve_cycle > 1 or self.real_time_cycle > 0) and isinstance(self.report_thread, threading.Thread):
                        self.report_thread.join()
                    self.report_list.append(self.report())
                    output_name = config.options.case_name
                    self.report_thread = threading.Thread(name='report', target=self.report_output, args=(
                        output_name, total_cycles, self.real_time_cycle))
                    self.report_thread.start()

                    # If user has updated the control dictionary
                    # if self.solve_cycle >= max(self.cycles, self.unsteady_start):
                    #    break

                    # Parse control dictionary if it has change
                    param = Parameters.Parameters()
                    if param.read_if_changed(config.options.case_name, config.controlfile):
                        config.logger.info(
                            Fore.MAGENTA + 'Control dictionary changed - parsing' + Fore.RESET)
                        self.parameter_update()
                timeSpent.stop("reporting")

                # Increment
                self.solve_cycle += 1

                config.logger.info(Fore.GREEN + "Timer: %s" %
                                   timeSpent.generateReport() + Fore.RESET)

                # self.host_sync()
            # Reset unsteady start
            self.unsteady_start = 0

            # Time history
            self.copy_time_history()
            # Volume history
            # If user has updated control dictionary
            if self.real_time_cycle >= int(self.total_time / self.real_time_step):
                break

            # Increment
            self.real_time_cycle += 1
            restart_solve_cycle = 0

        # self.output_thread.join()
        config.end_time = time.time()
        if isinstance(self.report_thread, threading.Thread):
            self.report_thread.join()
        self.sync()
        config.logger.info("Total Time: %s" % str(
            config.end_time - config.start_time))
        config.logger.info("Solver loop finished")

        config.logger.info("Timer Total: %s" %
                           timeSpent.generateReportAndReset())

    def advance_solution(self, cfl, real_time_step, time_order, mesh_level):
        """
        """

        if self.lusgs and self.finite_volume_solver:
            if mesh_level == 0:
                self.advance_lusgs(cfl.cfl, cfl.transport, real_time_step,
                                   time_order, self.solve_cycle, mesh_level)
            else:
                self.advance_lusgs(cfl.coarse, cfl.transport, real_time_step,
                                   time_order, self.solve_cycle, mesh_level)
        elif self.lusgs and mesh_level != 0:
            self.advance_rk(cfl.cfl, cfl.transport,
                            cfl.coarse, real_time_step, time_order)
        else:
            if mesh_level == 0:
                self.advance_rk(cfl.cfl, cfl.transport, real_time_step, time_order)
            else:
                self.advance_rk(cfl.coarse, min(
                    cfl.transport, cfl.coarse), real_time_step, time_order)

    def advance_rk(self, cfl, cfl_transport, real_time_step, time_order):
        """
        """
        self.copy_solution()

        for rk_index in xrange(len(self.rk.coeff())):
            # Runge-Kutta loop
            valid = self.march(rk_index, self.rk.coeff()[rk_index],
                               cfl, cfl_transport,
                               real_time_step, time_order, self.safe_mode, False)
            if self.safe_mode and not valid:
                raise InvalidSolution

    def set_mesh_level(self, mesh_level):
        raise NotImplementedError

    def advance_point_implicit(self, cfl, cfl_transport, real_time_step, time_order, solve_cycle):

        calculate_viscous = True
        fd_jacobian = self.lusgs_fd_jacobian
        use_rusanov = self.lusgs_use_rusanov_jacobian

        updateJacobian = False
        if (solve_cycle - 1) % self.lusgs_jacobian_update_frequency == 0:
            updateJacobian = True

        num_cell_colours = self.solver.get_number_cell_colours()

        self.copy_solution()

        if updateJacobian:
            config.logger.info("Updating Jacobian")
            self.solver.set_cell_colour(-1)

            if not fd_jacobian:
                self.solver.update_jacobian_LUSGS(True,
                                                  real_time_step, time_order,
                                                  1,  # self.space_order,
                                                  cfl, cfl_transport,
                                                  self.lusgs_epsilon,
                                                  False, False,
                                                  use_rusanov)
            else:
                for current_colour in xrange(num_cell_colours):
                    config.logger.debug(
                        "Updating jacobian matrix for colour %s" % current_colour)
                    self.solver.set_cell_colour(current_colour)
                    self.solver.update_jacobian_LUSGS(True,
                                                      real_time_step, time_order,
                                                      1,  # self.space_order,
                                                      cfl, cfl_transport,
                                                      self.lusgs_epsilon,
                                                      False, True, use_rusanov)
                self.solver.set_cell_colour(-1)

        self.solver.march_point_implicit(real_time_step,
                                         cfl, cfl_transport,
                                         self.safe_mode)
        self.update_halos()

    def advance_gmres(self, cfl, cfl_transport, real_time_step, time_order, solve_cycle):
        raise NotImplementedError

    def advance_lusgs(self, cfl, cfl_transport, real_time_step, time_order, solve_cycle, mesh_level=0):

        calculate_viscous = True
        fd_jacobian = self.lusgs_fd_jacobian
        use_rusanov = self.lusgs_use_rusanov_jacobian

        # Always calculate viscous fluxes if using fd jacobian
        if fd_jacobian:
            calculate_viscous = True

        updateJacobian = False
        if (solve_cycle - 1) % self.lusgs_jacobian_update_frequency == 0:
            updateJacobian = True

        num_cell_colours = self.solver.get_number_cell_colours()

        self.copy_solution()

        if updateJacobian:
            if mesh_level == 0:
                config.logger.info("Updating Jacobian")
            self.solver.set_cell_colour(-1)
            self.update_halos()

            if not fd_jacobian:
                self.solver.update_jacobian_LUSGS(True,
                                                  real_time_step, time_order,
                                                  1,  # self.space_order,
                                                  cfl, cfl_transport,
                                                  self.lusgs_epsilon,
                                                  False, False,
                                                  use_rusanov)
            else:
                for current_colour in xrange(num_cell_colours):
                    config.logger.debug(
                        "Updating jacobian matrix for colour %s" % current_colour)
                    self.solver.set_cell_colour(current_colour)
                    self.solver.update_jacobian_LUSGS(True,
                                                      real_time_step, time_order,
                                                      1,  # self.space_order,
                                                      cfl, cfl_transport,
                                                      self.lusgs_epsilon,
                                                      False, True, use_rusanov)

        # self.set_mesh_level(mesh_number)
        # self.solver.set_cell_colour(-1)
        # self.solver.calculate_rhs(real_time_step,time_order,self.space_order)
        # calculate_viscous = False

        converged = numpy.array(0, 'i')

        for sweep in xrange(self.num_sgs_sweeps):
            if mesh_level == 0:
                config.logger.info("Starting Sweep %s" % sweep)
            self.solver.set_cell_colour(-1)
            self.update_halos()
            # Forward sweep
            for current_colour in xrange(num_cell_colours):
                config.logger.debug("Marching colour %s" % current_colour)
                self.solver.set_cell_colour(current_colour)
                valid = self.solver.march_colour_set_LUSGS(calculate_viscous,
                                                           real_time_step, time_order,
                                                           self.space_order,
                                                           cfl, cfl_transport,
                                                           self.lusgs_add_relaxation,
                                                           self.safe_mode,
                                                           0,
                                                           # (current_colour == 0) and (sweep > 0)
                                                           False,
                                                           )
                if self.safe_mode and not valid:
                    raise InvalidSolution

            if self.include_backward_sweep:
                self.solver.set_cell_colour(-1)
                self.update_halos()

                # Backward sweep
                for current_colour in reversed(xrange(num_cell_colours)):
                    config.logger.debug("Marching colour %s" % current_colour)
                    self.solver.set_cell_colour(current_colour)
                    valid = self.solver.march_colour_set_LUSGS(calculate_viscous,
                                                               real_time_step, time_order,
                                                               self.space_order,
                                                               cfl, cfl_transport,
                                                               self.lusgs_add_relaxation,
                                                               self.safe_mode,
                                                               1,
                                                               # (current_colour == num_cell_colours-1)
                                                               False,
                                                               )
                    if self.safe_mode and not valid:
                        raise InvalidSolution

            self.solver.set_cell_colour(-1)

            if mesh_level == 0:
                self.host_sync()
                new_report = self.report(True)
                from mpi4py import MPI
                rank = MPI.COMM_WORLD.Get_rank()
                converged = numpy.array(0, 'i')
                if rank == 0:
                    if sweep == 0:
                        first_report = new_report
                    if sweep > 0:
                        # Compare reports
                        count = 0
                        nvar = 0
                        for i in xrange(min(7, len(new_report))):
                            v = new_report[i][0]
                            if v.startswith('rho'):
                                nvar += 1
                                v1 = new_report[i][1]
                                v2 = old_report[i][1]
                                v3 = first_report[i][1]

                                if abs(v1 - v2) / (v3 + 1.0e-8) < 0.1 or v1 < 1.0e-8:
                                    count += 1
                                #print v1, v2, v3, abs(v1 - v2) / (v3 + 1.0e-8)
                        if count == nvar:
                            converged = numpy.array(1, 'i')

                    old_report = new_report

                MPI.COMM_WORLD.Bcast([converged, MPI.INT], root=0)

                if numpy.asscalar(converged) == 1:
                    break

    def advance_multigrid(self, cfl, real_time_step, time_order, num_mesh_levels,
                          prolongation_factor, prolongation_transport_factor):
        """
        V-cycle multigrid with first solve on coarse mesh
        """
        for mesh_level in xrange(num_mesh_levels - 1):

            config.logger.debug("Solving on mesh level: %s" %
                                str(mesh_level + 1))

            self.set_mesh_level(mesh_level)

            # calculate residual on fine mesh
            self.calculate_rhs(real_time_step, time_order)

            # add stored residual to computed residual
            if mesh_level != 0:  # [CRrk + [RR - CR]
                self.add_stored_residual()

            self.set_mesh_level(mesh_level + 1)

            # restrict to coarse mesh
            self.restrict()

            # update halos on coarse mesh
            self.update_halos()

            # calculate residual on coarse mesh using restricted flow
            self.calculate_rhs(real_time_step, time_order)

            # Store restricted residual - computed residual from restricted
            # flow [RR - CR]
            self.store_residual()

            # solve on coarse mesh
            self.advance_solution(cfl,
                                  real_time_step, time_order,
                                  mesh_level + 1)

        if num_mesh_levels == 1:
            self.set_mesh_level(0)
            self.advance_solution(cfl,
                                  real_time_step, time_order, 0)

            if not self.finite_volume_solver and self.solve_cycle % self.filter_freq == 0:
                self.solver.filter_solution()

        for mesh_level in xrange(num_mesh_levels - 1, 0, -1):

            config.logger.debug("Prolonging on mesh level: from %s to %s" % (
                str(mesh_level), str(mesh_level - 1)))

            self.set_mesh_level(mesh_level)

            # prolongate the solution from coarse to fine
            self.prolongate(prolongation_factor, prolongation_transport_factor)

            self.set_mesh_level(mesh_level - 1)

            # update halos on fine mesh
            self.update_halos()

            # advance solution
            self.advance_solution(cfl,
                                  real_time_step, time_order,
                                  mesh_level - 1)

    def report_output(self, output_name, total_cycles, real_time_cycle):
        """
        """
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        if rank == 0:
            new_file = os.path.isfile(output_name + '_report.csv')
            f = open(output_name + '_report.csv', 'a')
            if not new_file:
                f.write('RealTimeStep Cycle' + ' '.join(' %s ' %
                                                        x[0] for x in self.report_list[-1]) + '\n')

            f.write(str(real_time_cycle) + ' ' + str(total_cycles) +
                    ' '.join(' %.8E ' % x[1] for x in self.report_list[-1]) + '\n')
            f.close()

    def report_initialise(self, output_name, total_cycles, real_time_cycle):
        """
        """
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        if total_cycles > 0:
            if rank == 0:
                #
                #  Read the current report file, up to total_cycles
                #  and write to a restart file, then remove the file
                #  to start a new clean file
                #
                restart_casename = output_name
                if 'restart casename' in config.parameters:
                    restart_casename = config.parameters['restart casename']
                    if os.path.isfile(restart_casename + '_report.restart.csv'):
                        from shutil import copyfile
                        copyfile(restart_casename + '_report.restart.csv',
                                 output_name + '_report.restart.csv')

                try:

                    if os.path.isfile(output_name + '_report.restart.csv'):

                        report_file = restart_casename + '_report.csv'
                        restart_report_file = output_name + '_report.restart.csv'

                        report_data = pd.read_csv(
                            report_file, sep=' ').dropna(axis=1)
                        # truncate
                        report_data = report_data.query(
                            'Cycle <= ' + str(total_cycles))
                        # read
                        restart_data = pd.read_csv(
                            restart_report_file, sep=' ').dropna(axis=1)
                        # truncate
                        restart_data = restart_data.query(
                            'Cycle <= ' + str(total_cycles))
                        # concat
                        # report_data = pd.concat([restart_data, report_data], ignore_index=True)
                        report_data = restart_data.append(
                            report_data, ignore_index=True)
                        # write
                        report_data.to_csv(
                            restart_report_file, sep=' ', index=False)

                        """
                        f_report = open(restart_casename + '_report.csv', 'r')
                        lines = f_report.readlines()
                        f_report.close()
                        f_restart = open(restart_casename + '_report.restart.csv', 'r')
                        restart_lines = f_restart.readlines()
                        f_restart.close()
                        old_length = len(restart_lines[0].split())
                        new_length = len(lines[0].split())
                        if new_length > old_length:
                            f = open(output_name + '_report.restart.csv', 'w')
                            f.write(lines[0])
                            for line in restart_lines:
                                words = line.split()
                                if words[0] != 'RealTimeStep':
                                    for i in range(old_length,new_length):
                                        words.append(0.0)
                                    f.write(" ".join(words))
                            for line in lines:
                                words = line.split()
                                if words[0] != 'RealTimeStep' and int(words[1]) <= total_cycles:
                                    f.write(line)
                            f.close()
                        elif new_length < old_length:
                            f = open(output_name + '_report.restart.csv', 'a')
                            for line in lines:
                                words = line.split()
                                if words[0] != 'RealTimeStep' and int(words[1]) <= total_cycles:
                                    for i in range(new_length,old_length):
                                        words.append(0.0)
                                    f.write(" ".join(words))
                            f.close()
                        else:
                            f = open(output_name + '_report.restart.csv', 'a')
                            for line in lines:
                                words = line.split()
                                if words[0] != 'RealTimeStep' and int(words[1]) <= total_cycles:
                                    f.write(line)
                            f.close()
                        """
                    else:
                        from shutil import copyfile
                        copyfile(restart_casename + '_report.csv',
                                 output_name + '_report.restart.csv')
                except:
                    pass
        else:
            if rank == 0:
                # delete .restart if not restarting
                try:
                    os.remove(output_name + '_report.restart.csv')
                except:
                    pass

        if rank == 0:
            try:
                os.remove(output_name + '_report.csv')
            except:
                pass

    # March solution in time
    def march(self, rk_index, rk_coeff, cfl, cfl_transport, real_time_step, time_order, safe_mode):
        raise NotImplementedError

    # Sync data from device to host
    def sync(self):
        raise NotImplementedError

    def report(self, residual_only=False):
        """
        """
        raise NotImplementedError

    def output(self, case_dir, case_name, surface_variable_list, volume_variable_list, real_time_cycle,
               solve_cycle,
               real_time, results_only):
        """
        """
        raise NotImplementedError

    def host_sync(self):
        raise NotImplementedError

    def copy_solution(self):
        raise NotImplementedError

    def copy_time_history(self):
        raise NotImplementedError

    def calculate_rhs(self, real_time_step, time_order):
        raise NotImplementedError

    def add_stored_residual(self):
        raise NotImplementedError

    def store_residual(self):
        raise NotImplementedError

    def add_const_time_derivative(self, real_time_step, time_order):
        raise NotImplementedError

    def restrict(self):
        raise NotImplementedError

    def update_halos(self):
        raise NotImplementedError

    def prolongate(self, prolongation_factor, prolongation_transport_factor):
        raise NotImplementedError

    def update_source_terms(self, cycle, force):
        # update source terms
        self.solver.update_source_terms(cycle, force)
