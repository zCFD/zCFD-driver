

from RungeKutta import FourStageRungeKutta
from RungeKutta import FiveStageRungeKutta
from RungeKutta import SingleStageRungeKutta
from RungeKutta import FiveStageRungeKuttaSSP
from RungeKutta import FourStageRungeKuttaSSP

def getRungeKutta(name):
    """
    RungeKutta factory
    """
    if name == '4' or name == 4:
        return FourStageRungeKutta()
    elif name == 'euler' or name == 1:
        return SingleStageRungeKutta()
    elif name == 'rk ssp':
        return FiveStageRungeKuttaSSP()
    elif name == 'rk ssp 4':
        return FourStageRungeKuttaSSP()
    else:
        return FiveStageRungeKutta()
    
    
