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