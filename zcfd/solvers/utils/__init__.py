

from RungeKutta import FourStageRungeKutta
from RungeKutta import FiveStageRungeKutta
from RungeKutta import SingleStageRungeKutta
from RungeKutta import ThreeStageThirdOrderTVDRungeKutta


def getRungeKutta(name):
    """
    RungeKutta factory
    """
    if name == '4' or name == 4:
        return FourStageRungeKutta()
    elif name == '5' or name == 5:
        return FiveStageRungeKutta()
    elif name == 'euler' or name == 1:
        return SingleStageRungeKutta()
    elif name == 'rk third order tvd':
        return ThreeStageThirdOrderTVDRungeKutta()
    else:
        return name
