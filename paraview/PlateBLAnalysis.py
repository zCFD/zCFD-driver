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

STANDARD_CHART_COLORS = [
    [0.933, 0.000, 0.000],     # Red
    [0.000, 0.804, 0.804],    # Cyan
    [0.000, 1.000, 0.000],    # Green
    [0.647, 0.165, 0.165],    # Brown
    [0.804, 0.569, 0.620],    # Pink
    [0.576, 0.439, 0.859],    # Purple
    [0.804, 0.522, 0.000],    # Orange
]

reference_area = 2.0
bl_position = 0.97
face_area = 0.075823


def plot_profile(label, colour, file_root):
    wall = PVDReader(FileName=file_root + '_wall.pvd')

    wall_slice = Slice(Input=wall, SliceType="Plane")

    wall_slice.SliceType.Normal = [1.0, 0.0, 0.0]
    wall_slice.SliceType.Origin = [bl_position, 0.0, 0.0]

    wall_slice.UpdatePipeline()

    wall_slice_client = servermanager.Fetch(wall_slice)
    nu = wall_slice_client.GetCellData().GetArray("nu").GetValue(0)
    #nu = 1.4e-5
    utau = wall_slice_client.GetCellData().GetArray("ut").GetValue(0)
    yplus = wall_slice_client.GetCellData().GetArray("yplus").GetValue(0)
    roughness = wall_slice_client.GetCellData().GetArray("roughness").GetValue(0)
    kplus = roughness * utau / nu

    t = wall_slice_client.GetCellData().GetArray("T").GetValue(0)
    p = wall_slice_client.GetCellData().GetArray("p").GetValue(0)
    rho = wall_slice_client.GetCellData().GetArray("rho").GetValue(0)

    wall_vel = wall_slice_client.GetCellData().GetArray("V").GetValue(0)

    symmetry = PVDReader(FileName=file_root + '_symmetry.pvd')

    CellDatatoPointData1 = CellDatatoPointData(Input=symmetry)
    CellDatatoPointData1.PassCellData = 1

    # Removes second symmetry plane keeping y max
    Clip1 = Clip(Input=CellDatatoPointData1, ClipType="Plane")
    Clip1.ClipType.Normal = [0.0, 1.0, 0.0]
    Clip1.ClipType.Origin = [0.0, -0.5, 0.0]

    Clip2 = Clip(Input=Clip1, ClipType="Plane")
    Clip2.ClipType.Normal = [0.0, 0.0, 1.0]
    Clip2.ClipType.Origin = [0.0, 0.0, 0.05]
    Clip2.InsideOut = 1

    Slice1 = Slice(Input=Clip2, SliceType="Plane")

    Slice1.SliceType.Normal = [1.0, 0.0, 0.0]
    Slice1.SliceType.Origin = [bl_position, 0.0, 0.0]

    Calculator1 = Calculator(Input=Slice1)

    #Calculator1.AttributeMode = 'point_data'
    Calculator1.AttributeMode = 'Point Data'
    Calculator1.Function = 'log10(coords.kHat * ' + \
        str(utau) + '/' + str(nu) + ')'
    Calculator1.ResultArrayName = 'yp'

    Calculator2 = Calculator(Input=Calculator1)

    #Calculator2.AttributeMode = 'point_data'
    Calculator2.AttributeMode = 'Point Data'
    Calculator2.Function = '(V.iHat - ' + str(wall_vel) + ')/ ' + str(utau)
    Calculator2.ResultArrayName = 'up'

    Calculator2.UpdatePipeline()

    PlotOnSortedLines1 = PlotOnSortedLines(Input=Calculator2)

    ExtractSelection1 = ExtractSelection(Input=PlotOnSortedLines1)

    selection_id = []

    for i in range(1, PlotOnSortedLines1.PointData.GetArray(0).GetNumberOfTuples()):
        selection_id.append(3)
        selection_id.append(-1)
        selection_id.append(i)

    selection_source_2386 = CompositeDataIDSelectionSource(
        ContainingCells=0, InsideOut=0, FieldType='POINT', IDs=selection_id)

    ExtractSelection1.Selection = selection_source_2386

    DataRepresentation3 = Show()
    DataRepresentation3.XArrayName = 'yp'
    DataRepresentation3.CompositeDataSetIndex = 3
    DataRepresentation3.UseIndexForXAxis = 0

    chart_variable_name = 'up'

    my_representation0 = GetDisplayProperties(ExtractSelection1)
    my_representation0.SeriesLabel = [chart_variable_name, 'y+=' + ('%.2f') % (
        yplus) + ' ' + 'k+=' + ('%.2f') % (kplus) + ' ' + 'ut=' + ('%.2f') % (utau) + ' ' + label]
    my_representation0.SeriesColor = [chart_variable_name, str(
        colour[0]), str(colour[1]), str(colour[2])]
#    my_representation0.SeriesVisibility = ['V (0)', '0', 'V (1)', '0', 'V (2)', '0', 'V (Magnitude)', '0', 'p', '0', 'T', '0', 'rho', '0', 'mach', '0', 'eddy', '0', 'yplus', '0', 'ut', '0', 'nu', '0', 'pressureforce (0)', '0', 'pressureforce (1)', '0', 'pressureforce (2)', '0', 'pressureforce (Magnitude)', '0', 'frictionforce (0)', '0', 'frictionforce (1)', '0', 'frictionforce (2)', '0', 'frictionforce (Magnitude)', '0', 'yp', '0', 'up', '1', 'arc_length', '0', 'Points (0)', '0', 'Points (1)', '0', 'Points (2)', '0', 'Points (Magnitude)', '0', 'vtkOriginalIndices', '0','vtkOriginalPointIds','0']

    my_representation0.UpdatePipeline()
    visibility = []
    for name in my_representation0.GetProperty("SeriesNamesInfo"):
        visibility.append(name)
        if name == chart_variable_name:
            visibility.append("1")
        else:
            visibility.append("0")

    print my_representation0.GetProperty("SeriesNamesInfo")
    #i = 0
    # for s in my_representation0.GetProperty('SeriesVisibilityInfo'):
    #    if i%2 == 0:
    #        my_representation0.SeriesVisibility = [ s, '0' ]
    #        print s
    #    i+=1

    #my_representation0.SeriesVisibility = ['up', '1']
    my_representation0.SeriesVisibility = visibility

    #my_representation0.SeriesPlotCorner = ['yp', '1']

    my_representation0.UpdatePipeline()

    my_view0 = GetRenderView()
    my_view0.ChartTitle = 'Zero Pressure Gradient Flat Plate'
    my_view0.ChartTitleFont = ['Arial', '24', '1', '0']
    my_view0.AxisTitle = ['u+', 'log(y+)', 'nut+', '']
    #my_view0.AxisBehavior = [1, 1, 0, 0]
    #my_view0.AxisRange = [0.0, 40.0, 0.0, 5.0, 0.0, 1.0, 0.0, 1.0]
    my_view0.LeftAxisRange = [0.0, 40.0]
    my_view0.BottomAxisRange = [0.0, 5.0]
    my_view0.RightAxisRange = [0.0, 600.0]


def plot_velocity_profile(label, colour, file_root):
    wall = PVDReader(FileName=file_root + '_wall.pvd')

    drag = MinMax(Input=wall)
    drag.Operation = "SUM"

    drag.UpdatePipeline()

    drag_client = servermanager.Fetch(drag)
    cd = drag_client.GetCellData().GetArray("frictionforce").GetValue(0)

    wall_slice = Slice(Input=wall, SliceType="Plane")

    wall_slice.SliceType.Normal = [1.0, 0.0, 0.0]
    wall_slice.SliceType.Origin = [bl_position, 0.0, 0.0]

    wall_slice.UpdatePipeline()

    wall_slice_client = servermanager.Fetch(wall_slice)
    nu = wall_slice_client.GetCellData().GetArray("nu").GetValue(0)
    utau = wall_slice_client.GetCellData().GetArray("ut").GetValue(0)
    yplus = wall_slice_client.GetCellData().GetArray("yplus").GetValue(0)
    cf = wall_slice_client.GetCellData().GetArray("frictionforce").GetValue(0)
    wall_vel = wall_slice_client.GetCellData().GetArray("V").GetValue(0)

    wall_vel = 0.0

    symmetry = PVDReader(FileName=file_root + '_symmetry.pvd')

    CellDatatoPointData1 = CellDatatoPointData(Input=symmetry)
    CellDatatoPointData1.PassCellData = 1

    # Removes second symmetry plane keeping y max
    Clip1 = Clip(Input=CellDatatoPointData1, ClipType="Plane")
    Clip1.ClipType.Normal = [0.0, 1.0, 0.0]
    Clip1.ClipType.Origin = [0.0, -0.5, 0.0]

    Clip2 = Clip(Input=Clip1, ClipType="Plane")
    Clip2.ClipType.Normal = [0.0, 0.0, 1.0]
    Clip2.ClipType.Origin = [0.0, 0.0, 0.05]
    Clip2.InsideOut = 1

    Slice1 = Slice(Input=Clip2, SliceType="Plane")

    Slice1.SliceType.Normal = [1.0, 0.0, 0.0]
    Slice1.SliceType.Origin = [bl_position, 0.0, 0.0]

    Calculator2 = Calculator(Input=Slice1)

    Calculator2.AttributeMode = 'Point Data'
    Calculator2.Function = '(V.iHat - ' + str(wall_vel) + ')'
    Calculator2.ResultArrayName = 'vprof'

    Calculator2.UpdatePipeline()

    PlotOnSortedLines1 = PlotOnSortedLines(Input=Calculator2)

    DataRepresentation3 = Show()
    DataRepresentation3.XArrayName = 'vprof'
    DataRepresentation3.CompositeDataSetIndex = 3
    DataRepresentation3.UseIndexForXAxis = 0

    chart_variable_name = 'Points (2)'

    my_representation0 = GetDisplayProperties(PlotOnSortedLines1)
    my_representation0.SeriesLabel = [chart_variable_name, 'y+=' + ('%.2f') % (yplus) + (
        ' cd=%.6f' % (cd / reference_area)) + (' cf=%.5f' % (cf / face_area)) + ' ' + label]
    my_representation0.SeriesColor = [chart_variable_name, str(
        colour[0]), str(colour[1]), str(colour[2])]

    my_representation0.UpdatePipeline()
    visibility = []
    for name in my_representation0.GetProperty("SeriesNamesInfo"):
        visibility.append(name)
        if name == chart_variable_name:
            visibility.append("1")
        else:
            visibility.append("0")
    my_representation0.SeriesVisibility = visibility
    my_representation0.UpdatePipeline()

    my_view0 = GetRenderView()
    my_view0.ChartTitle = 'Zero Pressure Gradient Flat Plate'
    my_view0.ChartTitleFont = ['Arial', '24', '1', '0']
    my_view0.AxisTitle = ['distance', 'speed', '', '']
    #my_view0.AxisBehavior = [1, 0, 0, 0]
    my_view0.LeftAxisRange = [0.0, 0.05]
    my_view0.BottomAxisRange = [0.0, 70.0]


def plot_theory():
    uytheory_csv = CSVReader(FileName=[root_directory + '/u+y+theory.csv'])

    uytheory_csv.MergeConsecutiveDelimiters = 1
    uytheory_csv.FieldDelimiterCharacters = ' '
    uytheory_csv.HaveHeaders = 0

    PlotData1 = PlotData(Input=uytheory_csv)

    SetActiveSource(PlotData1)
    DataRepresentation2 = Show()
    DataRepresentation2.XArrayName = 'Field 1'
    DataRepresentation2.SeriesColor = ['Field 0', '0', '0', '0', 'Field 1', '0.894118', '0.101961', '0.109804', 'Field 2', '0.215686', '0.494118',
                                       '0.721569', 'Field 3', '0.301961', '0.686275', '0.290196', 'Field 4', '0.596078', '0.305882', '0.639216', 'vtkOriginalIndices', '1', '0.498039', '0']
    DataRepresentation2.UseIndexForXAxis = 0
    DataRepresentation2.AttributeType = 'Row Data'
    DataRepresentation2.SeriesVisibility = [
        'vtkOriginalIndices', '0', 'Field 0', '1', 'Field 1', '0', 'Field 2', '0', 'Field 3', '0', 'Field 4', '0']
    #my_representation0 = GetDisplayProperties(ExtractSelection1)
    DataRepresentation2.SeriesLabel = ['Field 0', 'u+=y+']
    DataRepresentation2.SeriesColor = ['Field 0', '0.7', '0.7', '0.7']

    PlotData2 = PlotData(Input=uytheory_csv)

    SetActiveSource(PlotData2)
    DataRepresentation2 = Show()
    DataRepresentation2.XArrayName = 'Field 2'
    DataRepresentation2.SeriesColor = ['Field 0', '0', '0', '0', 'Field 1', '0.894118', '0.101961', '0.109804', 'Field 2', '0.215686', '0.494118',
                                       '0.721569', 'Field 3', '0.301961', '0.686275', '0.290196', 'Field 4', '0.596078', '0.305882', '0.639216', 'vtkOriginalIndices', '1', '0.498039', '0']
    DataRepresentation2.UseIndexForXAxis = 0
    DataRepresentation2.AttributeType = 'Row Data'
    DataRepresentation2.SeriesVisibility = [
        'vtkOriginalIndices', '0', 'Field 0', '1', 'Field 1', '0', 'Field 2', '0', 'Field 3', '0', 'Field 4', '0']
    DataRepresentation2.SeriesLabel = ['Field 0', 'log law']
    DataRepresentation2.SeriesColor = ['Field 0', '0.6', '0.6', '0.6']


# Create a line chart and plot data
root_directory = '/Users/jamil/Documents/ZenoTech/zCFD_DATA'
root_directory = '/Users/jamil/Documents'
# root_directory='/home/jamil'
root_directory = '/work/bristol/eisbr011/PLATE/SMOOTH'

XYChartView1 = CreateXYPlotView()
# plot_profile('',['0','0.5','1'],root_directory+'/PLATE/plate_coarse_P4_OUTPUT_NOMOV/plate_coarse')
# plot_profile('',['0.25','0.5','0.75'],root_directory+'/PLATE/plate_coarse_P4_OUTPUT/plate_coarse')
# plot_profile('',['0','0.5','1'],root_directory+'/PLATE/plate_fine_P1_OUTPUT/plate_fine')
# plot_profile('',['0','0.5','1'],root_directory+'/PLATE/plate_medium_f300_OUTPUT/plate_medium_f300')
# plot_profile('',['0.25','0.5','0.75'],root_directory+'/PLATE/plate_medium_f100_OUTPUT/plate_medium_f100')
# plot_profile('',['0.50','0.5','0.50'],root_directory+'/PLATE/plate_medium_f50_OUTPUT/plate_medium_f50')
# plot_profile('',['0.75','0.5','0.25'],root_directory+'/PLATE/plate_medium_f20_OUTPUT/plate_medium_f20')
# plot_profile('',['1','0.5','0'],root_directory+'/PLATE/plate_medium_testwf_OUTPUT/plate_medium_testwf')
root_directory = '/work/bristol/eisbr011/PLATE/SMOOTH'
plot_profile('', STANDARD_CHART_COLORS[
             0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_profile('', STANDARD_CHART_COLORS[
             1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_profile('', STANDARD_CHART_COLORS[
             2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_profile('', STANDARD_CHART_COLORS[
             3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_profile('', STANDARD_CHART_COLORS[
             4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
root_directory = '/work/bristol/eisbr011/PLATE/ROUGH'
plot_profile('', STANDARD_CHART_COLORS[
             0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_profile('', STANDARD_CHART_COLORS[
             1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_profile('', STANDARD_CHART_COLORS[
             2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_profile('', STANDARD_CHART_COLORS[
             3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_profile('', STANDARD_CHART_COLORS[
             4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
root_directory = '/work/bristol/eisbr011/PLATE/ROUGH_40'
plot_profile('', STANDARD_CHART_COLORS[
             0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_profile('', STANDARD_CHART_COLORS[
             1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_profile('', STANDARD_CHART_COLORS[
             2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_profile('', STANDARD_CHART_COLORS[
             3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_profile('', STANDARD_CHART_COLORS[
             4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
root_directory = '/work/bristol/eisbr011/PLATE/ROUGH_100'
plot_profile('', STANDARD_CHART_COLORS[
             0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_profile('', STANDARD_CHART_COLORS[
             1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_profile('', STANDARD_CHART_COLORS[
             2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_profile('', STANDARD_CHART_COLORS[
             3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_profile('', STANDARD_CHART_COLORS[
             4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
root_directory = '/work/bristol/eisbr011/PLATE/ROUGH_400'
plot_profile('', STANDARD_CHART_COLORS[
             0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_profile('', STANDARD_CHART_COLORS[
             1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_profile('', STANDARD_CHART_COLORS[
             2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_profile('', STANDARD_CHART_COLORS[
             3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_profile('', STANDARD_CHART_COLORS[
             4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')

root_directory = '/work/bristol/eisbr011/PLATE/SMOOTH'
#plot_profile('Low-Re Coarse',['1','0','1'],root_directory+'/PLATE/plate_coarse_OUTPUT/plate_coarse')
#plot_profile('Low-Re Coarse Moving',['1','0','1'],root_directory+'/PLATE/plate_coarse_moving_OUTPUT/plate_coarse_moving')
plot_theory()

XYChartView2 = CreateXYPlotView()
# plot_velocity_profile('',['0','0.5','1'],root_directory+'/PLATE/plate_coarse_P4_OUTPUT_NOMOV/plate_coarse')
# plot_velocity_profile('',['0.50','0.5','0.50'],root_directory+'/PLATE/plate_coarse_P4_OUTPUT/plate_coarse')
# plot_velocity_profile('',['0.25','0.5','0.75'],root_directory+'/PLATE/plate_medium_f100_OUTPUT/plate_medium_f100')
# plot_velocity_profile('',['0.75','0.5','0.25'],root_directory+'/PLATE/plate_medium_f20_OUTPUT/plate_medium_f20')
# plot_velocity_profile('',['1','0.5','0'],root_directory+'/PLATE/plate_medium_testwf_OUTPUT/plate_medium_testwf')
# plot_velocity_profile('Low-Re',['1','0','0'],root_directory+'/PLATE/plate_medium_OUTPUT/plate_medium')
#plot_velocity_profile('Low-Re Coarse',['1','0','1'],root_directory+'/PLATE/plate_coarse_OUTPUT/plate_coarse')
#plot_velocity_profile('Low-Re Coarse Moving',['1','0','1'],root_directory+'/PLATE/plate_coarse_moving_OUTPUT/plate_coarse_moving')
root_directory = '/work/bristol/eisbr011/PLATE/SMOOTH'
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
root_directory = '/work/bristol/eisbr011/PLATE/ROUGH'
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
root_directory = '/work/bristol/eisbr011/PLATE/ROUGH_40'
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
root_directory = '/work/bristol/eisbr011/PLATE/ROUGH_100'
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
root_directory = '/work/bristol/eisbr011/PLATE/ROUGH_400'
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      0], root_directory + '/plate_medium_P1_OUTPUT/plate_medium')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      1], root_directory + '/plate_medium_f20_P1_OUTPUT/plate_medium_f20')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      2], root_directory + '/plate_medium_f50_P1_OUTPUT/plate_medium_f50')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      3], root_directory + '/plate_medium_f100_P1_OUTPUT/plate_medium_f100')
plot_velocity_profile('', STANDARD_CHART_COLORS[
                      4], root_directory + '/plate_medium_f300_P1_OUTPUT/plate_medium_f300')
Render()
