
import math

def coriolis_parameter(latitude_degree):
    """
    return the coriolis parameter
    """
    # Earth rotation 
    omega = 7.2722e-5 # rad/self
    return 2.0*omega*math.sin(math.radians(latitude))

def surface_layer_height(friction_velocity,coriolis_parameter):
    """
    returns the height of the atmospheric boundary layer - Geostrophic height
    For neutral conditions this is the height of the ABL 
    """
    return friction_velocity/(6.0*coriolis_parameter)

def friction_velocity(wind_speed,height,roughness_length):
    """
    returns the friction velocity
    """
    return wind_speed*0.41/math.log(height/roughness_length)

def wind_speed(height,friction_velocity,roughness_length):
    """
    returns the wind speed at a given height
    
    May want to consider Deaves & Harris (1978) model for high speed wind
    """
    return friction_velocity/0.41 * math.log(height/roughness_length)

def wind_direction_to_beta(wind_dir_deg):
    """
    Beta = 0.0 -> [1.0,0.0,0.0]
    Wind = 0.0 -> [0.0,-1.0,0.0]
    
    Therefore Beta = Wind + 90.0
    """
    return 360.0 - (wind_dir_deg+90.0)
    
def vel_to_vxy(vel):
    """
    Speed of wind in xy plane
    """
    return math.sqrt(vel[0]*vel[0] + vel[1]*vel[1])

def vel_to_vxy_dir(vel):
    """
    Direction of wind in xy plane
    """
    vel_mag = math.sqrt(vel[0]*vel[0]+vel[1]*vel[1])
    vxy_dir = math.asin(vel[0]/vel_mag)
    vxy_dir = 360.0 - math.degrees(vxy_dir)
    return vxy_dir

def vel_to_upflow(vel):
    """
    Wind upflow angle
    """
    vel_mag = math.sqrt(vel[0]*vel[0]+vel[1]*vel[1]+vel[2]*vel[2])        
    upflow_angle = math.asin(vel[2]/vel_mag)
    upflow_angle = math.degrees(upflow_angle)
    return upflow_angle
