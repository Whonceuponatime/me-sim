# MODBUS Engine Simulator - Two VM Deployment

This project simulates an industrial engine monitoring system using MODBUS TCP communication between a Linux backend and Windows frontend.

## Architecture

- **Backend (Linux VM)**: `192.168.20.192` - MODBUS TCP Server + HTTP API
- **Frontend (Windows VM)**: `192.168.20.100` - React Web Interface

## Network Configuration

- **Backend MODBUS Server**: `192.168.20.192:502`
- **Backend HTTP API**: `192.168.20.192:8080`
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
   - frontend/ (entire folder)
   - start_frontend.bat
   ```

2. **Run the frontend:**
   ```cmd
   start_frontend.bat
   ```

## What Each Component Does

### Backend (Linux)
- Runs MODBUS TCP server on port 502
- Runs HTTP API server on port 8080
- Simulates engine parameters (RPM, temperature, fuel flow, load)
- Continuously sends MODBUS packets with current engine data
- Serves engine data via HTTP API for frontend
- Listens on all interfaces (0.0.0.0) to accept connections from Windows VM

### Frontend (Windows)
- React web application
- Displays real-time engine data
- Connects to backend HTTP API for data
- Runs on port 3000

## Network Traffic

- **MODBUS TCP**: Available on `192.168.20.192:502` (for external MODBUS clients)
- **HTTP API**: `192.168.20.100:3000` ↔ `192.168.20.192:8080`

## Monitoring with Wireshark

Use these filters to monitor network traffic:

- **MODBUS Traffic**: `tcp.port == 502`
- **HTTP API Traffic**: `tcp.port == 8080`
- **All Traffic Between VMs**: `ip.addr == 192.168.20.192 and ip.addr == 192.168.20.100`

## Troubleshooting

### Backend Issues
- Ensure Linux VM has IP `192.168.20.192`
- Check firewall allows ports 502 and 8080
- Verify Python dependencies are installed

### Frontend Issues
- Ensure Windows VM has IP `192.168.20.100`
- Check firewall allows port 3000
- Verify Node.js is installed
- Check backend HTTP API is running (http://192.168.20.192:8080/api/engine)

### Network Issues
- Ping between VMs: `ping 192.168.20.192` (from Windows)
- Test MODBUS connection: `telnet 192.168.20.192 502`
- Check network connectivity between VMs
