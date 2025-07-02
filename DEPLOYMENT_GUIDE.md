# Multi-Machine Engine Simulator Deployment Guide

This guide explains how to deploy the engine simulator across multiple machines with real MODBUS TCP communication.

## Architecture Overview

The system is now separated into:
- **Linux VM Backend**: Standalone MODBUS TCP server (`standalone_backend.py`)
- **Frontend Machine**: React frontend connecting to remote backend
- **Attack Machine**: Vulnerability demonstration tools

## Prerequisites

### Linux VM (Backend)
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.8+
- Root access (for port 502) or use alternative port 5020
- Network connectivity to frontend machine

### Frontend Machine (Windows/Linux/Mac)
- Node.js 14+
- Network connectivity to backend VM

### Attack Machine (Any OS)
- Python 3.8+
- pyModbusTCP library
- Network connectivity to backend VM

## Deployment Steps

### Step 1: Deploy Backend on Linux VM

#### Option A: Automated Deployment (Recommended)

1. **Transfer files to Linux VM:**
```bash
# Copy these files to your Linux VM:
# - standalone_backend.py
# - config_linux.yaml
# - deploy_backend.sh
# - requirements.txt
# - engine/, plc/, sensors/ directories
```

2. **Make deployment script executable:**
```bash
chmod +x deploy_backend.sh
```

3. **Run deployment script:**
```bash
# For standard port 502 (requires root):
sudo ./deploy_backend.sh

# For alternative port 5020 (no root required):
./deploy_backend.sh --port=5020
```

4. **Start the service:**
```bash
sudo systemctl start engine-simulator
sudo systemctl status engine-simulator
```

#### Option B: Manual Deployment

1. **Install Python dependencies:**
```bash
python3 -m venv venv_backend
source venv_backend/bin/activate
pip install -r requirements.txt
```

2. **Test the backend:**
```bash
python standalone_backend.py --host 0.0.0.0 --port 502
```

3. **Configure firewall:**
```bash
sudo ufw allow 502/tcp
# Or for alternative port:
sudo ufw allow 5020/tcp
```

#### Option C: Docker Deployment

1. **Build and run with Docker:**
```bash
# Build the container
docker build -f Dockerfile.backend -t engine-simulator .

# Run with Docker Compose
docker-compose -f docker-compose.backend.yml up -d
```

2. **Check container status:**
```bash
docker-compose -f docker-compose.backend.yml ps
docker-compose -f docker-compose.backend.yml logs
```

### Step 2: Configure Frontend for Remote Connection

1. **Get the Linux VM IP address:**
```bash
# On the Linux VM, run:
hostname -I
# Example output: 192.168.1.100
```

2. **Create frontend configuration:**
```bash
# Copy the template and update IP addresses
cp frontend/public/remote_settings_template.json frontend/public/remote_settings.json
```

3. **Edit `frontend/public/remote_settings.json`:**
```json
{
  "websocketUrl": "ws://192.168.1.100:8000/ws",
  "modbusHost": "192.168.1.100",
  "modbusPort": 502,
  "deployment": {
    "mode": "remote",
    "backendType": "modbus_only"
  }
}
```

4. **Install and run frontend:**
```bash
cd frontend
npm install
npm start
```

### Step 3: Test MODBUS Connectivity

1. **From any machine with network access to the backend:**
```bash
# Test basic connectivity
python demonstrate_vulnerability_remote.py 192.168.1.100 --scan-only

# Read engine registers
python demonstrate_vulnerability_remote.py 192.168.1.100 --read-only

# Demonstrate stop attack
python demonstrate_vulnerability_remote.py 192.168.1.100 --stop-only

# Full vulnerability assessment
python demonstrate_vulnerability_remote.py 192.168.1.100 --full
```

## Network Configuration

### Firewall Rules

**Linux VM (Backend):**
```bash
# Allow MODBUS TCP
sudo ufw allow 502/tcp
sudo ufw allow 5020/tcp  # Alternative port

# Check firewall status
sudo ufw status
```

**Frontend Machine:**
- No special firewall configuration needed (outbound connections only)

### Port Configuration

| Service | Default Port | Alternative | Purpose |
|---------|-------------|-------------|---------|
| MODBUS TCP | 502 | 5020 | Engine control data |
| WebSocket | 8000 | N/A | Real-time frontend updates (if available) |

## Security Considerations

⚠️ **WARNING: This setup demonstrates security vulnerabilities intentionally**

### Demonstrated Vulnerabilities:
1. **No Authentication**: Anyone can connect to MODBUS server
2. **No Encryption**: All data transmitted in plain text
3. **No Authorization**: No access control for critical commands
4. **No Auditing**: Limited logging of security events
5. **Network Exposure**: Server accessible from any IP

### For Production Use:
1. Use VPN tunnels for remote access
2. Implement MODBUS security extensions
3. Add authentication layers
4. Enable comprehensive logging
5. Use network segmentation
6. Regular security audits

## Troubleshooting

### Backend Issues

**Service won't start:**
```bash
# Check service status
sudo systemctl status engine-simulator

# View logs
sudo journalctl -u engine-simulator -f

# Check if port is in use
sudo netstat -tlnp | grep 502
```

**Permission denied on port 502:**
```bash
# Use alternative port
python standalone_backend.py --port 5020

# Or run with sudo
sudo python standalone_backend.py --port 502
```

**Network connectivity issues:**
```bash
# Test from another machine
nc -zv 192.168.1.100 502

# Check firewall
sudo ufw status
```

### Frontend Issues

**Cannot connect to backend:**
1. Verify backend IP address in `remote_settings.json`
2. Check if backend is running: `sudo systemctl status engine-simulator`
3. Test network connectivity: `ping 192.168.1.100`
4. Verify firewall allows connections

**WebSocket connection failed:**
- This is expected when using standalone MODBUS backend
- Frontend will show connection warnings but basic functionality works
- Engine data comes from direct MODBUS polling instead

### Vulnerability Demo Issues

**Connection refused:**
```bash
# Check if target is reachable
ping 192.168.1.100

# Check if MODBUS port is open
nc -zv 192.168.1.100 502
```

**Permission denied:**
```bash
# Install required dependencies
pip install pyModbusTCP pyyaml
```

## Testing the Complete Setup

### 1. Start Backend
```bash
# On Linux VM
sudo systemctl start engine-simulator
sudo systemctl status engine-simulator
```

### 2. Start Frontend
```bash
# On frontend machine
cd frontend
npm start
```

### 3. Demonstrate Vulnerability
```bash
# From attack machine
python demonstrate_vulnerability_remote.py 192.168.1.100 --full
```

### 4. Verify in Frontend
- Open http://localhost:3000
- You should see engine status change when vulnerability demo runs
- Engine should stop when attack is executed

## Advanced Configuration

### Custom Network Settings

**Backend on custom IP/Port:**
```bash
python standalone_backend.py --host 192.168.1.100 --port 5020
```

**Frontend with custom backend:**
Update `frontend/public/remote_settings.json`:
```json
{
  "modbusHost": "192.168.1.100",
  "modbusPort": 5020
}
```

### Multiple Backend Instances

Deploy multiple backends on different VMs:
```bash
# VM 1: Engine A
python standalone_backend.py --host 0.0.0.0 --port 502

# VM 2: Engine B  
python standalone_backend.py --host 0.0.0.0 --port 503
```

### Load Balancing

Use nginx or similar to load balance multiple backends:
```nginx
upstream modbus_backends {
    server 192.168.1.100:502;
    server 192.168.1.101:502;
}
```

## Cleanup

### Stop Services
```bash
# Stop systemd service
sudo systemctl stop engine-simulator
sudo systemctl disable engine-simulator

# Remove service file
sudo rm /etc/systemd/system/engine-simulator.service
sudo systemctl daemon-reload
```

### Docker Cleanup
```bash
# Stop containers
docker-compose -f docker-compose.backend.yml down

# Remove images
docker rmi engine-simulator
```

### Remove Files
```bash
# Remove backend files
rm -rf venv_backend
rm standalone_backend.py config_linux.yaml

# Remove frontend config
rm frontend/public/remote_settings.json
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify network connectivity between machines
3. Check firewall configurations
4. Review service logs: `sudo journalctl -u engine-simulator -f`

---

**Remember**: This setup demonstrates real security vulnerabilities. Use only on isolated networks or systems you own for educational purposes. 