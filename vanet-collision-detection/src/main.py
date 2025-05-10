import os
import sys
import traci
import argparse
import math
import threading
import queue
import time
import tkinter as tk
from tkinter import ttk
from collision_detection import CollisionDetector
from vanet_communication import VanetNetwork
from utils import calculate_distance

# Set SUMO_HOME environment variable if not set
if 'SUMO_HOME' not in os.environ:
    os.environ['SUMO_HOME'] = r'C:\Users\Devraj Meena\Desktop\MinorProject'

# Add SUMO tools to Python path
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

def create_demo_window():
    """Create a demonstration window showing collision information"""
    # Queue for thread-safe communication
    collision_queue = queue.Queue()
    
    # Create window in a separate thread to not block simulation
    def run_window():
        root = tk.Tk()
        root.title("VANET Collision Detection Demo")
        root.geometry("700x500")
        
        # Create a frame for collision information
        frame = ttk.Frame(root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a label
        ttk.Label(frame, text="Live Collision Detection", font=("Arial", 16)).pack(pady=10)
        
        # Create a treeview for collision data
        cols = ("Time", "Vehicle 1", "Vehicle 2", "Time to Collision", "Severity")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add a status label
        status_var = tk.StringVar()
        status_var.set("Simulation running...")
        status = ttk.Label(frame, textvariable=status_var)
        status.pack(pady=5)
        
        # Function to check queue and update UI
        def check_queue():
            try:
                while True:  # Process all available items
                    item = collision_queue.get_nowait()
                    if item == "END":
                        status_var.set("Simulation completed")
                        return
                    
                    # Add new collision to tree
                    sim_time, v1, v2, ttc, severity = item
                    tree.insert("", 0, values=(sim_time, v1, v2, f"{ttc:.2f}s", severity))
                    status_var.set(f"Latest collision risk: {v1} and {v2} in {ttc:.2f}s")
                    
                    # Keep only the last 100 entries to avoid slowdown
                    if len(tree.get_children()) > 100:
                        tree.delete(tree.get_children()[-1])
            except queue.Empty:
                pass
            finally:
                # Schedule next check
                root.after(100, check_queue)
        
        # Start queue checking
        check_queue()
        
        root.mainloop()
    
    # Start the window in a separate thread
    thread = threading.Thread(target=run_window)
    thread.daemon = True
    thread.start()
    
    return collision_queue

def run_simulation(use_gui=False):
    # Track simulation time
    simulation_start_time = time.time()
    step_length = 0.1  # Default SUMO step length in seconds (check your config)
    
    # Initialize collision detector with simulation start time
    detector = CollisionDetector(time_threshold=3.0, distance_threshold=30.0, 
                               simulation_start_time=simulation_start_time)
    vanet = VanetNetwork(transmission_range=100.0)
    
    # Create the demo window and get the queue for sending collision data
    collision_queue = create_demo_window()
    
    # Start SUMO
    sumo_binary = "sumo-gui" if use_gui else "sumo"
    sumo_cmd = [os.path.join(os.environ['SUMO_HOME'], 'bin', sumo_binary), 
                "-c", "simulation/sumo_config.sumocfg"]
    traci.start(sumo_cmd)
    
    # Show vehicle IDs in the GUI (Approach 1) - CORRECTED
    if use_gui:
        print("Configuring GUI to show vehicle IDs...")
        try:
            traci.gui.setSchema("View #0", "real world")
            traci.gui.setBoundary("View #0", 0, 0, 500, 500)  # Adjust based on your network size
            traci.gui.setShowVehicleNames("View #0", True)  # Show vehicle IDs above vehicles
        except Exception as e:
            print(f"Warning: Could not configure GUI completely: {e}")
    
    step = 0
    collision_count = 0
    
    print("Starting VANET collision detection simulation")
    print("=============================================")
    
    # Main simulation loop
    while step < 1000:  # Run for 1000 steps or until all vehicles finish
        traci.simulationStep()
        
        # Get all vehicles in the simulation
        vehicle_ids = traci.vehicle.getIDList()
        if not vehicle_ids:
            print("No vehicles in simulation, skipping step")
            step += 1
            continue
        
        # Reset all vehicle colors to default (Approach 2)
        if use_gui:
            for vehicle_id in vehicle_ids:
                traci.vehicle.setColor(vehicle_id, (255, 255, 255, 255))  # White/default
        
        # Collect vehicle data
        vehicles_data = {}
        for vehicle_id in vehicle_ids:
            position = traci.vehicle.getPosition(vehicle_id)
            speed = traci.vehicle.getSpeed(vehicle_id)
            angle = traci.vehicle.getAngle(vehicle_id)
            length = traci.vehicle.getLength(vehicle_id)
            width = traci.vehicle.getWidth(vehicle_id)
            
            vehicles_data[vehicle_id] = {
                'position': position,
                'speed': speed,
                'angle': angle,
                'length': length,
                'width': width
            }
        
        # Detect potential collisions
        collision_pairs = detector.detect_collisions(vehicles_data)
        
        # Highlight colliding vehicles (Approach 2)
        if use_gui and collision_pairs:
            for v1, v2, ttc in collision_pairs:
                # Highlight colliding vehicles in red (more severe) or yellow (less severe)
                if ttc < 1.5:  # Imminent collision
                    traci.vehicle.setColor(v1, (255, 0, 0, 255))  # Bright red
                    traci.vehicle.setColor(v2, (255, 0, 0, 255))  # Bright red
                else:  # Potential collision
                    traci.vehicle.setColor(v1, (255, 204, 0, 255))  # Yellow
                    traci.vehicle.setColor(v2, (255, 204, 0, 255))  # Yellow
                
                # Log to console
                message = f"Collision risk: {v1} and {v2} in {ttc:.1f}s"
                print(message)
        
        # Update demo window (Approach 3)
        if collision_pairs:
            collision_count += len(collision_pairs)
            vanet.send_warnings(vehicles_data, collision_pairs)
            
            # Calculate elapsed simulation time
            elapsed_time = step * step_length
            formatted_time = f"{int(elapsed_time/60):02d}:{int(elapsed_time%60):02d}.{int((elapsed_time%1)*10):01d}"
            
            # Send collision data to demo window with actual time
            for v1, v2, ttc in collision_pairs:
                severity = detector._calculate_severity(ttc, 
                                                    calculate_distance(vehicles_data[v1]['position'], 
                                                                    vehicles_data[v2]['position']),
                                                    vehicles_data[v1]['speed'],
                                                    vehicles_data[v2]['speed'])
                # Add to demo window queue with formatted time
                collision_queue.put((formatted_time, v1, v2, ttc, severity))
            
            # Log collisions to console with formatted time
            for v1, v2, ttc in collision_pairs:
                print(f"[Time {formatted_time}] WARNING: Potential collision between {v1} and {v2} in {ttc:.2f} seconds!")
        
        step += 1
    
    # Signal the demo window that simulation is complete
    collision_queue.put("END")
    
    print("=============================================")
    print(f"Simulation completed. Detected {collision_count} potential collisions.")
    print(f"Total simulation time: {step * step_length:.2f} seconds")
    traci.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run VANET collision detection simulation")
    parser.add_argument("--gui", action="store_true", help="Run with SUMO GUI")
    args = parser.parse_args()
    
    run_simulation(use_gui=args.gui)