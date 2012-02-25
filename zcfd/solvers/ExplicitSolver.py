"""
Copyright (c) 2012, Zenotech Ltd
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
import math
import time
from mpi4py import MPI
from colorama import Fore, Back, Style


from zcfd.utils import config, TimeSpent, Parameters

from zcfd.solvers import utils


class InvalidSolution(Exception):
    pass


class ExplicitSolver(object):
    
    
    def __init__(self,equations):
        self.rk = []
        self.cfl = 0.0
        self.cfl_transport = 0.0
        self.cfl_coarse = 0.0
        self.cfl_ramp = 1.0
        self.cfl_ini  = 0.0
        self.cfl_current = 0.0
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
        self.report_frequency = 0.0
        self.safe_mode = False
        self.cfl_ramp_func = None
        self.local_timestepping = True
        self.lusgs = False
        self.PMG = False
        self.minCFL = 1.0
        self.maxCFL = 10.0
        self.cflGrowth = 1.25
        self.lusgsRampOver = (self.maxCFL/(self.minCFL * math.log10(self.cflGrowth)))
        self.equations = equations
        self.finite_volume_solver = True
        self.include_backward_sweep = True
        self.num_sgs_sweeps = 7
        self.lusgs_epsilon = 1.0E-08
        self.lusgs_add_relaxation = True
        self.lusgs_jacobian_update_frequency = 1
        self.filter_freq = 1000000

    def parameter_update(self):
        self.cfl = config.parameters['time marching']['cfl']
        self.cfl_transport = self.cfl
        self.cfl_ini       = self.cfl
        
        if 'cfl transport' in config.parameters['time marching']:
            self.cfl_transport = config.parameters['time marching']['cfl transport']
        self.cfl_coarse = self.cfl
        if 'cfl coarse' in config.parameters['time marching']:
            self.cfl_coarse = config.parameters['time marching']['cfl coarse']
        if 'cfl ramp factor' in config.parameters['time marching']:
            self.cfl_ramp = config.parameters['time marching']['cfl ramp factor']['growth']
            self.cfl_ini = config.parameters['time marching']['cfl ramp factor']['initial']
        # Default to 5 stage RK
        self.rk_scheme_name = 'runge kutta'
        self.rk_scheme_data = '5'
        # Check for overrides 
        if 'scheme' in config.parameters['time marching'] and 'name' in config.parameters['time marching']['scheme']:
            if config.parameters['time marching']['scheme']['name'] == 'euler':
                self.rk_scheme_name = 'euler'
                self.rk_scheme_data = 'euler'
            else:
                if 'stage' in config.parameters['time marching']['scheme']:
                    self.rk_scheme_data = str(config.parameters['time marching']['scheme']['stage'])
                
        self.cycles = config.parameters['time marching']['cycles']
        self.num_mesh_levels = min(self.num_mesh_levels,config.parameters['time marching']['multigrid'])
        self.multigrid_cycles = self.cycles
        if 'multigrid cycles' in config.parameters['time marching']:
            self.multigrid_cycles = config.parameters['time marching']['multigrid cycles']
        if 'multigrid ramp' in config.parameters['time marching']:
            self.multigrid_ramp = config.parameters['time marching']['multigrid ramp']
        
        if 'scheme' in config.parameters['time marching'] and 'name' in config.parameters['time marching']['scheme']:
            if config.parameters['time marching']['scheme']['name'] == 'lu-sgs':
                self.lusgs = True
                self.rk_scheme_name = 'euler'
                self.rk_scheme_data = 'euler'
                self.num_mesh_levels = 1

        self.prolongation_factor = 0.75
        if 'prolong factor' in config.parameters['time marching']:
            self.prolongation_factor = config.parameters['time marching']['prolong factor']
        self.prolongation_transport_factor = 0.3
        if 'prolong transport factor' in config.parameters['time marching']:
            self.prolongation_transport_factor = config.parameters['time marching']['prolong transport factor']
        
        if 'unsteady' in config.parameters['time marching']:
            self.total_time     = config.parameters['time marching']['unsteady']['total time']
            self.real_time_step = config.parameters['time marching']['unsteady']['time step']
            if 'order' in config.parameters['time marching']['unsteady']:
                self.time_order = config.get_time_order(config.parameters['time marching']['unsteady']['order'])
            self.unsteady_start = config.parameters['time marching']['unsteady'].get('start',0)
        
        self.surface_variable_list = config.parameters['write output']['surface variables']
        self.volume_variable_list = config.parameters['write output']['volume variables']
        
        self.output_frequency = min(config.parameters['write output']['frequency'],max(self.cycles,1))
        self.report_frequency = min(config.parameters['report']['frequency'],max(self.cycles,1))
        
        if 'safe' in config.parameters:
            self.safe_mode = config.parameters['safe'] == 'true'
            
        if 'ramp func' in config.parameters['time marching']:
            self.cfl_ramp_func = config.parameters['time marching']['ramp func']

        if 'scheme' in config.parameters['time marching'] and 'name' in config.parameters['time marching']['scheme']:
                if config.parameters['time marching']['scheme']['name'] == 'lu-sgs':
                    if 'lu-sgs' in config.parameters['time marching']:
                        if 'Min CFL' in config.parameters['time marching']['lu-sgs']:
                            self.minCFL = config.parameters['time marching']['lu-sgs']['Min CFL']
                        if 'Max CFL' in config.parameters['time marching']['lu-sgs']:
                            self.maxCFL = config.parameters['time marching']['lu-sgs']['Max CFL']
                        if 'CFL growth' in config.parameters['time marching']['lu-sgs']:
                            self.cflGrowth = config.parameters['time marching']['lu-sgs']['CFL growth']
                        if 'Include Backward Sweep' in config.parameters['time marching']['lu-sgs']:
                            self.include_backward_sweep = config.parameters['time marching']['lu-sgs']['Include Backward Sweep']
                        if 'Number Of SGS Cycles' in config.parameters['time marching']['lu-sgs']:
                            self.num_sgs_sweeps = config.parameters['time marching']['lu-sgs']['Number Of SGS Cycles']
                        if 'Jacobian Epsilon' in config.parameters['time marching']['lu-sgs']:
                            self.lusgs_epsilon = config.parameters['time marching']['lu-sgs']['Jacobian Epsilon']
                        if 'Include Relaxation' in config.parameters['time marching']['lu-sgs']:
                            self.lusgs_add_relaxation = config.parameters['time marching']['lu-sgs']['Include Relaxation']
                        if 'Jacobian Update Frequency' in config.parameters['time marching']['lu-sgs']:
                            self.lusgs_jacobian_update_frequency = config.parameters['time marching']['lu-sgs']['Jacobian Update Frequency']

        if 'High Order Filter Frequency' in config.parameters['time marching']:
            self.filter_freq = config.parameters['time marching']['High Order Filter Frequency']
            

        self.lusgsRampOver = (self.maxCFL/(self.minCFL * math.log10(max(1.0001,self.cflGrowth))))
    
    def solve(self):
        """
        Explicit Solver loop
        """
        config.logger.debug("Solver solve")

        self.report_list = [[]];
        
        self.rk = utils.getRungeKutta(self.rk_scheme_data)

        # Update parameters from control dictionary
        self.parameter_update()
        
        self.report_thread = 0
        output_name = config.options.case_name
                
        restart_realtime_cycle = config.cycle_info[0]
        restart_solve_cycle    = config.cycle_info[1]
                
        total_cycles = restart_solve_cycle
        
        #if restart_realtime_cycle > 0:
        #    total_cycles = self.unsteady_start + restart_realtime_cycle*self.cycles + restart_solve_cycle

        # if restarting make sure the report file is appropriately truncated
        self.report_initialise(output_name,total_cycles,restart_realtime_cycle)
        self.multigrid_cycles = max(self.multigrid_cycles,self.unsteady_start)

        # Disable unsteady start if not on first real time step
        if restart_realtime_cycle > 0:
            self.unsteady_start = 0

        config.logger.info("Starting Cycle info "+str(restart_realtime_cycle)+ " "+str(restart_solve_cycle))

        # Check if we are restarting from a solution at the end of a real time step
        if restart_solve_cycle >= max(self.cycles,self.unsteady_start):
            restart_solve_cycle = 0
            restart_realtime_cycle = restart_realtime_cycle + 1
            config.logger.info(Fore.RED + "Starting real time cycle: %s" % (restart_realtime_cycle))
            self.copy_time_history()

        config.start_time = time.time()
        
        timeSpent = TimeSpent.TimeSpent()

        # Real time step loop
        self.real_time_cycle = restart_realtime_cycle
        self.num_real_time_cycle = int(self.total_time/self.real_time_step)
        # Check for steady run
        if self.total_time == self.real_time_step:
            self.num_real_time_cycle = 0
            self.unsteady_start = 0
        while self.real_time_cycle < self.num_real_time_cycle+1:
            #for self.real_time_cycle in range(config.cycle_info[0],int(self.total_time/self.real_time_step)):
            # Set volume for time step
                        
            # Pseudo time step
            self.solve_cycle = restart_solve_cycle+1
            while self.solve_cycle < max(self.cycles+1,self.unsteady_start+1):
                #for self.solve_cycle in range(config.cycle_info[1]+1,max(self.cycles+1,self.unsteady_start+1)):
                # TODO calculate cfl
                
                #self.num_mesh_levels = 

                if self.cfl_ramp_func:
                    new_cfl_tuple = self.cfl_ramp_func(self.solve_cycle,self.cfl,self.cfl_transport,self.cfl_coarse)
                    self.cfl = new_cfl_tuple[0]
                    self.cfl_transport = new_cfl_tuple[1]
                    self.cfl_coarse = new_cfl_tuple[2]

                if self.solve_cycle > self.multigrid_cycles:
                    self.num_mesh_levels = 1

                if self.lusgs:
                    if self.solve_cycle > self.lusgsRampOver:
                        thiscfl = self.maxCFL
                        #this.cfl = self.maxCFL
                    else:
                        thiscfl = min(self.minCFL*self.cflGrowth**(max(0,self.solve_cycle-1)),self.maxCFL)
                        #this.cfl = max(self.minCFL,min(self.cfl*self.cflGrowth,self.maxCFL))
                elif self.PMG:
                    thiscfl = self.polyMGCFL[0]
                else:
                    thiscfl = self.cfl
                
                config.logger.info(Fore.RED + "Cycle %s (real time cycle: %s time: %s)" % (self.solve_cycle,
                                                                                           self.real_time_cycle,
                                                                                           self.real_time_cycle*self.real_time_step) + Fore.RESET)
                if self.lusgs or self.PMG:
                    config.logger.info(Fore.GREEN + "CFL %s" % (thiscfl) + Fore.RESET)
                else:
                    config.logger.info(Fore.GREEN + "CFL %s (%s) - MG %s (coarse mesh: %s)" % (thiscfl,self.cfl_transport,self.cfl_coarse,
                                                                                               self.num_mesh_levels-1) + Fore.RESET)

                
                timeSpent.start("solving")
                
                #self.advance_solution(cfl,real_time_step,min(time_order,real_time_cycle))
                try:
                    if self.lusgs and self.finite_volume_solver:
                        self.advance_lusgs(thiscfl,thiscfl,self.real_time_step, 
                                           min(self.time_order,self.real_time_cycle),self.solve_cycle)
                    else:
                        self.advance_multigrid(thiscfl,self.cfl_transport,self.cfl_coarse,self.real_time_step,
                                               min(self.time_order,self.real_time_cycle),self.num_mesh_levels,
                                               self.prolongation_factor,self.prolongation_transport_factor)
                except InvalidSolution:
                    config.logger.info("Invalid solution detected: Writing out solution and terminating")
                    self.host_sync()
                    output_name = config.options.case_name
                    self.volume_variable_list.append('FailCell')
                    self.output(config.output_dir,output_name,self.surface_variable_list,
                                self.volume_variable_list,self.real_time_cycle,total_cycles,
                                self.local_timestepping and self.real_time_cycle*self.real_time_step or float(self.solve_cycle))
                    if isinstance(self.report_thread,threading.Thread):
                        self.report_thread.join()
                    self.sync()
                    config.logger.info("Terminating")
                    return

                timeSpent.stop("solving")

                config.logger.info(Fore.GREEN + "Timer: %s" % timeSpent.generateReport() + Fore.RESET)
                
                total_cycles+=1
                             
                # Sync to host for output and or reporting              
                if self.solve_cycle == 1 or self.solve_cycle >= max(self.cycles,self.unsteady_start) or ( self.solve_cycle%self.output_frequency == 0 or self.solve_cycle%self.report_frequency == 0):
                    self.host_sync()                    
                # Output 
                if self.solve_cycle%self.output_frequency == 0 or self.solve_cycle >= max(self.cycles,self.unsteady_start):
                    #if self.solve_cycle > output_frequency:
                    #    self.output_thread.join()
                    output_name = config.options.case_name 
                    #self.output_thread = threading.Thread(name='output', target=self.output,args=(output_name,surface_variable_list,volume_variable_list,real_time_cycle,))
                    #self.output_thread.start()
                    self.output(config.output_dir,output_name,self.surface_variable_list,
                                self.volume_variable_list,self.real_time_cycle,total_cycles,
                                self.local_timestepping and self.real_time_cycle*self.real_time_step or float(self.solve_cycle))

                # Reporting
                if ((self.real_time_cycle == 0) and (self.solve_cycle == 1)) or self.solve_cycle >= max(self.cycles,self.unsteady_start) or self.solve_cycle%self.report_frequency == 0:
                    if (self.solve_cycle > 1 or self.real_time_cycle > 0) and isinstance(self.report_thread,threading.Thread):
                        self.report_thread.join()
                    self.report_list.append(self.report())
                    output_name = config.options.case_name 
                    self.report_thread = threading.Thread(name='report', target=self.report_output,args=(output_name,total_cycles,self.real_time_cycle))
                    self.report_thread.start()

                    # If user has updated the control dictionary
                    if self.solve_cycle >= max(self.cycles,self.unsteady_start):
                        break

                    # Parse control dictionary if it has change
                    param = Parameters.Parameters()
                    if param.read_if_changed(config.options.case_name,config.controlfile):
                        config.logger.info(Fore.MAGENTA + 'Control dictionary changed - parsing' + Fore.RESET)
                        self.parameter_update()
                            
                    # Update source terms
                    self.solver.update_source_terms()        
                            
                # Increment
                self.solve_cycle += 1
                #self.host_sync()
            # Reset unsteady start
            self.unsteady_start = 0                     

            # Time history
            self.copy_time_history()
            # Volume history
            # If user has updated control dictionary
            if self.real_time_cycle >= int(self.total_time/self.real_time_step):
                break
            
            # Increment
            self.real_time_cycle += 1
            restart_solve_cycle = 0
        
        #self.output_thread.join()
        config.end_time = time.time()
        if isinstance(self.report_thread,threading.Thread):
            self.report_thread.join()
        self.sync()
        config.logger.info("Total Time: %s" % str(config.end_time-config.start_time))
        config.logger.info("Solver loop finished")
        
        config.logger.info("Timer Total: %s" % timeSpent.generateReportAndReset())
        
    def advance_solution(self,cfl,cfl_transport,cfl_coarse,real_time_step,time_order):
        """
        """
        self.copy_solution()
        
        for rk_index in range(len(self.rk.coeff())):
            # Runge-Kutta loop
            valid = self.march(rk_index,self.rk.coeff()[rk_index],
                               cfl,cfl_transport,cfl_coarse,
                               real_time_step,time_order,self.safe_mode, False)
            if self.safe_mode and not valid:
                raise InvalidSolution
             
    def set_mesh_level(self,mesh_level):
        raise NotImplementedError

    def advance_lusgs(self,cfl,cfl_transport,real_time_step,time_order,solve_cycle):
        mesh_number = 0
        calculate_viscous = True
        fd_jacobian = False
        use_rusanov = True
        
        
        updateJacobian = False
        if (solve_cycle-1)%self.lusgs_jacobian_update_frequency == 0:
            updateJacobian = True

        num_cell_colours = self.solver.get_number_cell_colours()

        self.copy_solution()

        if updateJacobian:
            config.logger.info("Updating Jacobian")
            self.solver.set_cell_colour(-1)
            self.update_halos()
            
            if not fd_jacobian:
                self.solver.update_jacobian_LUSGS(calculate_viscous,
                                  real_time_step,time_order,
                                  1, #self.space_order,
                                  cfl,cfl_transport,
                                  self.lusgs_epsilon,
                                  False, False,
                                  use_rusanov)
            else:
                for current_colour in range(0,num_cell_colours):
                    config.logger.debug("Updating jacobian matrix for colour %s" % current_colour)
                    self.solver.set_cell_colour(current_colour)
                    self.solver.update_jacobian_LUSGS(calculate_viscous,
                                                      real_time_step,time_order,
                                                      1, #self.space_order,
                                                      cfl,cfl_transport,
                                                      self.lusgs_epsilon,
                                                      False, True, use_rusanov)

        #self.set_mesh_level(mesh_number)
        #self.solver.set_cell_colour(-1)
        #self.solver.calculate_rhs(real_time_step,time_order,self.space_order)
        #calculate_viscous = False
        for sweep in range(0,self.num_sgs_sweeps):
            config.logger.info("Starting Sweep %s" % sweep)
            self.solver.set_cell_colour(-1)
            self.update_halos()
            # Forward sweep
            for current_colour in range(0,num_cell_colours):
                config.logger.debug("Marching colour %s" % current_colour)
                self.solver.set_cell_colour(current_colour)
                valid = self.solver.march_colour_set_LUSGS(calculate_viscous,
                                                   real_time_step,time_order,
                                                   self.space_order,
                                                   cfl,cfl_transport,
                                                   self.lusgs_add_relaxation,
                                                   self.safe_mode,
                                                   0,
                                                   False, #(current_colour == 0) and (sweep > 0)
                                                   )
                if self.safe_mode and not valid:
                    raise InvalidSolution


            if self.include_backward_sweep:
                self.solver.set_cell_colour(-1)
                self.update_halos()
                
                # Backward sweep
                for current_colour in reversed(range(0,num_cell_colours)):
                    config.logger.debug("Marching colour %s" % current_colour)
                    self.solver.set_cell_colour(current_colour)
                    valid = self.solver.march_colour_set_LUSGS(calculate_viscous,
                                                       real_time_step,time_order,
                                                       self.space_order,
                                                       cfl,cfl_transport,
                                                       self.lusgs_add_relaxation,
                                                       self.safe_mode,
                                                       1,
                                                       False,#(current_colour == num_cell_colours-1)
                                                       )
                    if self.safe_mode and not valid:
                        raise InvalidSolution

            self.host_sync()
            new_report = self.report()
            from mpi4py import MPI
            rank = MPI.COMM_WORLD.Get_rank()
            converged = 0
            if rank == 0:
                if sweep == 0:
                    first_report = new_report
                if sweep > 0:
                    # Compare reports
                    count = 0
                    nvar = 0
                    for i in range(0,min(7,len(new_report))):
                        v = new_report[i][0]
                        if v.startswith('rho'):
                            nvar += 1
                            v1 = new_report[i][1]                    
                            v2 = old_report[i][1]
                            v3 = first_report[i][1]
                            
                            if abs(v1 - v2)/(v3+1.0e-8) < 0.1 or v1 < 1.0e-8:
                                count += 1
                    if count == nvar:
                        converged = 1 

                old_report = new_report
                   
            converged = MPI.COMM_WORLD.bcast(converged, root=0)
            if converged == 1:
                break
             
        #if sweep == self.num_sgs_sweeps-1:
        #    self.cflGrowth = 0.95
        #else:
        #    self.cflGrowth = 1.05
            
        
            
    def advance_multigrid(self,cfl,cfl_transport,cfl_coarse,real_time_step,time_order,num_mesh_levels,
                          prolongation_factor,prolongation_transport_factor):
        """
        V-cycle multigrid with first solve on coarse mesh
        """
        for mesh_level in range(0,num_mesh_levels-1):
            
            config.logger.debug("Solving on mesh level: %s" % str(mesh_level+1))

            self.set_mesh_level(mesh_level)
            
            # calculate residual on fine mesh
            self.calculate_rhs(real_time_step,time_order)
            
            # add stored residual to computed residual
            if mesh_level != 0: # [CRrk + [RR - CR]
                self.add_stored_residual()
                        
            self.set_mesh_level(mesh_level+1)

            # restrict to coarse mesh
            self.restrict()
            
            # update halos on coarse mesh
            self.update_halos()
            
            # calculate residual on coarse mesh using restricted flow
            self.calculate_rhs(real_time_step,time_order)
            
            # Store restricted residual - computed residual from restricted flow [RR - CR]
            self.store_residual()
            
            # solve on coarse mesh
            self.advance_solution(cfl,cfl_transport,cfl_coarse,real_time_step,time_order)


        if num_mesh_levels == 1:
            self.advance_solution(cfl,cfl_transport,cfl_coarse,real_time_step,time_order)

            if self.finite_volume_solver != True and self.solve_cycle%self.filter_freq == 0:
                self.solver.filter_solution()
            
        for mesh_level in range(num_mesh_levels-1,0,-1):

            config.logger.debug("Prolonging on mesh level: from %s to %s" % (str(mesh_level),str(mesh_level-1)))

            self.set_mesh_level(mesh_level)

            # prolongate the solution from coarse to fine
            self.prolongate(prolongation_factor,prolongation_transport_factor)
            
            self.set_mesh_level(mesh_level-1)

            # update halos on fine mesh
            self.update_halos()
            
            # advance solution
            self.advance_solution(cfl,cfl_transport,cfl_coarse,real_time_step,time_order)
           
            
    def report_output(self,output_name, total_cycles, real_time_cycle):
        """
        """
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        nparts = comm.Get_size()
        if rank == 0:
            f = open(output_name+'_report.csv', 'a')
            if total_cycles == 1:
                f.write('RealTimeStep Cycle'+' '.join(' %s ' % x[0] for x in self.report_list[-1])+'\n')
            
            f.write(str(real_time_cycle)+' '+str(total_cycles)+' '.join(' %.8E ' % x[1] for x in self.report_list[-1])+'\n')
            f.close()
    
    def report_initialise(self,output_name, total_cycles, real_time_cycle):
        """
        """
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        nparts = comm.Get_size()
        if total_cycles > 0:
            if rank == 0:
                f = open(output_name+'_report.csv', 'r')
                lines = f.readlines()
                #f.write(str(self.solve_cycle)+' '.join(' %.8E ' % x for x in self.report_list[len(self.report_list)-1])+'\n')
                f.close()
                #cycles = config.parameters['time marching']['cycles']
                #report_frequency = min(config.parameters['report']['frequency'],cycles)
                f = open(output_name+'_report.csv', 'w')
                # Add one for first cycle
                for line in lines:
                    words = line.split()
                    if words[0] == 'RealTimeStep':
                        f.write(line)
                    elif int(words[1]) <= total_cycles:
                        f.write(line)
                    
                #for ln in range(self.solve_cycle/report_frequency+1):
                #    f.write(lines[ln])
                f.close()
        else:
            if rank == 0:
                try:
                    os.remove(output_name+'_report.csv')
                except:
                    pass
                    
    ## March solution in time
    def march(self,rk_index,rk_coeff,cfl,cfl_transport,cfl_coarse,real_time_step,time_order,safe_mode):
        raise NotImplementedError
    
    ## Sync data from device to host
    def sync(self):
        raise NotImplementedError        

    
    def report(self):
        """
        """
        raise NotImplementedError
    
    def output(self, case_dir, case_name, surface_variable_list, volume_variable_list, real_time_cycle, 
               solve_cycle, 
               real_time):
        """
        """
        raise NotImplementedError
    
    def host_sync(self):
        raise NotImplementedError
    
        
    def copy_solution(self):
        raise NotImplementedError
    
    def copy_time_history(self):
        raise NotImplementedError
        
    def calculate_rhs(self,real_time_step,time_order):
        raise NotImplementedError

    def add_stored_residual(self):
        raise NotImplementedError
    
    def store_residual(self):
        raise NotImplementedError

    def add_const_time_derivative(self,real_time_step,time_order):
        raise NotImplementedError

    def restrict(self):
        raise NotImplementedError

    def update_halos(self):
        raise NotImplementedError

    def prolongate(self,prolongation_factor,prolongation_transport_factor):
        raise NotImplementedError
