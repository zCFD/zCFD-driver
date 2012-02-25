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
import os
import sys
import os.path, pkgutil
import time
import json
import datetime

#import logging
#import logging.config

from mpi4py import rc
rc.initialize = False
if 'ZCFD_TRACE' in os.environ:
    rc.profile('vt-mpi', logfile='zcfd')

from mpi4py import MPI
from colorama import Fore, Back, Style

#try:
#    import pycuda.autoinit
#except:
#    """"""

import yaml

from zcfd.utils import commandline, Parameters
from zcfd import solvers
from zcfd.utils import config
from zcfd.utils import Logger
from zcfd.utils import md5sum

#import libzCFDVersion
#import libzCFDIO
#import libzCFDLogger


class zCFDSolver:
    """Worlds Fastest CFD Solver"""
    def main(self):
        MPI.Init_thread(MPI.THREAD_SERIALIZED)
        if MPI.Query_thread() != MPI.THREAD_SERIALIZED:
            print 'ERROR: make sure MPI is configured with thread support'
            self.terminate()

        self.read_commandline()
        self.init_messageq()
        self.init_logger()
        self.show_banner()
        self.list_solvers()
        self.init_defaults()
        if self.read_controlfile():
            if self.load_solver():
                self.initialise_solver()
                self.start_solver()
        #self.terminate()

    def __del__(self):
        self.terminate()

    def show_banner(self):
        # Show copyright banner
        # Show product banner (see http://patorjk.com/software/taag/)
        config.logger.info(Fore.BLUE+r"     _______________________/\\\\\\\\\___/\\\\\\\\\\\\\\\___/\\\\\\\\\\\\____"+"\n"+
                           r"      ____________________/\\\////////___\/\\\///////////___\/\\\////////\\\__"+"\n"+
                           r"       __________________/\\\/____________\/\\\______________\/\\\______\//\\\_"+"\n"+
                           r"        __/\\\\\\\\\\\___/\\\______________\/\\\\\\\\\\\______\/\\\_______\/\\\_"+"\n"+
                           r"         _\///////\\\/___\/\\\______________\/\\\///////_______\/\\\_______\/\\\_"+"\n"+
                           r"          ______/\\\/_____\//\\\_____________\/\\\______________\/\\\_______\/\\\_"+"\n"+
                           r"           ____/\\\/________\///\\\___________\/\\\______________\/\\\_______/\\\__"+"\n"+
                           r"            __/\\\\\\\\\\\_____\////\\\\\\\\\__\/\\\______________\/\\\\\\\\\\\\/___"+"\n"+
                           r"             _\///////////_________\/////////___\///_______________\////////////_____"+"\n\n"+Fore.RESET)
        config.logger.info(Fore.BLUE+r"            _____                  ______           __       ____                 __            __ "+"\n"+
                           r"  ____ _   /__  /  ___  ____  ____/_  __/___  _____/ /_     / __ \_________  ____/ /__  _______/ /_"+"\n"+
                           r" / __ `/     / /  / _ \/ __ \/ __ \/ /  / _ \/ ___/ __ \   / /_/ / ___/ __ \/ __  // / / / ___/ __/"+"\n"+
                           r"/ /_/ /     / /__/  __/ / / / /_/ / /  /  __/ /__/ / / /  / ____/ /  / /_/ / /_/ // /_/ / /__/ /_  "+"\n"+
                           r"\__,_/     /____/\___/_/ /_/\____/_/   \___/\___/_/ /_/  /_/   /_/   \____/\__,_/ \__,_/\___/\__/  "+Fore.RESET)

    def init_messageq(self):
        # TODO For multinode parallel runs need to specify IP address of master here
        if config.options.mq:
            import zMQ
            from zMessage import Message
            print('Connecting to Message Q at',"localhost",4001)
            config.zmq = zMQ.Connector('localhost',4001)
            config.zmq.run() # non blocking
            found = False
            while not found:  # Wait until a configuration file has been sent
                item = config.zmq.q.get() # This blocks if the queue is empty
                if Message.is_config(item):
                    found = True
                    config.parameters = yaml.load(Message.get_config(item))
                    if 'problem_name' in config.parameters:
                        config.options.problem_name = config.parameters['problem_name']
                    if 'case_name' in config.parameters:
                        config.options.case_name = config.parameters['case_name']
                    if 'solver' in config.parameters:
                        config.options.solver = config.parameters['solver']
                    config.controlfile = os.path.abspath(config.options.case_name+".ctl.yaml")
                    Parameters.Parameters().write_yaml()
                config.zmq.q.task_done()

    #def start_message(self):

    def terminate(self):
        #time.sleep(1)
        #MPI.finalize()
        if config.zmq != 0:
            config.zmq.stop()
            config.zmq.ts.join()
        MPI.Finalize()


    def message_wait(self):
        if config.options.mq:
            # Wait for start command
            exit(-1)

    def init_compute_device(self):
        rank = MPI.COMM_WORLD.Get_rank()
        nparts = MPI.COMM_WORLD.Get_size()

    def init_logger(self):

        rank = MPI.COMM_WORLD.Get_rank()
        nparts = MPI.COMM_WORLD.Get_size()

        directory = str(config.options.case_name)+"_P"+str(nparts)+"_OUTPUT"

        config.output_dir = directory

        if rank == 0:
            self.ensure_dir(directory)
            
            import libzCFDVersion as zversion
            
            # initialise status file
            with open(str(config.options.case_name)+'_status.txt','w') as f:
                json.dump({'num processor' : nparts,
                           'case' : config.options.case_name,
                           'problem' : config.options.problem_name,
                           'version' : zversion.get_project_version(),
                           'date' :  datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y"),
                           'case md5' : md5sum(config.options.case_name + '.py'),
                           },
                          f,indent=4)

        MPI.COMM_WORLD.Barrier()

        config.logger = Logger.Logger(rank,filename=directory+"/"+config.options.case_name+"."+str(rank)+".log",connector=config.zmq)

        #config.logger = libzCFDLogger.getLogger()
        #fh = libzCFDLogger.FileLogger(config.problem_name+"."+str(rank)+".log");
        #config.logger.addHandler(fh)

        #config.filelogger = fh
        #if rank == 0:
        #    ch = libzCFDLogger.StdOutLogger()
        #    config.logger.addHandler(ch)
        #    config.streamlogger = ch
        #
        #config.logger.debug('Initialised Logging')
        """
        #logging.config.fileConfig('zcfd/logging.conf')
        logging.basicConfig(level=logging.NOTSET)
        # create logger
        config.logger = logging.getLogger("zCFD")
        config.logger.propagate = 0

        # Add FileHandler to logger
        fh = logging.FileHandler(config.problem_name+"."+str(rank)+".log","w")
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        numeric_level = getattr(logging, config.loglevel.upper(), None)
        #print config.loglevel.upper(), numeric_level
        fh.setLevel(numeric_level)
        config.logger.addHandler(fh)
        # Add console handler just for master rank
        if rank == 0:
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s')
            ch.setFormatter(formatter)
            ch.setLevel(logging.DEBUG)
            config.logger.addHandler(ch)
        # 'application' code
        config.logger.debug('Initialised Logging')
        """

    def init_defaults(self):
        Parameters.Parameters().create_defaults()

    def list_solvers(self):
        config.logger.debug("Listing available Solvers")
        pkgpath = os.path.dirname(solvers.__file__)
        config.solver_names =  [name for _, name, _ in pkgutil.iter_modules([pkgpath])]
        config.logger.info("Solvers Available: "+", ".join(map(str, config.solver_names)))
        #print names

    def read_commandline(self):
        #config.logger.debug("Reading commandline")
        options = commandline.ZOption()
        config.options = options.parse()
        # Remove .py extension from case name
        if config.options.case_name.endswith('.py') or config.options.case_name.endswith('.h5'):
            config.options.case_name = config.options.case_name[:-3]
        if config.options.problem_name.endswith('.h5'):
            config.options.problem_name = config.options.problem_name[:-3]


    def read_controlfile(self):
        config.logger.debug("Reading controlfile")
        cfilename = config.options.case_name;
        if cfilename == "NOT-DEFINED":
            cfilename = config.options.problem_name;
        #cfilename += ".ctl.yaml";
        config.controlfile = os.path.abspath(cfilename)+".py"
        if os.path.isfile(config.controlfile):
            config.logger.info("Control file: "+config.controlfile)
            p = Parameters.Parameters()
            p.read(cfilename)
            #p.read_yaml()
            #p.create_native()
            return True
        else:
            config.logger.info("Creating missing control file with defaults")
            #Parameters.Parameters().write_yaml()
            Parameters.Parameters().write(config.controlfile)
            config.logger.error("Control file: "+config.controlfile+" not found")
            return False


    def load_solver(self):
        config.logger.debug("Loading Solver")
        equations = config.parameters['equations']

        solver_name = 'NONE'

        if equations == 'euler':
            solver_name = 'EulerSolver'
        if equations == 'viscous':
            solver_name = 'ViscousSolver'
        if equations == 'RANS':
            solver_name = 'MenterSSTSolver'
        if equations == 'LES':
            solver_name = 'ViscousSolver'
        if equations == 'DGeuler':
            solver_name = 'DGEulerSolver'
        if equations == 'DGviscous':
            solver_name = 'DGViscousSolver'
        if equations == 'DGLES':
            solver_name = 'DGViscousSolver'
	if equations == 'DGMenterDES':
	    solver_name = 'DGViscousSolver'
	if equations == 'DGRANS':
	    solver_name = 'DGViscousSolver'

        if config.solver_names.count(solver_name):
            indx = config.solver_names.index(solver_name)
            #print indx
            solver = 'zcfd.solvers.'+config.solver_names[indx];
            #print solver
            __import__(solver)
            config.solver = getattr(sys.modules[solver],config.solver_names[indx])(equations)
            return True
        else:
            config.logger.error("Failed to load solver")
            return False

    def initialise_solver(self):
        config.logger.debug("Initialising Solver")
        comm = MPI.COMM_WORLD
        nparts = comm.Get_size()
        rank = comm.Get_rank()
        config.solver.initialise()
        #reader = libzCFDIO.FluentReader()
        #reader.set_filename("test")

    def start_solver(self):
        config.logger.debug("Starting Solver")
        config.solver.solve()
        config.logger.debug("Terminating Solver")
        config.solver = 0;

    def ensure_dir(self,d):
        #d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)

if __name__ == "__main__":
    zcfd = zCFDSolver()
    zcfd.main()

