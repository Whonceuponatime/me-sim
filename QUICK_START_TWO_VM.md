# Quick Start: Two-VM Setup

## Overview
- **Linux VM**: Runs MODBUS TCP server (port 502)
- **Windows VM**: Runs bridge service (port 8000) + React frontend (port 3000)

## Network Setup
- **Linux VM IP**: `192.168.1.100`
- **Windows VM IP**: `192.168.1.101`
- **Subnet**: `192.168.1.0/24`

## Step 1: Linux VM (Backend)

### 1.1 Install Dependencies
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

### 1.2 Setup Project
```bash
cd /home/user/
git clone <your-repo> me-sim
cd me-sim

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1.3 Start Backend
```bash
# Make script executable (on Linux)
chmod +x start_linux_backend.sh

# Run the startup script
./start_linux_backend.sh

# Or manually:
source venv/bin/activate
python standalone_backend.py --config config_linux.yaml --host 0.0.0.0 --port 502
```

**Expected Output:**
```
✓ MODBUS TCP Server started successfully
  Host: 0.0.0.0
  Port: 502
```

## Step 2: Windows VM (Frontend)

### 2.1 Install Dependencies
- Install Node.js from https://nodejs.org/
- Install Python from https://www.python.org/downloads/

### 2.2 Setup Project
```powershell
cd C:\Users\YourUser\Desktop\
git clone <your-repo> me-sim
cd me-sim

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2.3 Start Frontend
```powershell
# Run the PowerShell script
.\start_windows_frontend.ps1

# Or manually:
# Terminal 1 - Bridge Service
venv\Scripts\activate
python modbus_bridge.py --modbus-host 192.168.1.100 --modbus-port 502

# Terminal 2 - Frontend
cd frontend
npm install
npm start
```

## Step 3: Verify Setup

### 3.1 Test Network Connectivity
```powershell
# From Windows VM
ping 192.168.1.100
Test-NetConnection -ComputerName 192.168.1.100 -Port 502
```

### 3.2 Test Services
```powershell
# Test bridge service
Invoke-RestMethod -Uri "http://localhost:8000/api/health"

# Expected response:
# {
#   "status": "healthy",
#   "modbus": "connected",
#   "target": "192.168.1.100:502"
# }
```

### 3.3 Access Frontend
1. Open browser on Windows VM
2. Navigate to `http://localhost:3000`
3. Verify real-time engine data is displayed

## Troubleshooting

### Issue: MODBUS Connection Failed
```bash
# On Linux VM
sudo netstat -tlnp | grep :502
sudo ufw allow 502/tcp
```

### Issue: Bridge Cannot Connect
```powershell
# On Windows VM
Test-NetConnection -ComputerName 192.168.1.100 -Port 502
```

### Issue: Frontend Not Loading
```powershell
# Check bridge service
Invoke-RestMethod -Uri "http://localhost:8000/api/health"

# Check browser console (F12)
```

## Monitoring

### Monitor MODBUS Traffic
```bash
# On Linux VM
sudo tcpdump -i any port 502 -vv
```

### Monitor REST API
```powershell
# On Windows VM
netstat -an | findstr :8000
```

## Services Summary

| Service | VM | Port | URL |
|---------|----|----|-----|
| MODBUS TCP Server | Linux | 502 | `192.168.1.100:502` |
| Bridge Service | Windows | 8000 | `http://localhost:8000` |
| React Frontend | Windows | 3000 | `http://localhost:3000` |

## Files Created
- `config_linux.yaml` - Linux VM backend configuration
- `start_linux_backend.sh` - Linux VM startup script
- `start_windows_frontend.ps1` - Windows VM startup script
- `TWO_VM_DEPLOYMENT_GUIDE.md` - Detailed deployment guide
- Updated `frontend/public/remote_settings.json` - Frontend configuration

Your two-VM setup is now ready! The Linux VM will serve MODBUS TCP data, and the Windows VM will display it through a web interface. 