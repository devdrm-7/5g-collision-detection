import math
import time
import random
import os
from utils import calculate_distance

class VanetNetwork:
    def __init__(self, transmission_range=100.0, packet_loss_rate=0.05):
        """
        Initialize VANET network simulation
        
        Args:
            transmission_range: Maximum communication range between vehicles in meters
            packet_loss_rate: Probability of packet loss in wireless transmission
        """
        self.transmission_range = transmission_range
        self.packet_loss_rate = packet_loss_rate
        self.log_file = "data/communication_log.txt"
        self.step = 0
        self.step_length = 0.1  # Default SUMO step length in seconds
        
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Initialize log file - UPDATED to include severity and distance
        with open(self.log_file, 'w') as f:
            f.write("Timestamp,Sender,Receiver,MessageType,Severity,Distance,Success\n")
    
    def send_warnings(self, vehicles_data, collision_pairs):
        """
        Simulate warning message dissemination in VANET
        
        Args:
            vehicles_data: Dictionary with vehicle information
            collision_pairs: List of tuples (v1, v2, ttc) with potential collisions
        """
        self.step += 1
        
        # Calculate simulation time from step number
        elapsed_time = self.step * self.step_length
        formatted_time = f"{int(elapsed_time/60):02d}:{int(elapsed_time%60):02d}.{int((elapsed_time%1)*10):01d}"
        
        for v1_id, v2_id, ttc in collision_pairs:
            # Calculate distance between vehicles
            distance = calculate_distance(vehicles_data[v1_id]['position'], vehicles_data[v2_id]['position'])
            
            # Determine severity based on TTC and relative speed
            rel_speed = abs(vehicles_data[v1_id]['speed'] - vehicles_data[v2_id]['speed'])
            if ttc < 1.0:
                if rel_speed > 10.0:
                    severity = "CRITICAL"
                else:
                    severity = "HIGH"
            elif ttc < 2.0:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            
            # Direct communication between the two vehicles that may collide
            self._send_message(vehicles_data, formatted_time, v1_id, v2_id, "COLLISION_WARNING", severity, distance)
            self._send_message(vehicles_data, formatted_time, v2_id, v1_id, "COLLISION_WARNING", severity, distance)
            
            # Multi-hop dissemination to nearby vehicles
            for v3_id in vehicles_data:
                if v3_id != v1_id and v3_id != v2_id:
                    # Calculate distance for the nearby vehicle
                    v3_to_v1_distance = calculate_distance(vehicles_data[v3_id]['position'], vehicles_data[v1_id]['position'])
                    v3_to_v2_distance = calculate_distance(vehicles_data[v3_id]['position'], vehicles_data[v2_id]['position'])
                    
                    # Vehicle 3 can relay warnings if it's connected to either v1 or v2
                    if self._can_communicate(vehicles_data, v1_id, v3_id):
                        self._send_message(vehicles_data, formatted_time, v1_id, v3_id, "NEARBY_COLLISION", severity, v3_to_v1_distance)
                    
                    if self._can_communicate(vehicles_data, v2_id, v3_id):
                        self._send_message(vehicles_data, formatted_time, v2_id, v3_id, "NEARBY_COLLISION", severity, v3_to_v2_distance)
    
    def _can_communicate(self, vehicles_data, v1_id, v2_id):
        """Check if two vehicles can communicate based on distance"""
        if v1_id not in vehicles_data or v2_id not in vehicles_data:
            return False
            
        v1_pos = vehicles_data[v1_id]['position']
        v2_pos = vehicles_data[v2_id]['position']
        
        distance = calculate_distance(v1_pos, v2_pos)
        
        return distance <= self.transmission_range
    
    def _send_message(self, vehicles_data, timestamp, sender_id, receiver_id, message_type, severity, distance):
        """Simulate sending a message between vehicles with severity and distance info"""
        # Check if communication is possible
        if not self._can_communicate(vehicles_data, sender_id, receiver_id):
            return False
        
        # Simulate packet loss
        success = random.random() > self.packet_loss_rate
        
        # Log communication with severity and distance
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp},{sender_id},{receiver_id},{message_type},{severity},{distance:.2f},{success}\n")
        
        return success