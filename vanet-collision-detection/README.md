# VANET Collision Detection System

This project implements a collision detection system using Vehicle Ad-hoc Networks (VANETs) in Python. The system utilizes SUMO for traffic simulation and ns-3 for network simulation to detect potential collisions between vehicles based on their positions and velocities.

## Project Structure

```
vanet-collision-detection
├── src
│   ├── main.py
│   ├── collision_detection.py
│   ├── vanet_communication.py
│   └── utils.py
├── simulation
│   ├── sumo_config.sumocfg
│   ├── map.net.xml
│   └── routes.rou.xml
├── data
│   └── README.md
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Install the required software:**
   - Ensure you have SUMO and ns-3 installed on your system.
   - Install Python and pip if not already installed.

2. **Set up the Python environment:**
   - Create a virtual environment (optional but recommended).
   - Install the required Python packages using the command:
     ```
     pip install -r requirements.txt
     ```

3. **Configure the SUMO simulation:**
   - Edit the `simulation/sumo_config.sumocfg` file to adjust simulation parameters as needed.

4. **Run the simulation:**
   - Execute the main script using the command:
     ```
     python src/main.py
     ```

5. **Monitor the output for collision detection results and any logged data.**

## Overview of Components

- **src/main.py**: Entry point of the application that initializes the simulation environment and starts the collision detection system.
- **src/collision_detection.py**: Contains the `CollisionDetection` class for detecting potential collisions.
- **src/vanet_communication.py**: Handles communication between vehicles using VANET protocols.
- **src/utils.py**: Utility functions for data processing and logging.
- **simulation/**: Contains configuration files for the SUMO simulation.
- **data/**: Directory for additional datasets or resources.

## Acknowledgments

This project utilizes SUMO and ns-3 for traffic and network simulation, respectively. Special thanks to the developers of these tools for their contributions to the field of transportation and network simulation.