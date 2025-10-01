# Troubleshooting Guide

## API Connection Failed - Step by Step Debugging

### 1. Check Backend is Running (Linux)

**Run the simple backend first:**
```bash
./start_backend_simple.sh
```

**You should see:**
```
Starting MODBUS TCP Backend on Linux
==========================================
Backend IP: 192.168.20.192
Backend Port: 502
HTTP API Port: 8080
Frontend IP: 192.168.20.100
==========================================
Starting MODBUS TCP Server + HTTP API...
MODBUS server will listen on 0.0.0.0:502 (all interfaces)
HTTP API will listen on 0.0.0.0:8080 (all interfaces)
Frontend can connect from 192.168.20.100

Press Ctrl+C to stop the server
==========================================
✓ MODBUS TCP Server started successfully
✓ HTTP Server started on 0.0.0.0:8080
✓ Engine simulation started
```

### 2. Test Backend API (Windows)

**From Windows machine, test the API:**
```bash
python test_backend.py
```

**Or use curl:**
```bash
curl http://192.168.20.192:8080/api/status
```

**Expected response:**
```json
{
  "engine": {
    "status": 0,
    "rpm": 0,
    "temp": 70,
    "fuel_flow": 0.0,
    "load": 0
  },
  "timestamp": "2025-01-01T12:00:00"
}
```

### 3. Check Frontend Console (Windows)

**Open browser console (F12) and look for:**
- `"Loaded settings:"` - Should show the config
- `"Fetching from: http://192.168.20.192:8080/api/status"`
- `"Response status: 200"` - Should be 200, not 404 or error

### 4. Common Issues and Fixes

#### Issue: "Connection refused" or "Network error"
**Cause:** Backend not running or firewall blocking
**Fix:** 
- Make sure backend is running on Linux
- Check firewall: `sudo ufw allow 8080`
- Test with: `telnet 192.168.20.192 8080`

#### Issue: "404 Not Found"
**Cause:** Wrong API endpoint
**Fix:** Backend should serve `/api/status`, not `/api/engine`

#### Issue: "CORS error"
**Cause:** Cross-origin request blocked
**Fix:** Backend has CORS headers, but check browser console

#### Issue: "No API base URL configured"
**Cause:** `remote_settings.json` not loading
**Fix:** Check if file exists in `frontend/public/`

### 5. Network Connectivity Test

**From Windows, test connectivity:**
```bash
# Test if Linux machine is reachable
ping 192.168.20.192

# Test if port 8080 is open
telnet 192.168.20.192 8080

# Test if port 502 is open (MODBUS)
telnet 192.168.20.192 502
```

### 6. Backend Logs to Check

**Look for these messages in backend console:**
- `✓ MODBUS TCP Server started successfully`
- `✓ HTTP Server started on 0.0.0.0:8080`
- `✓ Engine simulation started`
- `192.168.20.100 - - [timestamp] "GET /api/status HTTP/1.1" 200 -`

### 7. Frontend Logs to Check

**Look for these in browser console:**
- `Loaded settings: {apiBaseUrl: "http://192.168.20.192:8080/api", ...}`
- `Fetching from: http://192.168.20.192:8080/api/status`
- `Response status: 200`
- `API data received: {engine: {...}}`

### 8. Quick Fix Commands

**If backend won't start:**
```bash
# Check if port 502 is in use
sudo netstat -tlnp | grep :502
sudo netstat -tlnp | grep :8080

# Kill any processes using these ports
sudo fuser -k 502/tcp
sudo fuser -k 8080/tcp

# Try running with sudo (if permission denied)
sudo python3 standalone_backend.py --host 0.0.0.0 --port 502
```

**If frontend won't start:**
```bash
# Clean and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

### 9. Expected Network Traffic

**With Wireshark, you should see:**
- **MODBUS TCP**: Port 502 traffic (if traffic generator is running)
- **HTTP API**: Port 8080 traffic between 192.168.20.100 and 192.168.20.192

**Wireshark filters:**
- `tcp.port == 502` - MODBUS traffic
- `tcp.port == 8080` - HTTP API traffic
- `ip.addr == 192.168.20.192` - All backend traffic
