# Two-VM Deployment Guide: Linux Backend + Windows Frontend

This guide sets up your MODBUS TCP engine simulation across two VMs on the same subnet.

## Architecture Overview

```
┌─────────────────┐    MODBUS TCP    ┌─────────────────┐    REST API     ┌─────────────────┐
│   Linux VM      │ ────────────────► │  Windows VM     │ ───────────────► │  React Frontend │
│  (Backend)      │   Port 502       │  (Bridge)       │   Port 8000     │  (Browser)      │
│                 │                  │                 │                  │                 │
│ standalone_     │                  │ modbus_bridge   │                  │ localhost:3000  │
│ backend.py      │                  │ .py             │                  │                 │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
```

## Network Configuration

### VM Network Setup
- **Linux VM IP**: `192.168.1.100`
- **Windows VM IP**: `192.168.1.101`
- **Subnet**: `192.168.1.0/24`
- **Gateway**: `192.168.1.1`

### Required Ports
- **Port 502**: MODBUS TCP (Linux VM)
- **Port 8000**: REST API (Windows VM)
- **Port 3000**: React Development Server (Windows VM)

## Step 1: Linux VM Setup (Backend)

### 1.1 Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install required packages
sudo apt install git -y
```

### 1.2 Setup Project
```bash
# Clone or copy project to Linux VM
cd /home/user/
git clone <your-repo-url> me-sim
cd me-sim

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 1.3 Configure Backend
```bash
# Create config file for Linux VM
cat > config_linux.yaml << 'EOF'
modbus:
  host: "0.0.0.0"  # Listen on all interfaces
  port: 502

engine:
  rpm_min: 600
  rpm_max: 1200
  rpm_normal: 900
  temp_min: 70
  temp_max: 120
  temp_normal: 85
  fuel_flow_min: 0.5
  fuel_flow_max: 2.5
  fuel_flow_normal: 1.5
  update_interval: 1.0

registers:
  status: 0
  rpm: 1
  temp: 2
  fuel_flow: 3
  load: 4
EOF
```

### 1.4 Start Backend Service
```bash
# Activate virtual environment
source venv/bin/activate

# Start MODBUS TCP server
python standalone_backend.py --config config_linux.yaml --host 0.0.0.0 --port 502

# Expected output:
# ✓ MODBUS TCP Server started successfully
#   Host: 0.0.0.0
#   Port: 502
```

### 1.5 Verify Backend
```bash
# Test MODBUS connection (from Linux VM)
python -c "
from pyModbusTCP.client import ModbusClient
client = ModbusClient(host='192.168.1.100', port=502)
if client.open():
    print('✓ MODBUS server is running')
    client.close()
else:
    print('✗ MODBUS server not accessible')
"
```

## Step 2: Windows VM Setup (Frontend)

### 2.1 Install Dependencies
```powershell
# Install Node.js (if not already installed)
# Download from https://nodejs.org/

# Install Python
# Download from https://www.python.org/downloads/
```

### 2.2 Setup Project
```powershell
# Clone or copy project to Windows VM
cd C:\Users\YourUser\Desktop\
git clone <your-repo-url> me-sim
cd me-sim

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2.3 Configure Bridge Service
```powershell
# Create config file for Windows VM
@"
modbus:
  host: "192.168.1.100"  # Linux VM IP
  port: 502

registers:
  status: 0
  rpm: 1
  temp: 2
  fuel_flow: 3
  load: 4
"@ | Out-File -FilePath "config_windows.yaml" -Encoding UTF8
```

### 2.4 Start Bridge Service
```powershell
# Activate virtual environment
venv\Scripts\activate

# Start bridge service
python modbus_bridge.py --modbus-host 192.168.1.100 --modbus-port 502

# Expected output:
# 🌐 Bridge will connect via NETWORK IP: 192.168.1.100:502
# 📡 This ensures MODBUS traffic is visible in Wireshark!
```

### 2.5 Setup Frontend
```powershell
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start React development server
npm start

# Expected output:
# Local:            http://localhost:3000
# On Your Network:  http://192.168.1.101:3000
```

## Step 3: Network Testing

### 3.1 Test Network Connectivity
```powershell
# From Windows VM, test connection to Linux VM
ping 192.168.1.100

# Test MODBUS port
Test-NetConnection -ComputerName 192.168.1.100 -Port 502
```

### 3.2 Test Bridge Service
```powershell
# Test REST API endpoint
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET

# Expected response:
# {
#   "status": "healthy",
#   "modbus": "connected",
#   "target": "192.168.1.100:502"
# }
```

### 3.3 Test Frontend
1. Open browser on Windows VM
2. Navigate to `http://localhost:3000`
3. Verify data is being displayed from MODBUS backend

## Step 4: Monitoring and Troubleshooting

### 4.1 Monitor MODBUS Traffic
```bash
# On Linux VM - Monitor MODBUS packets
sudo tcpdump -i any port 502 -vv

# On Windows VM - Use Wireshark
# Filter: tcp.port == 502
```

### 4.2 Monitor REST API Traffic
```powershell
# On Windows VM - Monitor API calls
netstat -an | findstr :8000
```

### 4.3 Common Issues

#### Issue: MODBUS Connection Failed
```bash
# Check if MODBUS server is running on Linux VM
sudo netstat -tlnp | grep :502

# Check firewall on Linux VM
sudo ufw status
sudo ufw allow 502/tcp
```

#### Issue: Bridge Cannot Connect
```powershell
# Check if bridge can reach Linux VM
Test-NetConnection -ComputerName 192.168.1.100 -Port 502

# Check bridge logs
python modbus_bridge.py --modbus-host 192.168.1.100 --modbus-port 502 --verbose
```

#### Issue: Frontend Not Loading Data
```powershell
# Check if bridge service is running
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET

# Check browser console for errors
# Press F12 in browser and check Console tab
```

## Step 5: Security Considerations

### 5.1 Firewall Configuration
```bash
# Linux VM - Allow MODBUS traffic
sudo ufw allow 502/tcp
sudo ufw enable

# Windows VM - Allow REST API traffic
netsh advfirewall firewall add rule name="REST API" dir=in action=allow protocol=TCP localport=8000
```

### 5.2 Network Isolation
- Ensure both VMs are on the same subnet
- Consider using a dedicated network for this setup
- Monitor traffic for unauthorized access attempts

## Step 6: Automation Scripts

### 6.1 Linux VM Startup Script
```bash
# Create startup script
cat > start_backend.sh << 'EOF'
#!/bin/bash
cd /home/user/me-sim
source venv/bin/activate
python standalone_backend.py --config config_linux.yaml --host 0.0.0.0 --port 502
EOF

chmod +x start_backend.sh
```

### 6.2 Windows VM Startup Script
```powershell
# Create startup script
@"
cd C:\Users\YourUser\Desktop\me-sim
venv\Scripts\activate
python modbus_bridge.py --modbus-host 192.168.1.100 --modbus-port 502
"@ | Out-File -FilePath "start_bridge.ps1" -Encoding UTF8
```

## Verification Checklist

- [ ] Linux VM MODBUS server running on port 502
- [ ] Windows VM bridge service running on port 8000
- [ ] Frontend accessible on port 3000
- [ ] Network connectivity between VMs
- [ ] MODBUS data flowing from Linux to Windows
- [ ] Frontend displaying real-time data
- [ ] All services restart properly after reboot

## Performance Monitoring

### Monitor MODBUS Performance
```bash
# On Linux VM
watch -n 1 'netstat -an | grep :502 | wc -l'
```

### Monitor Bridge Performance
```powershell
# On Windows VM
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

This setup provides a complete distributed MODBUS TCP simulation environment with real network traffic visible for monitoring and analysis. 