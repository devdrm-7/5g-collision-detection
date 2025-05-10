import math
import numpy as np
import time
import os

class CollisionDetector:
    def __init__(self, time_threshold=3.0, distance_threshold=30.0, simulation_start_time=None):
        """
        Initialize collision detector with thresholds
        
        Args:
            time_threshold: Time-to-collision threshold in seconds
            distance_threshold: Maximum distance to consider for collision detection
            simulation_start_time: Reference time when simulation started
        """
        self.time_threshold = time_threshold
        self.distance_threshold = distance_threshold
        self.simulation_start_time = simulation_start_time or time.time()
        self.step_length = 0.1  # Default SUMO step length in seconds
        self.step = 0
        self.log_file = "data/collision_log.txt"
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize log file
        with open(self.log_file, 'w') as f:
            f.write("Timestamp,Vehicle1,Vehicle2,TTC,Distance,Severity\n")
    
    def detect_collisions(self, vehicles_data):
        """
        Detect potential collisions between vehicles
        
        Args:
            vehicles_data: Dictionary with vehicle IDs as keys and position/velocity as values
            
        Returns:
            List of tuples (vehicle1_id, vehicle2_id, ttc) representing potential collisions
        """
        self.step += 1
        collision_pairs = []
        vehicle_ids = list(vehicles_data.keys())
        
        # Compare each pair of vehicles
        for i in range(len(vehicle_ids)):
            for j in range(i+1, len(vehicle_ids)):
                v1_id = vehicle_ids[i]
                v2_id = vehicle_ids[j]
                
                v1 = vehicles_data[v1_id]
                v2 = vehicles_data[v2_id]
                
                # Calculate distance between vehicles
                distance = self._calculate_distance(v1['position'], v2['position'])
                
                # Skip if vehicles are too far apart
                if distance > self.distance_threshold:
                    continue
                
                # Calculate Time-to-Collision (TTC)
                ttc = self._calculate_ttc(v1, v2)
                
                # If TTC is within our threshold, report potential collision
                if 0 < ttc < self.time_threshold:
                    collision_pairs.append((v1_id, v2_id, ttc))
                    severity = self._calculate_severity(ttc, distance, v1['speed'], v2['speed'])
                    self._log_collision(v1_id, v2_id, ttc, distance, severity)
        
        return collision_pairs
    
    def _calculate_distance(self, pos1, pos2):
        """Calculate Euclidean distance between two positions"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _calculate_ttc(self, v1, v2):
        """
        Calculate Time-to-Collision (TTC) based on position, speed and direction
        Returns infinity if vehicles are not on collision course
        """
        # Extract positions and convert to numpy arrays for vector calculations
        p1 = np.array(v1['position'])
        p2 = np.array(v2['position'])
        
        # Calculate relative position vector
        rel_pos = p2 - p1
        
        # Convert angles from SUMO (clockwise from north) to standard math (counterclockwise from east)
        angle1 = (90 - v1['angle']) % 360
        angle2 = (90 - v2['angle']) % 360
        
        # Calculate velocity vectors
        v1_speed = v1['speed']
        v2_speed = v2['speed']
        
        v1_vel = np.array([v1_speed * math.cos(math.radians(angle1)), 
                           v1_speed * math.sin(math.radians(angle1))])
        v2_vel = np.array([v2_speed * math.cos(math.radians(angle2)), 
                           v2_speed * math.sin(math.radians(angle2))])
        
        # Calculate relative velocity vector
        rel_vel = v2_vel - v1_vel
        
        # If relative speed is zero or negligible, no collision
        if np.linalg.norm(rel_vel) < 0.1:
            return float('inf')
        
        # Calculate Time-to-Collision (TTC)
        # This uses the dot product to project the relative position onto the relative velocity
        # divided by the squared magnitude of the relative velocity
        ttc_candidates = []
        
        # Check if vehicles are approaching each other
        dot_product = np.dot(rel_pos, rel_vel)
        if dot_product < 0:  # Negative dot product means vehicles are approaching
            ttc = -np.dot(rel_pos, rel_vel) / np.dot(rel_vel, rel_vel)
            ttc_candidates.append(ttc)
        
        # Account for vehicle dimensions (rectangular approximation)
        # This is a simplified approach - a more detailed collision detection would consider the exact
        # rectangles of the vehicles and their overlapping
        
        if not ttc_candidates:
            return float('inf')
        
        return min(ttc_candidates)
    
    def _calculate_severity(self, ttc, distance, speed1, speed2):
        """Calculate collision severity based on TTC, distance and speeds"""
        # Simple severity calculation based on TTC and relative speed
        relative_speed = abs(speed1 - speed2)
        
        if ttc < 1.0:
            if relative_speed > 10.0:
                return "CRITICAL"
            else:
                return "HIGH"
        elif ttc < 2.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _log_collision(self, v1_id, v2_id, ttc, distance, severity):
        """Log collision data to file with simulation time"""
        # Calculate simulation time from step number
        elapsed_time = self.step * self.step_length
        formatted_time = f"{int(elapsed_time/60):02d}:{int(elapsed_time%60):02d}.{int((elapsed_time%1)*10):01d}"
        
        with open(self.log_file, 'a') as f:
            f.write(f"{formatted_time},{v1_id},{v2_id},{ttc:.2f},{distance:.2f},{severity}\n")