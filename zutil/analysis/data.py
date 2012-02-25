import os

remote_data = False
remote_server_auto = True

data_dir = None
ref_data_dir = None
data_host = None
paraview_cmd = None


def init(default_data_dir=None,
         default_data_host=None,
         default_paraview_cmd='mpiexec.hydra pvserver'):
    global data_dir, ref_data_dir, data_host, paraview_cmd


    if 'DATA_DIR' in os.environ:
        data_dir = os.environ['DATA_DIR']
    else:
        data_dir = default_data_dir
    
    if 'REF_DATA_DIR' in os.environ:
        ref_data_dir = os.environ['REF_DATA_DIR']
    else:
        ref_data_dir = data_dir
    
    if 'DATA_HOST' in os.environ:
        data_host = os.environ['DATA_HOST']
    else:
        data_host = default_data_host
    
    if 'PARAVIEW_CMD' in os.environ:
        paraview_cmd = os.environ['PARAVIEW_CMD']
    else:
        paraview_cmd = default_paraview_cmd
    
    if not remote_server_auto:
        paraview_cmd=None
    
    if not remote_data:
        data_host='localhost'
        paraview_cmd=None