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
try:
    paraview.simple
except:
    from paraview.simple import *
paraview.simple._DisableFirstRenderCameraReset()

import math
from zutil import rotate_vector

alpha = 0.0
beta = 0.0
reference_area = 1.0
#bl_position = 0.97
#face_area = 0.075823


def get_chord(slice):

    Calculator1 = Calculator(Input=slice)

    Calculator1.AttributeMode = 'point_data'
    Calculator1.Function = 'coords.iHat'
    Calculator1.ResultArrayName = 'xpos'
    Calculator1.UpdatePipeline()

    xmin = MinMax(Input=Calculator1)
    xmin.Operation = "MIN"
    xmin.UpdatePipeline()

    xmin_client = servermanager.Fetch(xmin)

    min_pos = xmin_client.GetPointData().GetArray("xpos").GetValue(0)

    xmax = MinMax(Input=Calculator1)
    xmax.Operation = "MAX"
    xmax.UpdatePipeline()

    xmax_client = servermanager.Fetch(xmax)

    max_pos = xmax_client.GetPointData().GetArray("xpos").GetValue(0)

    Delete(xmin)
    Delete(xmax)
    Delete(Calculator1)

    return [min_pos, max_pos]


def plot_cp_profile(label, colour, file_root):

    wall = PVDReader(FileName=file_root + '_WALL.pvd')

    CellDatatoPointData1 = CellDatatoPointData(Input=wall)
    CellDatatoPointData1.PassCellData = 1

    wall_slice = Slice(Input=CellDatatoPointData1, SliceType="Plane")

    wall_slice.SliceType.Normal = [0.0, 1.0, 0.0]
    wall_slice.SliceType.Origin = [0.0, -0.5, 0.0]

    wall_slice.UpdatePipeline()

    offset = get_chord(wall_slice)

    Calculator1 = Calculator(Input=wall_slice)

    Calculator1.AttributeMode = 'point_data'
    Calculator1.Function = '(coords.iHat - ' + \
        str(offset[0]) + ')/' + str(offset[1] - offset[0])
    Calculator1.ResultArrayName = 'chord'

    sum = MinMax(Input=wall_slice)
    sum.UpdatePipeline()
    sum.Operation = "SUM"

    sum_client = servermanager.Fetch(sum)
    pforce = sum_client.GetCellData().GetArray("pressureforce").GetTuple(0)
    fforce = sum_client.GetCellData().GetArray("frictionforce").GetTuple(0)
    #yplus = wall_slice_client.GetCellData().GetArray("yplus").GetValue(0)

    pforce = rotate_vector(pforce, alpha, beta)
    fforce = rotate_vector(fforce, alpha, beta)

    PlotOnSortedLines1 = PlotOnSortedLines(Input=Calculator1)
    PlotOnSortedLines1.UpdatePipeline()

    SetActiveSource(PlotOnSortedLines1)

    DataRepresentation3 = Show()
    DataRepresentation3.XArrayName = 'chord'
    #DataRepresentation3.CompositeDataSetIndex = 3
    DataRepresentation3.UseIndexForXAxis = 0
    DataRepresentation3.SeriesLabel = ['cp', label + ' Re=6m fully turbulent']
    DataRepresentation3.SeriesColor = ['cp', colour[0], colour[1], colour[2]]
    DataRepresentation3.SeriesVisibility = ['chord', '0', 'cp', '0', 'V (0)', '0', 'V (1)', '0', 'V (2)', '0', 'V (Magnitude)', '0', 'p', '0', 'T', '0', 'rho', '0', 'mach', '0', 'pressureforce (0)', '0', 'pressureforce (1)', '0', 'pressureforce (2)', '0', 'pressureforce (Magnitude)', '0', 'pressuremoment (0)', '0', 'pressuremoment (1)', '0', 'pressuremoment (2)', '0', 'pressuremoment (Magnitude)', '0', 'frictionforce (0)',
                                            '0', 'frictionforce (1)', '0', 'frictionforce (2)', '0', 'frictionforce (Magnitude)', '0', 'frictionmoment (0)', '0', 'frictionmoment (1)', '0', 'frictionmoment (2)', '0', 'frictionmoment (Magnitude)', '0', 'eddy', '0', 'yplus', '0', 'var_6', '0', 'var_7', '0', 'arc_length', '0', 'Points (0)', '0', 'Points (1)', '0', 'Points (2)', '0', 'Points (Magnitude)', '0', 'vtkOriginalIndices', '0']
    DataRepresentation3.SeriesVisibility = ['cp', '1']

    #my_representation0 = GetDisplayProperties(PlotOnSortedLines1)
    #my_representation0.SeriesLabel = ['cp', label]
    #my_representation0.SeriesColor = ['cp', colour[0], colour[1], colour[2]]
    #my_representation0.SeriesVisibility = ['cp', '0', 'V (0)', '0', 'V (1)', '0', 'V (2)', '0', 'V (Magnitude)', '0', 'p', '0', 'T', '0', 'rho', '0', 'mach', '0', 'pressureforce (0)', '0', 'pressureforce (1)', '0', 'pressureforce (2)', '0', 'pressureforce (Magnitude)', '0', 'pressuremoment (0)', '0', 'pressuremoment (1)', '0', 'pressuremoment (2)', '0', 'pressuremoment (Magnitude)', '0', 'frictionforce (0)', '0', 'frictionforce (1)', '0', 'frictionforce (2)', '0', 'frictionforce (Magnitude)', '0', 'frictionmoment (0)', '0', 'frictionmoment (1)', '0', 'frictionmoment (2)', '0', 'frictionmoment (Magnitude)', '0', 'eddy', '0', 'yplus', '0', 'var_6', '0', 'var_7', '0', 'arc_length', '0', 'Points (0)', '0', 'Points (1)', '0', 'Points (2)', '0', 'Points (Magnitude)', '0', 'vtkOriginalIndices', '0']
    #i = 0
    # for s in my_representation0.GetProperty('SeriesVisibilityInfo'):
    #    if i%2 == 0:
    #        my_representation0.SeriesVisibility = [ s, '0' ]
    #        print s
    #    i+=1
    #my_representation0.SeriesVisibility = ['cp', '1']

    # my_representation0.UpdatePipeline()

    my_view0 = GetRenderView()
    my_view0.ChartTitle = 'NACA0012 alpha=' + \
        ('%.1f ' % alpha) + ('Cd=%.4f Cl=%.4f' %
                             (pforce[0] + fforce[0], pforce[2] + fforce[2]))
    my_view0.ChartTitleFont = ['Arial', '24', '1', '0']
    my_view0.AxisTitle = ['cp', 'x/c', '', '']
    my_view0.AxisBehavior = [0, 1, 0, 0]
    my_view0.AxisRange = [2.0, -6.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]


def plot_experiment(filename):
    experiment = CSVReader(FileName=[root_directory + '/NACA0012/' + filename])

    experiment.MergeConsecutiveDelimiters = 0
    experiment.FieldDelimiterCharacters = ' '
    experiment.HaveHeaders = 0

    SetActiveSource(experiment)

    DataRepresentation2 = Show()
    DataRepresentation2.XArrayName = 'Field 0'
    #DataRepresentation2.SeriesColor = ['Field 0', '0', '0', '0', 'Field 1', '0.894118', '0.101961', '0.109804', 'Field 2', '0.215686', '0.494118', '0.721569', 'Field 3', '0.301961', '0.686275', '0.290196', 'Field 4', '0.596078', '0.305882', '0.639216', 'vtkOriginalIndices', '1', '0.498039', '0']
    DataRepresentation2.UseIndexForXAxis = 0
    DataRepresentation2.AttributeType = 'Row Data'
    DataRepresentation2.SeriesVisibility = [
        'vtkOriginalIndices', '0', 'Field 0', '0', 'Field 1', '1']
    #my_representation0 = GetDisplayProperties(ExtractSelection1)
    DataRepresentation2.SeriesLabel = [
        'Field 1', 'Gregory Re=3m free transition']
    DataRepresentation2.SeriesColor = ['Field 1', '0.7', '0.7', '0.7']


root_directory = '/Users/jamil/Documents'
root_directory = '/home/jamil'
root_directory = '/home/bristol/eisbr011'

# Create a line chart and plot data
# plot_theory()
"""
XYChartView1 = CreateXYPlotView()
alpha = 0.0
beta  = 0.0
plot_cp_profile('cp',['0','0.5','1'],root_directory+'/NACA0012/n0012_113_a0p0_P1_OUTPUT/n0012_113_a0p0')
plot_experiment('CP_Gregory_expdata_a0p0.csv')

XYChartView1 = CreateXYPlotView()
beta  = 0.0
alpha = 10.0
plot_cp_profile('cp',['0','0.5','1'],root_directory+'/NACA0012/n0012_113_a10p0_P1_OUTPUT/n0012_113_a10p0')
plot_experiment('CP_Gregory_expdata_a10p0.csv')

XYChartView1 = CreateXYPlotView()
alpha = 15.0
beta  = 0.0
plot_cp_profile('cp',['0','0.5','1'],root_directory+'/NACA0012/n0012_113_a15p0_P1_OUTPUT/n0012_113_a15p0')
plot_experiment('CP_Gregory_expdata_a15p0.csv')

XYChartView1 = CreateXYPlotView()
alpha = 10.0
beta  = 0.0
plot_cp_profile('cp',['0','0.5','1'],root_directory+'/NACA0012/n0012_1793-513_a10p0_P1_OUTPUT/n0012_1793-513_a10p0')
plot_experiment('CP_Gregory_expdata_a10p0.csv')
"""
XYChartView1 = CreateXYPlotView()
alpha = 15.0
beta = 0.0
plot_cp_profile('cp', ['0', '0.5', '1'], root_directory +
                '/NACA0012/n0012_1793-513_a15p0_P6_OUTPUT/n0012_1793-513_a15p0')
plot_experiment('CP_Gregory_expdata_a15p0.csv')

Render()
