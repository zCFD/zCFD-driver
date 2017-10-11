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
from mpi4py import MPI
import argparse


class ZOption:

    def parse(self):
        # config.logger.debug('Start ZOption parse')
        if MPI.COMM_WORLD.Get_rank() > 0:
            usage = argparse.SUPPRESS
            parser = argparse.ArgumentParser(usage=usage, add_help=False)
        else:
            usage = "usage: %(prog)s [options] PROBLEM-NAME"
            parser = argparse.ArgumentParser(
                usage=usage, description="zCFD command line arguments", add_help=True)

        parser.add_argument('problem_name', nargs='?', default=None)

        parser.add_argument('--version', action='version', version='1.0')

        parser.add_argument("--mq", dest='mq', action='store_const',
                            const=True, default=False, help='Use message queue')

        parser.add_argument("-c", "--case-name", dest="case_name",
                            metavar="CASE-NAME", default=None, help="Case name")
        parser.add_argument("-d", "--device", dest="device",
                            metavar="DEVICE", default="cpu", help="Execution mode: cpu or gpu [default: %(default)s]")
        # parser.add_argument("-l","--loglevel", dest="loglevel",
        # metavar="LOGLEVEL", default="INFO", help=argparse.SUPPRESS)
        args = parser.parse_args()
        # print args.problem
        # print options.filename
        # check number of arguments, verify values, etc.:
        # if len(args.args) > 1 and MPI.COMM_WORLD.Get_rank() == 0:
        #    parser.error('unrecognised command-line arguments; '
        #             '"%s"' % (args.args[1],))
        # elif len(args.args):
        if not args.mq:
            if args.problem_name is None:
                parser.error('Problem name not defined')
            # if args.solver is None:
            #    parser.error('Please define solver type')
            if args.case_name is None:
                args.case_name = args.problem_name
        # exit(-1)
        # config.logger.debug('End ZOption parse')
        return args


if __name__ == "__main__":
    opt = ZOption()
    opt.parse()
