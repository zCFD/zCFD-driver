import numpy as np
import matplotlib
import os
import pandas as pd

#  This is required when running in script mode
batch = False
if 'BATCH_ANALYSIS' in os.environ:
    batch = True

if batch:
    matplotlib.use('Agg')
else:
    matplotlib.use('nbagg')

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

