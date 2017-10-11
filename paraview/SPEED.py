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
    * Neither the name of the <organization> nor the
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
# try: paraview.simple
# except:

from paraview.simple import *

paraview.simple._DisableFirstRenderCameraReset()

import math
import numpy as np
from scipy.optimize import curve_fit
from zutil import rotate_vector

alpha = 0.0
beta = 0.0
reference_area = 1.0
#bl_position = 0.97
#face_area = 0.075823


def calc_drag(file_root):

    wall = PVDReader(FileName=file_root + '_wall.pvd')

    CellDatatoPointData1 = CellDatatoPointData(Input=wall)
    CellDatatoPointData1.PassCellData = 1

    sum = MinMax(Input=CellDatatoPointData1)
    sum.Operation = "SUM"
    sum.UpdatePipeline()

    sum_client = servermanager.Fetch(sum)
    pforce = sum_client.GetCellData().GetArray("pressureforce").GetTuple(0)
    #fforce = sum_client.GetCellData().GetArray("frictionforce").GetTuple(0)
    #yplus = wall_slice_client.GetCellData().GetArray("yplus").GetValue(0)

    pforce = rotate_vector(pforce, alpha, beta)
    #fforce = rotate_vector(fforce,alpha,beta)

    return pforce


def drag_curve(x, a, b, c, d):
    return a * a * a * x + b * b * x + c * x + d


# Connect('localhost')
ReverseConnect('11111')

num_procs = '24'
pressure = 87510.53
gamma = 1.4

case = 'm0p5'
mach = 0.5
q = 1.0e6  # (0.5*gamma*pressure*mach*mach)
alpha = 0.0
beta = 0.0
force_m0p5 = calc_drag('C13_2013-04-04-half-' + case +
                       '_P' + num_procs + '_OUTPUT/C13_2013-04-04-half-' + case)
for i in range(0, 3):
    force_m0p5[i] /= q

case = 'm0p8'
mach = 0.8
q = 1.0e6  # (0.5*gamma*pressure*mach*mach)
alpha = 0.0
beta = 0.0
force_m0p8 = calc_drag('C13_2013-04-04-half-' + case +
                       '_P' + num_procs + '_OUTPUT/C13_2013-04-04-half-' + case)
for i in range(0, 3):
    force_m0p8[i] /= q

case = 'm1p1'
mach = 1.1
q = 1.0e6  # (0.5*gamma*pressure*mach*mach)
alpha = 0.0
beta = 0.0
force_m1p1 = calc_drag('C13_2013-04-04-half-' + case +
                       '_P' + num_procs + '_OUTPUT/C13_2013-04-04-half-' + case)
for i in range(0, 3):
    force_m1p1[i] /= q

case = 'm1p3'
mach = 1.3
q = 1.0e6  # (0.5*gamma*pressure*mach*mach)
alpha = 0.0
beta = 0.0
force_m1p3 = calc_drag('C13_2013-04-04-half-' + case +
                       '_P' + num_procs + '_OUTPUT/C13_2013-04-04-half-' + case)
for i in range(0, 3):
    force_m1p3[i] /= q

print force_m0p5
print force_m0p8
print force_m1p1
print force_m1p3

x = [0.0, 0.5, 0.8, 1.1, 1.3]
y = [0.0, force_m0p5[0], force_m0p8[0], force_m1p1[0], force_m1p3[0]]

from scipy.interpolate import interp1d
f2 = interp1d(x, y, kind='cubic')
xnew = np.linspace(0.5, 1.3, 10)


pl.plot(x, y, xnew, f2(xnew))


# Render()
