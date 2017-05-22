import numpy as np
import matplotlib
import os
import pandas as pd

#  This is required when running in script mode
batch = False
if 'BATCH_ANALYSIS' in os.environ:
    batch = True

from matplotlib.rcsetup import all_backends

if batch:
    if 'Agg' in all_backends:
        matplotlib.use('Agg')
    else:
        matplotlib.use('agg')
else:
    if 'nbagg' in all_backends:
        matplotlib.use('nbagg')
    else:
        matplotlib.use('nbAgg')

matplotlib.rcParams['backend_fallback'] = False

from matplotlib import pylab, mlab, pyplot
plt = pyplot
if batch:
    plt.ioff()
else:
    plt.ion()

from IPython.display import display
from IPython.core.pylabtools import figsize, getfigs

from paraview.simple import *
paraview.simple._DisableFirstRenderCameraReset()

import font as ft
import colour as cl

from plot_report import Report


