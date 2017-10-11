try:
    paraview.simple
except:
    from paraview.simple import *
paraview.simple._DisableFirstRenderCameraReset()

# Read solution
bolund_0_pvtu = XMLPartitionedUnstructuredGridReader(
    FileName=['/work/bristol/eisbr011/GH/bolund_P16_OUTPUT/bolund_0.pvtu'])
bolund_0_pvtu.UpdatePipeline()

# Read measurement points
output_points_txt = CSVReader(
    FileName=['/work/bristol/eisbr011/GH/output_points.txt'])
output_points_txt.MergeConsecutiveDelimiters = 1
output_points_txt.FieldDelimiterCharacters = ', '
output_points_txt.HaveHeaders = 0
output_points_txt.UpdatePipeline()

# Convert table to points
SetActiveSource(output_points_txt)
TableToPoints1 = TableToPoints()
TableToPoints1.XColumn = 'Field 0'
TableToPoints1.YColumn = 'Field 1'
TableToPoints1.ZColumn = 'Field 2'
TableToPoints1.UpdatePipeline()

# Sample solution at locations
SetActiveSource(bolund_0_pvtu)
ResampleWithDataset1 = ResampleWithDataset(Source=TableToPoints1)
ResampleWithDataset1.UpdatePipeline()

# Read in measured points
measured_points_txt = CSVReader(
    FileName=['/work/bristol/eisbr011/GH/Dir_239.dat'])
measured_points_txt.MergeConsecutiveDelimiters = 1
measured_points_txt.FieldDelimiterCharacters = ', '
measured_points_txt.HaveHeaders = 1
measured_points_txt.UpdatePipeline()

# Convert table to points
SetActiveSource(measured_points_txt)
TableToPoints2 = TableToPoints()
TableToPoints2.XColumn = 'x'
TableToPoints2.YColumn = 'y'
TableToPoints2.ZColumn = 'z'
TableToPoints2.UpdatePipeline()

# Convert measured data to m/s
#Calculator1 = Calculator(Input=TableToPoints2)
#Calculator1.AttributeMode = 'Point Data'
#Calculator1.Function = '(u_ut*ut)*iHat + (v_ut*ut)*jHat + (w_ut*ut)*kHat'
#Calculator1.ResultArrayName = 'Vm'
# Calculator1.UpdatePipeline()


DataRepresentation4 = Show()
Render()
