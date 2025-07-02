# Quick Start: Multi-Machine Engine Simulator

## What We've Created

Your engine simulator has been successfully separated into multiple components for realistic multi-machine deployment:

### 🖥️ New Files Created

**Standalone Backend:**
- `standalone_backend.py` - Pure MODBUS TCP server (runs on Linux VM)
- `config_linux.yaml` - Linux-optimized configuration
- `deploy_backend.sh` - Automated deployment script

**Enhanced Vulnerability Demo:**
- `demonstrate_vulnerability_remote.py` - Advanced remote vulnerability testing

**Docker Support:**
- `Dockerfile.backend` - Container for backend deployment
- `docker-compose.backend.yml` - Docker Compose configuration

**Frontend Configuration:**
- `frontend/public/remote_settings_template.json` - Template for remote connection

**Documentation:**
- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `QUICK_START.md` - This quick start guide

## 🚀 Quick Deployment

### 1. Deploy Backend on Linux VM

```bash
# Transfer files to your Linux VM, then:
chmod +x deploy_backend.sh
sudo ./deploy_backend.sh

# Start the service
sudo systemctl start engine-simulator
```

### 2. Configure Frontend

```bash
# Copy template and update IP address
cp frontend/public/remote_settings_template.json frontend/public/remote_settings.json

# Edit the file to point to your Linux VM IP
# Example: "modbusHost": "192.168.1.100"
```

### 3. Test the Setup

```bash
# Test MODBUS connectivity from any machine
python demonstrate_vulnerability_remote.py 192.168.1.100 --full

# Start frontend
cd frontend && npm start
```

## 🎯 Key Benefits

✅ **Realistic Architecture**: Backend runs on separate Linux machine  
✅ **Real MODBUS TCP**: Actual industrial protocol packets  
✅ **Security Demonstration**: Shows real-world vulnerabilities  
✅ **Multiple Deployment Options**: Bare metal, Docker, or systemd service  
✅ **Network Separation**: Frontend and backend can be on different networks  

## 🔧 Usage Examples

**Start backend manually:**
```bash
python standalone_backend.py --host 0.0.0.0 --port 502
```

**Test with vulnerability script:**
```bash
# Scan for MODBUS service
python demonstrate_vulnerability_remote.py 192.168.1.100 --scan-only

# Read current engine data
python demonstrate_vulnerability_remote.py 192.168.1.100 --read-only

# Demonstrate stop attack
python demonstrate_vulnerability_remote.py 192.168.1.100 --stop-only
```

**Monitor backend service:**
```bash
# Check status
sudo systemctl status engine-simulator

# View live logs
sudo journalctl -u engine-simulator -f
```

## 🛡️ Security Demonstration

The system now demonstrates these real-world vulnerabilities:

1. **No Authentication** - Anyone can connect to MODBUS server
2. **No Encryption** - All data sent in plain text
3. **Remote Control** - Engine can be stopped/started from any machine
4. **Parameter Manipulation** - Safety-critical values can be changed
5. **Network Exposure** - Server accessible from entire network

## 📁 File Structure

```
me-sim/
├── standalone_backend.py          # 🆕 Standalone MODBUS server
├── config_linux.yaml             # 🆕 Linux configuration
├── deploy_backend.sh              # 🆕 Deployment script
├── demonstrate_vulnerability_remote.py  # 🆕 Remote vulnerability demo
├── Dockerfile.backend             # 🆕 Docker configuration
├── docker-compose.backend.yml     # 🆕 Docker Compose
├── DEPLOYMENT_GUIDE.md            # 🆕 Complete instructions
├── QUICK_START.md                 # 🆕 This file
├── frontend/
│   └── public/
│       └── remote_settings_template.json  # 🆕 Frontend config template
├── app.py                         # Original combined backend
├── demonstrate_vulnerability.py    # Original local demo
└── ...                           # Other existing files
```

## 🔄 Migration from Original Setup

**Before**: Single machine running `app.py` with WebSocket frontend  
**After**: Separated architecture with real MODBUS TCP communication

The original files (`app.py`, `demonstrate_vulnerability.py`) are still available for local testing.

## 📞 Need Help?

1. **Read the full guide**: `DEPLOYMENT_GUIDE.md`
2. **Check troubleshooting**: Look for common issues in deployment guide
3. **Test connectivity**: Use `demonstrate_vulnerability_remote.py --scan-only`
4. **Check logs**: `sudo journalctl -u engine-simulator -f`

---

**🎉 Your engine simulator is now ready for realistic multi-machine deployment with actual MODBUS TCP communication!** 