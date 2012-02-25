
from zcfd.utils.Logger import Logger


zmq = 0 # Message Q connector
logger = 0#= Logger(0)
filelogger = 0
streamlogger = 0
options = 0 # Output from argparser
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
    
    if isinstance(time_order,int):
        return time_order
    else:
        if time_order == 'first':
            return 1
        if time_order == 'second':
            return 2
        # Default to first order
        return 1
    

    