# All-in-One Main Engine (ME) Simulator

A comprehensive Main Engine simulator that combines engine simulation, PLC control, and HMI into a single application. This simulator provides a realistic environment for testing and training purposes.

## Features

- **Engine Simulation**
  - Realistic parameter simulation (RPM, temperature, fuel flow)
  - Modbus TCP/IP server for external connectivity
  - Configurable engine parameters
  - Real-time parameter updates

- **PLC Control**
  - Automatic and manual control modes
  - Safety monitoring and alarms
  - Setpoint control
  - Emergency shutdown logic

- **Web-based HMI**
  - Real-time parameter display
  - Trend graphs
  - Control interface
  - Alarm monitoring
  - Responsive design using Material-UI

## Requirements

- Python 3.8+
- Node.js 14+
- npm or yarn

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourrepo/me-sim.git
cd me-sim
```

2. Create and activate Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
cd ..
```

## Configuration

The simulation parameters can be configured in `config.yaml`. Key parameters include:
- Modbus server settings
- Engine parameters ranges
- Update intervals
- Register mappings

## Usage

### Local Usage (Single Machine)

1. Start the backend server:
```bash
python app.py
```

2. In a new terminal, start the frontend development server:
```bash
cd frontend
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

### Remote Access (Multiple Machines)

To run the simulator on one machine and access it from another:

#### Quick Start (Easiest)

Run the all-in-one script that configures IP and starts both servers:
```bash
python start_remote.py
```

This script will:
1. Automatically detect and configure the correct IP address
2. Start the backend server
3. Start the frontend server
4. Display access URLs for local and remote connections

#### Manual Configuration Steps

1. On the machine that will host the simulator, run the IP configuration helper:
```bash
python configure_ip.py
```

2. Follow the prompts to configure the correct IP address

3. Start the backend and frontend as usual:
```bash
# Terminal 1: Start backend
python app.py

# Terminal 2: Start frontend  
cd frontend
npm start
```

4. From other machines, access the simulator at:
   - Frontend: `http://[HOST_IP]:3000`
   - The frontend will automatically connect to the backend

#### Manual Configuration

1. Edit `remote_settings.json` and update the IP addresses:
```json
{
  "websocketUrl": "ws://YOUR_IP_ADDRESS:8000/ws",
  "modbusHost": "YOUR_IP_ADDRESS",
  ...
}
```

2. Copy the settings to the frontend:
```bash
copy remote_settings.json frontend\public\remote_settings.json
```

3. Start both backend and frontend servers

#### Firewall Configuration

Make sure the following ports are open on the host machine:
- **Port 8000**: Backend WebSocket and API server
- **Port 3000**: Frontend development server
- **Port 502**: Modbus TCP server (if using external Modbus clients)

#### Troubleshooting Remote Access

- **"Start Engine" button doesn't work**: Usually indicates WebSocket connection failure
- **Connection lost alerts**: Check firewall settings and network connectivity
- **Frontend loads but no data**: Verify backend is running and ports are accessible
- **Engine starts but RPM doesn't change**: Simulation loop issue

**Diagnostic Steps:**

1. **Debug Startup** (recommended first step):
   ```bash
   python debug_start.py
   ```
   This starts the backend with enhanced debugging and shows exactly what's happening.

2. **Test Backend Only** (isolate the issue):
   ```bash
   python test_backend.py
   ```
   This will test the backend simulation without the frontend.

3. **Check Browser Console** (F12 → Console) for WebSocket errors

4. **Look for Debug Messages** in backend output:
   - `✓ Simulation loop started successfully!` - Loop initialization
   - `[SIM] Loop X: Running=True, RPM=XXX` - Simulation running
   - `[BROADCAST] Sending to X clients` - Data being sent to frontend

5. **Verify Network Connectivity**:
   ```bash
   # Test if backend is reachable
   curl http://[HOST_IP]:8000/api/status
   ```

**Common Issues and Solutions:**

- **Simulation loop not starting**: The debug startup will show if this is the issue
- **Parameters not updating**: Look for `[SIM] Engine starting` messages
- **Frontend not receiving data**: Check for `[BROADCAST]` messages
- **WebSocket connection fails**: Usually firewall or network configuration

## Components

### Engine Simulator
- Simulates main engine behavior
- Exposes parameters via Modbus TCP
- Handles start/stop sequences
- Manages engine states

### PLC Controller
- Monitors engine parameters
- Implements safety logic
- Handles automatic control
- Manages alarms and shutdowns

### HMI Interface
- Real-time parameter display
- Interactive controls
- Trend visualization
- Alarm management

## Modbus Register Map

| Register | Parameter | Type | Scale |
|----------|-----------|------|--------|
| 0 | Engine RPM | INT | 1 |
| 1 | Temperature | INT | 1 |
| 2 | Fuel Flow | INT | x100 |
| 3 | Engine Load | INT | 1 |
| 4 | Status | INT | - |

## License

MIT License 