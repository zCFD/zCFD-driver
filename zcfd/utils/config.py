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

from zcfd.utils.Logger import Logger


zmq = 0  # Message Q connector
logger = 0  # = Logger(0)
filelogger = 0
streamlogger = 0
options = 0  # Output from argparser
controlfile = 0
parameters = {}
solver = 0
solver_handle = 0
solver_names = 0
device = 0
output_dir = 0
cycle_info = 0
start_time = 0
end_time = 0


def get_space_order(equations):
    global parameters

    if equations.startswith('DG'):
        space_order = 0
        if parameters[equations]['order'] == 'zero' or parameters[equations]['order'] == 0:
            space_order = 0
        if parameters[equations]['order'] == 'first' or parameters[equations]['order'] == 1:
            space_order = 1
        if parameters[equations]['order'] == 'second' or parameters[equations]['order'] == 2:
            space_order = 2
        if parameters[equations]['order'] == 'third' or parameters[equations]['order'] == 3:
            space_order = 3
        if parameters[equations]['order'] == 'fourth' or parameters[equations]['order'] == 4:
            space_order = 4
        if parameters[equations]['order'] == 'fifth' or parameters[equations]['order'] == 5:
            space_order = 5
        if parameters[equations]['order'] == 'sixth' or parameters[equations]['order'] == 6:
            space_order = 6
        if parameters[equations]['order'] == 'seventh' or parameters[equations]['order'] == 7:
            space_order = 7
        if parameters[equations]['order'] == 'eighth' or parameters[equations]['order'] == 8:
            space_order = 8

    else:
        space_order = 2
        if parameters[equations]['order'] == 'first':
            space_order = 1
        if parameters[equations]['order'] == 'euler_second':
            space_order = 3

    return space_order


def get_time_order(time_order):

    if isinstance(time_order, int):
        return time_order
    else:
        if time_order == 'first':
            return 1
        if time_order == 'second':
            return 2
        # Default to first order
        return 1
