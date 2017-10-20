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
import sys
import os.path
import pkgutil
import json
import datetime
from colorama import Fore
from mpi4py import rc
import yaml
rc.initialize = False
if 'ZCFD_TRACE' in os.environ:
    rc.profile('vt-mpi', logfile='zcfd')

from mpi4py import MPI


from . import solvers
from .utils import (
    config,
    commandline,
    Parameters,
    Logger,
    md5sum
)


class zCFDSolver:
    """Worlds Fastest CFD Solver"""

    def main(self):
        MPI.Init_thread(MPI.THREAD_MULTIPLE)
        if MPI.Query_thread() != MPI.THREAD_MULTIPLE:
            print 'ERROR: make sure MPI is configured with thread support'
            self.terminate()

        self.read_commandline()
        self.init_logger()
        self.show_banner()
        self.list_solvers()
        self.init_defaults()
        if self.read_controlfile() and self.load_solver():
            self.initialise_solver()
            self.start_solver()
        # self.terminate()

    def __del__(self):
        self.terminate()

    def show_banner(self):
        # Show copyright banner
        # Show product banner (see http://patorjk.com/software/taag/)
        config.logger.info(Fore.BLUE + r"     _______________________/\\\\\\\\\___/\\\\\\\\\\\\\\\___/\\\\\\\\\\\\____" + "\n" +
                           r"      ____________________/\\\////////___\/\\\///////////___\/\\\////////\\\__" + "\n" +
                           r"       __________________/\\\/____________\/\\\______________\/\\\______\//\\\_" + "\n" +
                           r"        __/\\\\\\\\\\\___/\\\______________\/\\\\\\\\\\\______\/\\\_______\/\\\_" + "\n" +
                           r"         _\///////\\\/___\/\\\______________\/\\\///////_______\/\\\_______\/\\\_" + "\n" +
                           r"          ______/\\\/_____\//\\\_____________\/\\\______________\/\\\_______\/\\\_" + "\n" +
                           r"           ____/\\\/________\///\\\___________\/\\\______________\/\\\_______/\\\__" + "\n" +
                           r"            __/\\\\\\\\\\\_____\////\\\\\\\\\__\/\\\______________\/\\\\\\\\\\\\/___" + "\n" +
                           r"             _\///////////_________\/////////___\///_______________\////////////_____" + "\n\n" + Fore.RESET)
        config.logger.info(Fore.BLUE + r"            _____                  ______           __       ____                 __            __ " + "\n" +
                           r"  ____ _   /__  /  ___  ____  ____/_  __/___  _____/ /_     / __ \_________  ____/ /__  _______/ /_" + "\n" +
                           r" / __ `/     / /  / _ \/ __ \/ __ \/ /  / _ \/ ___/ __ \   / /_/ / ___/ __ \/ __  // / / / ___/ __/" + "\n" +
                           r"/ /_/ /     / /__/  __/ / / / /_/ / /  /  __/ /__/ / / /  / ____/ /  / /_/ / /_/ // /_/ / /__/ /_  " + "\n" +
                           r"\__,_/     /____/\___/_/ /_/\____/_/   \___/\___/_/ /_/  /_/   /_/   \____/\__,_/ \__,_/\___/\__/  " + Fore.RESET)

    def terminate(self):
        # time.sleep(1)
        # MPI.finalize()
        if config.zmq != 0:
            config.zmq.stop()
            config.zmq.ts.join()
        MPI.Finalize()

    def message_wait(self):
        if config.options.mq:
            # Wait for start command
            exit(-1)

    def init_compute_device(self):
        pass

    def init_logger(self):

        rank = MPI.COMM_WORLD.Get_rank()
        nparts = MPI.COMM_WORLD.Get_size()

        directory = str(config.options.case_name) + \
            "_P" + str(nparts) + "_OUTPUT"

        log_path = directory + '/LOGGING'

        config.output_dir = directory

        if rank == 0:
            self.ensure_dir(directory)
            self.ensure_dir(log_path)

            vis_path = directory + '/VISUALISATION'
            self.ensure_dir(vis_path)

            import libzCFDVersion as zversion

            # initialise status file
            with open(str(config.options.case_name) + '_status.txt', 'w') as f:
                json.dump({'num processor': nparts,
                           'case': config.options.case_name,
                           'problem': config.options.problem_name,
                           'version': zversion.get_project_version(),
                           'date': datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y"),
                           'case md5': md5sum(config.options.case_name + '.py'),
                           },
                          f, indent=4)

        MPI.COMM_WORLD.Barrier()

        config.logger = Logger.Logger(rank, filename=os.path.join(
            log_path, config.options.case_name + "." + str(rank) + ".log"), connector=config.zmq)

        # config.logger = libzCFDLogger.getLogger()
        # fh = libzCFDLogger.FileLogger(config.problem_name+"."+str(rank)+".log");
        # config.logger.addHandler(fh)

        # config.filelogger = fh
        # if rank == 0:
        #    ch = libzCFDLogger.StdOutLogger()
        #    config.logger.addHandler(ch)
        #    config.streamlogger = ch
        #
        # config.logger.debug('Initialised Logging')
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
        config.solver_names = [name for _, name,
                               _ in pkgutil.iter_modules([pkgpath])]
        config.logger.info("Solvers Available: " +
                           ", ".join(map(str, config.solver_names)))
        # print names

    def read_commandline(self):
        # config.logger.debug("Reading commandline")
        options = commandline.ZOption()
        config.options = options.parse()

        case_filename = None
        problem_filename = None

        # Remove .py extension from case name
        if config.options.case_name.endswith('.py') or config.options.case_name.endswith('.h5'):
            case_filename = config.options.case_name
            config.options.case_name = config.options.case_name[:-3]
        else:
            case_filename = config.options.case_name + '.py'

        if config.options.problem_name.endswith('.h5'):
            problem_filename = config.options.problem_name
            config.options.problem_name = config.options.problem_name[:-3]
        else:
            problem_filename = config.options.problem_name + '.h5'

        # Check if files exist
        ok = True
        if not os.path.isfile(case_filename):
            ok = False
            if MPI.COMM_WORLD.Get_rank() == 0:
                print(" Control file: %s not found" % (case_filename))
                Parameters.Parameters().write(case_filename)
        if not os.path.isfile(problem_filename):
            ok = False
            if MPI.COMM_WORLD.Get_rank() == 0:
                print(" Mesh file: %s not found" % (problem_filename))
        MPI.COMM_WORLD.Barrier()
        if not ok:
            self.terminate()

    def read_controlfile(self):
        config.logger.debug("Reading controlfile")
        cfilename = config.options.case_name
        if cfilename is None:
            cfilename = config.options.problem_name
        config.controlfile = os.path.abspath(cfilename) + ".py"
        if os.path.isfile(config.controlfile):
            config.logger.info("Control file: " + config.controlfile)
            p = Parameters.Parameters()
            p.read(cfilename)
            config.logger.info("Parameters: " + str(config.parameters))
            return True
        else:
            config.logger.info("Creating missing control file with defaults")
            Parameters.Parameters().write(config.controlfile)
            config.logger.error("Control file: " +
                                config.controlfile + " not found")
            return False

    def load_solver(self):
        config.logger.debug("Loading Solver")
        equations = config.parameters['equations']

        solver_name_map = {
            'euler': 'EulerSolver',
            'viscous': 'ViscousSolver',
            'RANS': 'TurbulentSolver',
            'LES': 'ViscousSolver',
            'DGeuler': 'DGExplicitSolver',
            'DGviscous': 'DGExplicitSolver',
            'DGLES': 'DGExplicitSolver',
            'DGRANS': 'DGExplicitSolver'
        }
        solver_name = solver_name_map.get(equations, None)

        if solver_name and config.solver_names.count(solver_name):
            indx = config.solver_names.index(solver_name)
            solver = 'zcfd.solvers.' + config.solver_names[indx]
            __import__(solver)
            config.solver = getattr(
                sys.modules[solver], config.solver_names[indx])(equations)
            return True
        else:
            config.logger.error("Failed to load solver")
            return False

    def initialise_solver(self):
        config.logger.debug("Initialising Solver")
        config.solver.initialise()

    def start_solver(self):
        config.logger.debug("Starting Solver")
        config.solver.solve()
        config.logger.debug("Terminating Solver")
        config.solver = 0

    def ensure_dir(self, d):
        if not os.path.exists(d):
            os.makedirs(d)


if __name__ == "__main__":
    zcfd = zCFDSolver()
    zcfd.main()
