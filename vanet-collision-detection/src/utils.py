import math
import numpy as np

def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance between two 2D points"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

def calculate_angle(pos1, pos2):
    """Calculate angle between two points (in degrees)"""
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    
    # Convert to standard angle (0 = east, counterclockwise)
    angle = math.degrees(math.atan2(dy, dx))
    
    # Normalize to [0,360)
    return angle % 360

def predict_position(position, speed, angle, time_delta):
    """Predict future position based on current position, speed, and direction"""
    # Convert angle from SUMO format (clockwise from north) to standard (counterclockwise from east)
    math_angle = (90 - angle) % 360
    math_angle_rad = math.radians(math_angle)
    
    # Project position
    x = position[0] + speed * math.cos(math_angle_rad) * time_delta
    y = position[1] + speed * math.sin(math_angle_rad) * time_delta
    
    return (x, y)

def calculate_ttc(p1, v1, p2, v2):
    """
    Calculate Time-to-Collision between two vehicles
    
    Args:
        p1, p2: Position vectors of vehicles 1 and 2
        v1, v2: Velocity vectors of vehicles 1 and 2
        
    Returns:
        Time-to-Collision in seconds, or infinity if no collision
    """
    # Convert to numpy arrays
    p1 = np.array(p1)
    p2 = np.array(p2)
    v1 = np.array(v1)
    v2 = np.array(v2)
    
    # Calculate relative position and velocity
    dP = p2 - p1
    dV = v2 - v1
    
    # Check if relative velocity is zero
    dV_magnitude = np.linalg.norm(dV)
    if dV_magnitude < 0.0001:
        return float('inf')
    
    # Calculate time to closest approach
    t_closest = -np.dot(dP, dV) / (dV_magnitude**2)
    
    # If time is negative, vehicles are moving away from each other
    if t_closest < 0:
        return float('inf')
    
    # Calculate closest distance
    closest_point = dP + t_closest * dV
    closest_distance = np.linalg.norm(closest_point)
    
    # Define threshold for collision (sum of vehicle radii)
    # This is a simplified approximation - real implementation would use vehicle dimensions
    collision_threshold = 2.5  # meters
    
    if closest_distance < collision_threshold:
        return t_closest
    else:
        return float('inf')