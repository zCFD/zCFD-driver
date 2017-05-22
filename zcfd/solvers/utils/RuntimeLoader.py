import importlib
from zcfd.utils import config


def load_solver_runtime(params, solver_params):
    required_params = ("device", "precond", "medium", "type", "dg")
    if not all(k in params for k in required_params):
        raise ValueError(
            "All required parameters not passed to load_solver_runtime")

    if params['dg']:
        module_name = "libzCFDDGSolver"
    else:
        module_name = "libzCFDSolver"
    module_name += params["type"]

    if ((type(params["precond"]) is str and params["precond"] == 'true') or
            (type(params["precond"]) is bool and params["precond"])):
        module_name += "PRECOND"

    if params["medium"] == "air":
        module_name += "AIR"
    elif params['medium'] == "water":
        module_name += "WATER"
    else:
        raise ValueError("Unknown medium: %s" % params['medium'])

    # For CUDA we have a separate library
    # The MIC Offload is compiled into the INTEL build
    module_name_stub = module_name
    if params['device'] == "gpu":
        module_name += '_CUDA'
    else:
        module_name += '_INTEL'

    config.logger.info(" Loading Library: " + module_name)
    try:
        solverlib = importlib.import_module(module_name)
    except Exception as e:
        config.logger.info(" Unable to load " + module_name)
        config.logger.info(" Error: " + str(e))
        # Failed to find library - try intel
        if params['device'] == "gpu":
            module_name = module_name_stub
            module_name += '_INTEL'
            config.logger.info(" Loading Library: " + module_name)
            solverlib = importlib.import_module(module_name)
        else:
            raise e

    set_parameters = getattr(solverlib, "set_parameters")
    set_parameters(solver_params)

    if params['dg']:
        solver_type = "DGExplicitSolver"
        DGExplicitSolver = getattr(solverlib, solver_type)

        return DGExplicitSolver(params['space_order'], (params["device"] == "cpu"))
    else:
        solver_type = "ExplicitSolver"
        ExplicitSolver = getattr(solverlib, solver_type)

        return ExplicitSolver((params["device"] == "cpu"))
