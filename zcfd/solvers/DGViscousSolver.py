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
    * Neither the name of the <organization> nor the
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

class DGViscousSolver(ExplicitSolver):

    """DG Viscous Solver"""
    def initialise(self):

        precond = config.parameters[self.equations]['precondition']
        if self.equations == 'DGviscous':
            config.logger.info("DG Viscous Solver Initialise")
            config.solver_native = 0
	    solver_type = "DGVISCOUS"
    
        if self.equations == 'DGLES':
            config.logger.info("DG LES Solver Initialise")
            config.solver_native = 0
	    solver_type = "DGLESWALE"

        if self.equations == 'DGMenterDES':
            config.logger.info("DG Menter SST DES Solver Initialise")
            config.solver_native = 0
	    solver_type = "DGMENTERDES"

        if self.equations == 'DGRANS':
            config.logger.info("DG RANS SST Solver Initialise")
            config.solver_native = 0
	    solver_type = "DGRANS"

        self.parameter_update()
        
        self.solver = load_solver_runtime({"dg": True,
					"space_order": self.space_order,
					"type": solver_type,
					"medium": "air",
					"device": config.options.device,
					"precond": precond 
					},
                                       config.parameters)

        if not config.parameters.has_key('Nodal Locations'):
            from zcfd.solvers.utils.DGNodalLocations import nodal_locations_default
            config.parameters.update(nodal_locations_default)
        
        num_mesh = config.parameters['time marching']['multigrid']
        self.solver.read_mesh(config.options.problem_name,config.options.case_name,num_mesh)
        num_mesh = self.solver.init_storage()
        config.parameters['time marching']['multigrid'] = num_mesh        
        config.cycle_info = self.solver.init_solution(config.options.case_name)
        self.polyMG = 'false'
        if self.lusgs == False:
            if 'multipoly' in config.parameters['time marching']:
                self.polyMG = config.parameters['time marching']['multipoly']
        
        if 'multipolycfl' in config.parameters['time marching']:
        	self.polyMGCFL = config.parameters['time marching']['multipolycfl']
    	else:
    		self.polyMGCFL = [self.cfl]
    		for index in range(0,self.space_order):
    			self.polyMGCFL.append(self.cfl)

        
    def parameter_update(self):
        super(DGViscousSolver,self).parameter_update()
        
        self.space_order = config.get_space_order(self.equations)
        
        if 'kind' in config.parameters['time marching']['scheme']:
            if config.parameters['time marching']['scheme']['kind'] == 'global timestepping':
                self.local_timestepping = False

        if 'multipoly' in config.parameters['time marching']:
            mp = config.parameters['time marching']['multipoly']
            if(mp == 'True' or mp == 'true' or mp == 't'):
                self.PMG = True

        self.finite_volume_solver = False
            
    def advance_solution(self,cfl,cfl_transport,cfl_coarse,real_time_step,time_order):
        """
        """
        if (self.polyMG == 'True' or self.polyMG == 'true' or self.polyMG == 't'):

            # Perform time step at highest order (1)
            self.copy_solution()        
            for rk_index in range(len(self.rk.coeff())):
                # Runge-Kutta loop
                valid = self.march(rk_index,self.rk.coeff()[rk_index],self.polyMGCFL[0],cfl_transport,cfl_coarse,real_time_step,time_order,self.safe_mode,0)
                if self.safe_mode and not valid:
                    raise InvalidSolution

            for polyLevel in range(0,self.space_order):
                    
                # Restrict solution and residual to poly level below
                # Compute force terms
                self.solver.restrictToPolynomialLevel(polyLevel,polyLevel+1,real_time_step,time_order,self.polyMGCFL[polyLevel])
            
                # March lower level (4)
                self.copy_solution()                    
                for rk_index in range(len(self.rk.coeff())):
                    # Runge-Kutta loop
                    valid = self.march(rk_index,self.rk.coeff()[rk_index],self.polyMGCFL[polyLevel+1],cfl_transport,cfl_coarse,real_time_step,time_order,self.safe_mode,polyLevel+1)
                    if self.safe_mode and not valid:
                        raise InvalidSolution

            for polyLevel in range(0,self.space_order):
                self.solver.addPolyCorrections(self.space_order-polyLevel,self.space_order-polyLevel-1)
        else:
            self.copy_solution()        
            for rk_index in range(len(self.rk.coeff())):
                # Runge-Kutta loop
                valid = self.march(rk_index,self.rk.coeff()[rk_index],cfl,cfl_transport,cfl_coarse,real_time_step,time_order,self.safe_mode,0)
                if self.safe_mode and not valid:
                    raise InvalidSolution           
            
        
    def march(self,rk_index,rk_coeff,cfl,cfl_transport,cfl_coarse,real_time_step,time_order,safe_mode,polyLevel):
        config.logger.debug("Explicit March")
        valid = self.solver.march(rk_index,rk_coeff,cfl,
                                  cfl_transport,
                                  cfl_coarse,real_time_step,time_order,self.space_order,polyLevel,safe_mode)
        return valid
    
    def copy_solution(self):
        config.logger.debug("Copy solution")
        self.solver.copy_solution();
        
    def copy_time_history(self):
        self.solver.copy_time_history()

    def sync(self):
        self.solver.sync()
        
    def output(self, case_dir, case_name, surface_variable_list, volume_variable_list, real_time_cycle, solve_cycle, real_time):
        self.solver.output(case_name, surface_variable_list, volume_variable_list,real_time_cycle,solve_cycle,real_time,False);
        
    def host_sync(self):
        self.solver.host_sync()
        
    def report(self):
        """
        """
        return self.solver.report();
        
    def calculate_rhs(self,real_time_step,time_order):
        self.solver.calculate_rhs(real_time_step,time_order,self.space_order)

    def add_stored_residual(self):
        self.solver.add_stored_residual()
    
    def store_residual(self):
        self.solver.store_residual()

    def add_const_time_derivative(self,real_time_step,time_order):
        self.solver.add_const_time_derivative(real_time_step,time_order)

    def restrict(self):
        self.solver.restrict()

    def update_halos(self):
        self.solver.update_halos()

    def prolongate(self,prolongation_factor,prolongation_transport_factor):
        self.solver.prolongate(prolongation_factor,prolongation_transport_factor)
 
    def set_mesh_level(self,mesh_level):
        self.solver.set_mesh_level(mesh_level)
