import math
import ast
import sys
from paraview.simple import *
import numpy as np
import post
import zutil

# Usage
#import zutil.farm as farm
#farm.create_mesh_sources('London_Array_ZCFD.py',(396000,5721000))

#farm.create_mesh_sources('Horns_Rev_ZCFD.py',(427000,6149500))
#f.create_zcfd_input('Horns_Rev_ZCFD.py',(427000,6149500))

#http://jthatch.com/Terrain2STL/

def create_mesh_sources(array_data_file, farm_centre, turbine_only=False):
    
    # Read file
    
    array_data = {}
    
    with open(array_data_file,"r") as f:
        s = f.read()
        array_data = ast.literal_eval(s)
    
    # Cases
    cases = array_data['Cases']
    
    for (key,value) in cases.items():
        #print key
    
        # Wind direction
        wind_direction = key
    
        # Turbines
        turbines = array_data['Turbines']
        
        # List of tuples
        mesh_source_location = []
        
        for (key,value) in turbines.items():
            #print key
            name = key
            if isinstance(key,int):
                name = 'A'+str(key)
            
            # Location as a tuple
            turbine_location = (value['X'],value['Y'],float(value['Z']))
            
            # Convert to local coordinates
            turbine_location = convert_to_local_coordinates(turbine_location,farm_centre)
            
            # Compute new location
            turbine_location = get_turbine_location(turbine_location,wind_direction)
            
            turbine_diameter = float(value['RotorDiameter'])
            # Create line source using turbine diameter            
            source = create_source(turbine_location,turbine_diameter)
            mesh_source_location.append(source)
            
            generate_turbine(name,turbine_location,turbine_diameter,wind_direction)
            if not turbine_only:
                generate_turbine_region(name,turbine_location,turbine_diameter,wind_direction)
            
                
        if not turbine_only:
            # Write Solar .bac file
            write_solar_bac('wind-'+str(wind_direction)+'.bac',wind_direction,mesh_source_location)
            # Write Solar .ctl file
            write_control_file('wind-'+str(wind_direction)+'.ctl')  
    
    
def create_turbines(array_data_file, wall_file, volume_file):
    
    array_data = {}
    
    with open(array_data_file,"r") as f:
        s = f.read()
        array_data = ast.literal_eval(s)
    
    # Read terrain
    terrain = PVDReader(FileName=wall_file)
    terrain = CleantoGrid(Input=terrain)
    bounds = terrain.GetDataInformation().GetBounds()
    # Elevation
    elevation = Elevation(Input=terrain)
    elevation.LowPoint = [0,0,bounds[4]]
    elevation.HighPoint = [0,0,bounds[5]]
    elevation.ScalarRange = [bounds[4],bounds[5]]
    # Flatten
    transform = Transform(Input=elevation)
    transform.Transform = 'Transform'
    transform.Transform.Scale = [1.0, 1.0, 0.0]
    transform.UpdatePipeline()
    
    # create a new 'Probe Location'
    probeLocation = ProbeLocation(Input=transform,ProbeType='Fixed Radius Point Source')
    probeLocation.Tolerance = 2.22044604925031e-16

    # Read volume
    volume = PVDReader(FileName=volume_file)
    volume = CleantoGrid(Input=volume)
    volume.UpdatePipeline()
    hubProbe = ProbeLocation(Input=volume,ProbeType='Fixed Radius Point Source')
    hubProbe.Tolerance = 2.22044604925031e-16
    

    # Cases
    cases = array_data['Cases']
    
    for (key,value) in cases.items():
        #print key
    
        # Wind direction
        wind_direction = key
    
        # Turbines
        turbines = array_data['Turbines']
        
        # List of tuples
        location = []
        
        for (key,value) in turbines.items():
            #print key
            name = key
            if isinstance(key,int):
                name = 'A'+str(key)
            
            # Location as a tuple
            turbine_location = (value['X'],value['Y'],float(value['Z']))
            
            # Find terrain elevation at X and Y
            probeLocation.ProbeType.Center = [turbine_location[0], turbine_location[1], 0.0]
            probeLocation.UpdatePipeline()
            
            ground = probeLocation.GetPointData().GetArray("Elevation").GetValue(0)
            
            turbine_location = (value['X'],value['Y'],ground+float(value['Z']))
            
            turbine_diameter = float(value['RotorDiameter'])

            # Get wind direction at hub
            hubProbe.ProbeType.Center = [turbine_location[0],
                                         turbine_location[1],
                                         turbine_location[2]]
            hubProbe.UpdatePipeline()
            (u,v) = hubProbe.GetPointData().GetArray("V").GetValue(0)
            
            local_wind_direction = wind_direction(u,v)
            
            # Thrust Coefficient
            tc = value['ThrustCoEfficient']
            try:
                thrust_coefficient = float(value['ThrustCoEfficient'][-1])
            except:
                 thrust_coefficient = float(value['ThrustCoEfficient'])
            
            turbine_diameter = float(value['RotorDiameter'])
                        
            # Point turbine into the wind
            turbine_normal = [-u,-v,0.0]
            mag = math.sqrt(sum(x**2 for x in turbine_normal))
            turbine_normal = [-u/mag,-v/mag,0.0]
            
            generate_turbine(name,turbine_location,turbine_diameter,wind_direction,True)
            if not turbine_only:
                generate_turbine_region(name,turbine_location,turbine_diameter,wind_direction,True)
                
            location.append((name,
                             wind_direction,
                             turbine_location,
                             turbine_diameter,
                             thrust_coefficient,
                             turbine_normal))
              
        # Write zone definition
        write_zcfd_zones('wind-'+str(wind_direction)+'_zone.py',location)    
    pass

    
def create_zcfd_input(array_data_file, farm_centre):
    # Read file
    
    array_data = {}
    
    with open(array_data_file,"r") as f:
        s = f.read()
        array_data = ast.literal_eval(s)
    
    # Cases
    cases = array_data['Cases']
    
    for (key,value) in cases.items():
        #print key

        # Wind direction
        wind_direction = key
        
        # Wind Speed
        wind_speed = value['Windspeed']

        density = value['AirDensity']
    
        # Turbines
        turbines = array_data['Turbines']
        
        # List of tuples
        location = []
        
        for (key,value) in turbines.items():
            #print key
            name = key
            if isinstance(key,int):
                name = 'A'+str(key)            
            # Location as a tuple
            turbine_location = (value['X'],value['Y'],float(value['Z']))
            
            # Convert to local coordinates
            turbine_location = convert_to_local_coordinates(turbine_location,farm_centre)
            
            # Compute new location
            turbine_location = get_turbine_location(turbine_location,wind_direction)
            
            # Thrust Coefficient
            tc = value['ThrustCoEfficient']
            try:
                thrust_coefficient = float(value['ThrustCoEfficient'][-1])
            except:
                 thrust_coefficient = float(value['ThrustCoEfficient'])
            
            turbine_diameter = float(value['RotorDiameter'])

            location.append((name,wind_direction,turbine_location,turbine_diameter,thrust_coefficient))
            
        # Write zone definition
        write_zcfd_zones('wind-'+str(wind_direction)+'_zone.py',location)
            
    pass

def write_zcfd_zones(zcfd_file_name,location):
    
    with open(zcfd_file_name,'w') as f:
        for idx,val in enumerate(location):
            f.write('\'FZ_'+str(idx+1)+'\':{\n')
            f.write('\'type\':\'disc\',\n')
            f.write('\'def\':\''+str(val[0])+'-'+str(val[1])+'.vtp\',\n')
            f.write('\'thrust coefficient\':'+str(val[4])+',\n')
            f.write('\'tip speed ratio\':'+str(6.0)+',\n')
            f.write('\'centre\':['+str(val[2][0])+','+str(val[2][1])+','+str(val[2][2])+'],\n')
            f.write('\'up\':[0.0,0.0,1.0],\n')
            if len(val) > 5:
                f.write('\'normal\':['+str(val[5][0])+','+str(val[5][1])+','+str(val[5][2])+'],\n')
            else:
                f.write('\'normal\':[-1.0,0.0,0.0],\n')
            f.write('\'inner radius\':'+str(0.05*val[3]/2.0)+',\n')
            f.write('\'outer radius\':'+str(val[3]/2.0)+',\n')
            f.write('},\n')
    pass
    
def generate_turbine_region(turbine_name,turbine_location,turbine_diameter,wind_direction,rotate=False):
    
    cylinder = Cylinder()
    cylinder.Radius = 0.5*turbine_diameter
    cylinder.Resolution = 128
    cylinder.Height = 2.0*turbine_diameter
    
    transform = Transform()
    transform.Transform = "Transform"
    transform.Transform.Rotate = [0.0,0.0,90.0]
    if rotate:
        transform.Transform.Rotate = [0.0,0.0,-wind_direction]
    transform.Transform.Translate = [turbine_location[0],turbine_location[1],turbine_location[2]]
    
    writer = CreateWriter(turbine_name+'-'+str(wind_direction)+'.vtp')
    writer.Input = transform
    writer.UpdatePipeline()

def generate_turbine(turbine_name,turbine_location,turbine_diameter,wind_direction,rotate=False):
    
    disk = Disk()
    disk.InnerRadius = 0.05*0.5*turbine_diameter
    disk.OuterRadius = 0.5*turbine_diameter
    disk.CircumferentialResolution = 128
    disk.RadialResolution = 12
    
    transform = Transform()
    transform.Transform = "Transform"
    transform.Transform.Rotate = [0.0,90.0,0.0]
    if rotate:
        transform.Transform.Rotate = [0.0,90.0,90.0-wind_direction]
    transform.Transform.Translate = [turbine_location[0],turbine_location[1],turbine_location[2]]
    
    writer = CreateWriter(turbine_name+'-'+str(wind_direction)+'-disk.vtp')
    writer.Input = transform
    writer.UpdatePipeline()

def write_control_file(control_file_name):
    
    with open(control_file_name,'w') as f:
        f.write('domain:  -50000 50000 -50000 50000 0 1000.0'+'\n')
        f.write('initial: 5000.0'+'\n')
        f.write('generateCartOnly: true'+'\n')
        f.write('generateLayer: false'+'\n')

def create_source(turbine_location, diameter):
    
    upstream_factor = 1.0
    downstream_factor = 4.0
    radial_factor = 1.0
    diameter_mesh_pts = 50.0
    radius_factor = 2.0
    
    # Upstream
    pt_1 = turbine_location[0] - upstream_factor*diameter
    # Downstream
    pt_2 = turbine_location[0] + downstream_factor*diameter
    # Radius
    radius = 0.5*diameter*radial_factor
    # Mesh size
    mesh_size = diameter/diameter_mesh_pts
    
    return ((pt_1,turbine_location[1],turbine_location[2],mesh_size,radius,radius*radius_factor),
            (pt_2,turbine_location[1],turbine_location[2],mesh_size,radius,radius*radius_factor))
        
def write_solar_bac(bac_file_name,wind_direction,mesh_source):
    
    farfield_mesh_size = 5000.0
    
    with open(bac_file_name,'w') as f:
        f.write('zCFD Farmer - wind direction: '+str(wind_direction)+'\n')
        f.write(' 8 6'+'\n')
        f.write('  1  1.0e+6 -1.0e+6 -1.0e+6'+'\n')
        f.write('  1.0 0.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 1.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 0.0 1.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  2  1.0e+6  1.0e+6 -1.0e+6'+'\n')
        f.write('  1.0 0.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 1.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 0.0 1.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  3 -1.0e+6 -1.0e+6 -1.0e+6'+'\n')
        f.write('  1.0 0.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 1.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 0.0 1.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  4 -1.0e+6  1.0e+6 -1.0e+6'+'\n')
        f.write('  1.0 0.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 1.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 0.0 1.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  5  1.0e+6 -1.0e+6  1.0e+6'+'\n')
        f.write('  1.0 0.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 1.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 0.0 1.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  6  1.0e+6  1.0e+6  1.0e+6'+'\n')
        f.write('  1.0 0.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 1.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 0.0 1.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  7 -1.0e+6 -1.0e+6  1.0e+6'+'\n')
        f.write('  1.0 0.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 1.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 0.0 1.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  8 -1.0e+6  1.0e+6  1.0e+6'+'\n')
        f.write('  1.0 0.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 1.0 0.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  0.0 0.0 1.0 ' + str(farfield_mesh_size)+'\n')
        f.write('  1  1  2  4  8'+'\n')
        f.write('  2  1  2  8  6'+'\n')
        f.write('  3  1  6  8  5'+'\n')
        f.write('  4  2  3  4  7'+'\n')
        f.write('  5  2  7  4  8'+'\n')
        f.write('  6  2  7  8  6'+'\n')
        f.write(' background sources...'+'\n')
        f.write(' 0 ' + str(len(mesh_source)) + ' 0'+'\n')
        f.write(' The points'+'\n')
        f.write(' The lines'+'\n')
        for s in mesh_source:
            pt_1 = s[0]
            pt_2 = s[1]
            f.write('Line Source :'+'\n')
            f.write( ' '.join( str(elem) for elem in pt_1) +'\n' )
            f.write( ' '.join( str(elem) for elem in pt_2) +'\n')
        f.write(' The triangles'+'\n')
        


def convert_to_local_coordinates(turbine_location, farm_centre):
    # Converts location from Eastings and Northings into local coordinates
    # 
    
    local_coordinates = (turbine_location[0] - farm_centre[0],
                         turbine_location[1] - farm_centre[1],
                         turbine_location[2])
    return local_coordinates

def get_turbine_location(current_location, wind_direction):
    # Assume that the CFD solver expects freestream flow in x-direction 
    # Rotate farm about its centre to account for the actual wind direction 
    # i.e. if the wind is coming from the West (270 degrees), then there is no rotation.
    # In general: rotate wind farm in standard co-ordinate geometry sense 
    # about centre by (wind direction + 90 degrees)
    rotation_angle = (wind_direction + 90.0)
    rotation_angle = math.radians(rotation_angle)
    
    x_temp = current_location[0]
    y_temp = current_location[1]
    new_x_temp = ( x_temp*math.cos(rotation_angle)
                  +y_temp*math.sin(rotation_angle))
    new_y_temp = (-x_temp*math.sin(rotation_angle)
                  +y_temp*math.cos(rotation_angle))

    return (new_x_temp,new_y_temp,current_location[2])


def report_data_reader(name, arr1, arr2):
    var = -999.0
    idx = np.where(arr1 == name)
    if (len(idx[0].flat) == 0):
        print 'farm.py : report_data_reader : no data found in results file for ' + name
    elif (len(idx[0].flat) == 1):
        var = float(arr2[idx[0]][0])
    else:
        print 'farm.py : report_data_reader : multiple columns in data results file for ' + name + ' ' + len(idx[0].flat)
    return var

min_dist=1.0e16
closest_point = [min_dist, min_dist, min_dist]

def closest_point_func(dataset, pointset, s=[0,0,0], **kwargs):
    global min_dist, closest_point
    points = pointset.GetPoints()
    for p in points:
        dx = s[0]-p[0]
        dy = s[1]-p[1]
        dz = s[2]-p[2]
        dist = math.sqrt(dx*dx + dy*dy) #  + dz*dz)
        if (dist < min_dist):
            closest_point = p
            min_dist = dist

def write_windfarmer_data(case_name, num_processes, up):
    # case_name = 'windfarm' (for example - note that there is no .py suffix)
    # ground_zone = 1 (for example, an integer)
    # num_processes = 24 (for example, an integer)
    # up = [0,1,0] (the vector pointing vertically upwards)
    global min_dist, closest_point
    # Step 1: Read the case file parameters
    __import__(case_name)
    case_data = getattr(sys.modules[case_name], 'parameters')
    
    # Step 2: Determine the (conventional) wind direction from the case inflow parameters
    v = case_data['IC_1']['V']['vector']
    print 'farm.py : write_windfarmer_data : v = ' + str(v)
    import numpy as np
    angle = 270.0 - np.angle(complex(v[0], v[1]), deg=True)
    if (angle < 0.0):
        angle += 360.0
    if (angle > 360.0):
        angle -= 360.0
    print 'farm.py : write_windfarmer_data : angle = ' + str(angle)

    #Step 3: Import the result file data incuding the probe data
    windfarmer_filename = case_name + "_" + str(angle)+'.out'
    print 'farm.py : write_windfarmer_data : windfarmer_filename = ' + windfarmer_filename
    report_file_name = case_name+'_report.csv'
    report_array = np.genfromtxt(report_file_name, dtype=None)
    
    # Step 4: Calculate the ground heights at the probe locations by subtracting the local height of the wall
    reader = OpenDataFile('./' + case_name + '_P' + str(num_processes) + '_OUTPUT/' + case_name +'_wall.pvd')
    local_surface = servermanager.Fetch(reader)
    
    # Step 5: Loop over the probe locations plus the results to create the Windfarmer file.
    with open(windfarmer_filename,'w') as f:
        f.write('"Point","X[m]","Y [m]","Z ground [m]","Z hub [m]","H [m]","D [m]","Theta[Deg]","TI hub","TI upper",' +
                '"TI lower","TI15 hub","TI15 upper","TI15 lower","Vxy hub [m/s]","Vxy upper [m/s]","Vxy lower [m/s]","Windshear [-]",' +
                '"Theta left [Deg]","Theta hub [Deg]","Theta right [Deg]","Veer [Deg]","Local Elevation Angle [Deg]","Simple Power [kW]",' +
                '"V/VT01_sample_vxy [-]","Power (Sector) [kW]","AEP (Sector) [kWh]","NEC [kWh]" \n')
        for probe in case_data['report']['monitor']:
            point =  case_data['report']['monitor'][probe]['point']
            name = case_data['report']['monitor'][probe]['name']
                            
            # Step 5.1: Find the report data for the windfarmer probe if it exists.
            V_x = report_data_reader(name+'_V_x', report_array[0], report_array[len(report_array)-1])
            V_y = report_data_reader(name+'_V_y', report_array[0], report_array[len(report_array)-1])
            V_z = report_data_reader(name+'_V_z', report_array[0], report_array[len(report_array)-1])
            TI_hub = report_data_reader(name+'_ti', report_array[0], report_array[len(report_array)-1])
            VXY_hub = math.sqrt(V_x*V_x + V_y*V_y)
            Theta_hub = 270.0 - np.angle(complex(V_x, V_y), deg=True)
            if (Theta_hub < 0.0):
                Theta_hub += 360.0
            if (Theta_hub > 360.0):
                Theta_hub -= 360.0
            Local_Elevation_Angle = np.angle(complex(VXY_hub, V_z), deg=True)
                                                                
            # Step 5.2: Swap the axes if necessary to match the Windfarmer default (z-axis is up)
            if (up[0] == 0):
                x = point[0]
                if (up[1] == 0):
                    y = point[1]
                    z = point[2]
                elif (up[2] == 0):
                    y = point[2]
                    z = point[1]
            else:
                x = point[1]
                y = point[2]
                z = point[0]
                                                                                                                
            # Step 5.3: Find the closest ground point to the probe to work out elevation
            min_dist=1.0e16
            closest_point = [min_dist, min_dist, min_dist]
            post.for_each(local_surface, closest_point_func, s=[x,y,z])
            zground = up[0]*closest_point[0] + up[1]*closest_point[1] + up[2]*closest_point[2]
            zhub = up[0]*x + up[1]*y + up[2]*z
                
            # Step 5.4: Output the Windfarmer data
            f.write(name + "," + str(x) + "," + str(y) + "," + str(zground) + "," + str(zhub) + "," +
            str(zhub-zground) + "," + "," + str(angle) + "," + str(TI_hub) + ",,,,,," + str(VXY_hub) + ",,,,," +
            str(Theta_hub) + ",,," + str(Local_Elevation_Angle) + ",,,,, \n")
        print 'farm.py : write_windfarmer_data : DONE'

def create_trbx_zcfd_input(case_name = 'windfarm',
                           wind_direction = '0.0',
                           reference_wind_speed = 10.0,
                           num_processes = 1,
                           report_frequency = 1000,
                           turbine_files=[['xyz_location_file1.txt', 'turbine_type1.trbx'],
                                          ['xyz_location_file2.txt', 'turbine_type2.trbx']],
                            **kwargs):
    global min_dist, closest_point
    from xml.etree import ElementTree as ET
    reader = OpenDataFile('./' + case_name + '_P' + str(num_processes) + '_OUTPUT/' + case_name +'_wall.pvd')
    local_surface = servermanager.Fetch(reader)
    # Step 1: Read in the location data (.txt) and turbine information (.trbx) for each turbine type
    idx = 0
    with open(case_name+'_zones.py','w') as tz:
        tz.write('turb_zone = {\n')
        with open(case_name+'_probes.py','w') as tp:
            tp.write('turb_probe = { \n \'report\' : { \n    \'frequency\' : '+str(report_frequency)+',\n     \'monitor\' : { \n')
            for [location_file_name, trbx_file_name] in turbine_files:
                print 'trbx file name = ' + trbx_file_name
                trbx = ET.ElementTree(file = trbx_file_name)
                # ET.dump(trbx)
                root = trbx.getroot()
                turbine_dict = {}
                # print elem.tag, elem.attrib
                for elem in root:
                    turbine_dict[elem.tag] = elem.text
                for elem in trbx.find('Turbine3DModel'):
                    turbine_dict[elem.tag] = elem.text
                for elem in trbx.find('PerformanceTableList/PerformanceTable/PowerCurveInfo'):
                    turbine_dict[elem.tag] = elem.text
                for elem in trbx.find('PerformanceTableList/PerformanceTable/PowerCurveInfo/StartStopStrategy'):
                    turbine_dict[elem.tag] = elem.text
                turbine_dict['DataTable'] = {}
                wp = 0
                for elem in trbx.find('PerformanceTableList/PerformanceTable/DataTable'):
                    turbine_dict['DataTable'][wp] = {}
                    for child in elem:
                        turbine_dict['DataTable'][wp][child.tag] = child.text
                    wp+=1
                # print turbine_dict
                print 'location file name = ' + location_file_name
                location_array = np.genfromtxt(location_file_name, dtype=None)
                for location in location_array:
                    idx+=1
                    name = location[0]
                    easting = location[1]
                    northing = location[2]
                                                                  
                    # Step 2: Work out the local elevation
                    min_dist=1.0e16
                    closest_point = [min_dist, min_dist, min_dist]
                    post.for_each(local_surface, closest_point_func, s=[easting,northing,0.0])
                    height = closest_point[2]
                    hub_z = height+float(turbine_dict['SelectedHeight'])
                                                                  
                    # Step 3: Generate the turbine region files (./turbine_vtp/*.vtp)
                    generate_turbine_region('./turbine_vtp/'+name,
                                            [easting, northing, hub_z],
                                            float(turbine_dict['RotorDiameter']),
                                            wind_direction)
                                                                  
                    # Step 4: Generate the turbine zone definition (./turbine_zone.py)
                    rd = float(turbine_dict['RotorDiameter'])
                    tz.write('\'FZ_'+str(idx)+'\':{\n')
                    tz.write('\'type\':\'disc\',\n')
                    tz.write('\'def\':\'./turbine_vtp/'+name+'-'+str(wind_direction)+'.vtp\',\n')
                    if (len(turbine_dict['DataTable'].keys())==0):
                        print 'WARNING: Windspeed DataTable empty - using Reference Wind Speed = ' + str(reference_wind_speed)
                    wsc = np.zeros((3,len(turbine_dict['DataTable'].keys())))
                    tcc_string = '[' # Thrust coefficient curve
                    tsc_string = '[' # Tip speed ratio curve
                    for wp in turbine_dict['DataTable'].keys():
                         wsc[0][wp] = turbine_dict['DataTable'][wp]['WindSpeed']
                         wsc[1][wp] = turbine_dict['DataTable'][wp]['ThrustCoEfficient']
                         wsc[2][wp] = turbine_dict['DataTable'][wp]['RotorSpeed']
                         tcc_string += '[' +str(wsc[0][wp]) + ',' + str(wsc[1][wp]) + '],'
                         tsc_string += '[' +str(wsc[0][wp]) + ',' + str(((wsc[2][wp]*math.pi/30.0)*rd/2.0)/max(wsc[0][wp],1.0)) + '],'
                    tcc_string += ']'
                    tsc_string += ']'
                    # print wsc
                    # If there is a single value for thrust coefficient use the reference wind speed
                    tc = np.interp(reference_wind_speed, wsc[0], wsc[1])
                    tz.write('\'thrust coefficient\':'+str(tc)+',\n')
                    tz.write('\'thrust coefficient curve\':' + tcc_string + ',\n')
                    rs = np.interp(reference_wind_speed, wsc[0], wsc[2])
                    # The rotor speed is in revolutions per minute, so convert to tip speed ratio
                    tsr = ((rs*math.pi/30.0)*rd/2.0)/reference_wind_speed
                    tz.write('\'tip speed ratio\':'+str(tsr)+',\n')
                    tz.write('\'tip speed ratio curve\':' + tsc_string + ',\n')
                    tz.write('\'centre\':['+str(easting)+','+str(northing)+','+str(hub_z)+'],\n')
                    tz.write('\'up\':[0.0,0.0,1.0],\n')
                    wv = zutil.vector_from_wind_dir(wind_direction)
                    tz.write('\'normal\':['+str(-wv[0])+','+str(-wv[1])+','+str(-wv[2])+'],\n')
                    tz.write('\'inner radius\':'+str(float(turbine_dict['DiskDiameter'])/2.0)+',\n')
                    tz.write('\'outer radius\':'+str(float(turbine_dict['RotorDiameter'])/2.0)+',\n')
                    pref_offset = rd
                    pref = [easting - pref_offset*wv[0], northing - pref_offset*wv[1], hub_z - pref_offset*wv[2]]
                    tz.write('\'reference point\':['+str(pref[0])+','+str(pref[1])+','+str(pref[2])+'],\n')
                    tz.write('},\n')
                                                                  
                    # Step 5: Generate the turbine monitor probes (./turbine_probe.py)
                    # Turbines:    label@MHH@## (## = hub height of the turbine relative to the ground in meters)
                    # Anemometers: label@AN@##  (## = height of the anemometer above the ground in meters)
                    tp.write('        \'MR_'+str(idx)+'\' : {\n')
                    tp.write('        \'name\' :\'probe'+str(idx)+'@MHH@'+turbine_dict['SelectedHeight']+'\',\n')
                    tp.write('        \'point\' : ['+str(easting)+','+str(northing)+','+str(hub_z)+'],\n')
                    tp.write('        \'variables\' : [\'V\', \'ti\'],\n')
                    tp.write('        },\n')
            tp.write('},\n  },\n } \n')
        tz.write('}\n')