# MODBUS Engine Simulator - Two VM Deployment

This project simulates an industrial engine monitoring system using MODBUS TCP communication between a Linux backend and Windows frontend.

## Architecture

- **Backend (Linux VM)**: `192.168.20.192` - MODBUS TCP Server
- **Frontend (Windows VM)**: `192.168.20.100` - React Web Interface + Bridge Service

## Network Configuration

- **Backend MODBUS Server**: `192.168.20.192:502`
- **Bridge Service**: `192.168.20.100:8000`
- **Frontend Web App**: `192.168.20.100:3000`

## Deployment Instructions

### Linux Backend (192.168.20.192)

1. **Copy files to Linux VM:**
   ```bash
   # Copy these files to Linux VM:
   - standalone_backend.py
   - config_linux.yaml
   - requirements.txt
   - start_linux_backend.sh
   ```

2. **Make script executable:**
   ```bash
   chmod +x start_linux_backend.sh
   ```

3. **Run the backend:**
   ```bash
   ./start_linux_backend.sh
   ```

   Or manually:
   ```bash
   python3 standalone_backend.py --host 0.0.0.0 --port 502
   ```

### Windows Frontend (192.168.20.100)

1. **Copy files to Windows VM:**
   ```bash
   # Copy these files to Windows VM:
   - modbus_bridge.py
   - frontend/ (entire folder)
   - requirements.txt
   - start_windows_frontend.ps1
   - start_windows_frontend.bat
   ```

2. **Run the frontend:**
   
   **Option 1: PowerShell Script**
   ```powershell
   .\start_windows_frontend.ps1
   ```
   
   **Option 2: Batch File**
   ```cmd
   start_windows_frontend.bat
   ```

## What Each Component Does

### Backend (Linux)
- Runs MODBUS TCP server on port 502
- Simulates engine parameters (RPM, temperature, fuel flow, load)
- Continuously sends MODBUS packets with current engine data
- Listens on all interfaces (0.0.0.0) to accept connections from Windows VM

### Bridge Service (Windows)
- Connects to Linux backend via MODBUS TCP
- Provides REST API for the frontend
- Translates MODBUS data to JSON format
- Runs on port 8000

### Frontend (Windows)
- React web application
- Displays real-time engine data
- Sends start/stop commands to engine
- Connects to bridge service via REST API
- Runs on port 3000

## Network Traffic

- **MODBUS TCP**: `192.168.20.100:8000` ↔ `192.168.20.192:502`
- **REST API**: `192.168.20.100:3000` ↔ `192.168.20.100:8000`

## Monitoring with Wireshark

Use these filters to monitor network traffic:

- **MODBUS Traffic**: `tcp.port == 502`
- **REST API Traffic**: `tcp.port == 8000`
- **All Traffic Between VMs**: `ip.addr == 192.168.20.192 and ip.addr == 192.168.20.100`

## Troubleshooting

### Backend Issues
- Ensure Linux VM has IP `192.168.20.192`
- Check firewall allows port 502
- Verify Python dependencies are installed

### Frontend Issues
- Ensure Windows VM has IP `192.168.20.100`
- Check firewall allows ports 3000 and 8000
- Verify Node.js and Python are installed
- Check bridge service is running before starting frontend

### Network Issues
- Ping between VMs: `ping 192.168.20.192` (from Windows)
- Test MODBUS connection: `telnet 192.168.20.192 502`
- Check network connectivity between VMs
