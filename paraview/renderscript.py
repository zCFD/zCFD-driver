try: paraview.simple
except: from paraview.simple import *
paraview.simple._DisableFirstRenderCameraReset()

wall_pvd = PVDReader( FileName='/scratch/co-appa1/AHMED/test_P24_OUTPUT/test_wall.pvd' )

Clip2 = Clip( ClipType="Plane", Input=wall_pvd)
#Clip2.Scalars = ['CELLS', 'cp']
#Clip2.ClipType = "Plane"
#Clip2.Value = 0.24902987480163574
Clip2.ClipType.Origin = [1.0439999103546143, 0.0, 0.001]
Clip2.ClipType.Normal = [0.0, 0.0, 1.0]
Clip2.UpdatePipeline()

ahmed_pvd = PVDReader( FileName='/scratch/co-appa1/AHMED/ahmed_P24_OUTPUT/ahmed.pvd' )

AnimationScene2 = GetAnimationScene()
AnimationScene2.EndTime = 697.0
AnimationScene2.PlayMode = 'Snap To TimeSteps'
AnimationScene2.AnimationTime = 415.0

CellDatatoPointData1 = CellDatatoPointData()
CellDatatoPointData1.UpdatePipeline()

Clip1 = Clip( ClipType="Box" )
Clip1.ClipType.Position = [-1.3877787807814457e-17, -1.3877787807814457e-17, 2.7755575615628914e-17]
Clip1.ClipType.Bounds = [-3.131999969482422, 5.21999979019165, -0.9350000023841858, 0.9350000023841858, -2.374872742905154e-09, 1.399999976158142]
Clip1.ClipType.Scale = [0.1, 0.22, 0.3]
Clip1.InsideOut = 1
Clip1.Crinkleclip = 1
Clip1.UpdatePipeline()


Contour1 = Contour( PointMergeMethod="Uniform Binning" )
Contour1.ContourBy = ['POINTS', 'Qcriterion']
Contour1.Isosurfaces = [250.0]

a1_cp_PVLookupTable = GetLookupTableForArray( "cp", 1, RGBPoints=[-1.7252761125564575, 0.23, 0.299, 0.754, -0.7464806586503983, 0.865, 0.865, 0.865, 0.232314795255661, 0.706, 0.016, 0.15], VectorMode='Magnitude', NanColor=[0.25, 0.0, 0.0], ColorSpace='Diverging', ScalarRangeInitialized=1.0 )

a1_cp_PiecewiseFunction = CreatePiecewiseFunction( Points=[-1.7252761125564575, 0.0, 0.5, 0.0, 0.232314795255661, 1.0, 0.5, 0.0] )

DataRepresentation4 = Show() # GetDisplayProperties( Contour1 )
DataRepresentation4.EdgeColor = [0.0, 0.0, 0.5000076295109483]
DataRepresentation4.SelectionPointFieldDataArrayName = 'cp'
DataRepresentation4.SelectionCellFieldDataArrayName = 'eddy'
DataRepresentation4.ColorArrayName = ('POINT_DATA', 'cp')
DataRepresentation4.LookupTable = a1_cp_PVLookupTable
DataRepresentation4.ScaleFactor = 0.08385616838932038
DataRepresentation4.Interpolation = 'Flat'

wall_rep = GetDisplayProperties( Clip2 )
wall_rep.DiffuseColor = [0.6, 0.6, 0.6]

RenderView2 = GetRenderView()
if not RenderView2:
    # When using the ParaView UI, the View will be present, not otherwise.
    RenderView2 = CreateRenderView()

RenderView2.CameraViewUp = [-0.35, 0.26, 0.89]
RenderView2.CameraPosition = [1.4, -1.2, 1.0]
RenderView2.CameraFocalPoint = [0.1, 0.0, 0.21]
RenderView2.CameraParallelScale = 0.499418869125992
RenderView2.CenterOfRotation = [0.1, 0.0, 0.2]
RenderView2.CenterAxesVisibility = 0
RenderView2.ViewSize = [3840,2160]
RenderView2.LightSwitch=0
RenderView2.UseLight = 1

Render()


# Create Key Frames
frame1 = CameraKeyFrame()
#frame1.FocalPathPoints = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
#frame1.PositionPathPoints = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
frame1.ClosedPositionPath = 1
#frame1.ParallelScale = 1.73205
frame1.Position = [1.4, -1.2, 1.0]
frame1.ViewUp = [-0.35, 0.26, 0.89]
frame1.KeyTime = 400.0/697.0

frame2 = CameraKeyFrame()
frame2.Position = [1.4, 0.0, 0.5]
frame2.ViewUp = [0.0, 0.0, 1.0]
frame2.KeyTime = 450.0/697.0

frame3 = CameraKeyFrame()
frame3.Position = [1.4, 1.2, 1.0]
frame3.ViewUp = [-0.35, -0.26, 0.89]
frame3.KeyTime = 500.0/697.0

frame4 = CameraKeyFrame()
frame4.Position = [1.4, 0.0, 1.5]
frame4.ViewUp = [0.0, 0.0, 1.0]
frame4.KeyTime = 550.0/697.0

frame5 = CameraKeyFrame()
frame5.Position = [1.4, -1.2, 1.0]
frame5.ViewUp = [-0.35, 0.26, 0.89]
frame5.KeyTime = 600.0/697.0

CameraAnimationCue3 = GetCameraTrack()
CameraAnimationCue3.Mode = 'Interpolate Camera'
CameraAnimationCue3.AnimatedProxy = RenderView2
CameraAnimationCue3.KeyFrames = [ frame1, frame2, frame3, frame4, frame5 ]

TimeAnimationCue4 = GetTimeTrack()

print 'Generating: ' + str(415)
WriteImage('ahmed250f_'+str(415)+'.png')

for t in range(416,601):
    print 'Generating: ' + str(t)
    AnimationScene2.AnimationTime = t
    WriteImage('ahmed250f_'+str(t)+'.png')

