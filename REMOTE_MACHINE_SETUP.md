# 🌐 ME Simulator - Remote Machine Configuration Guide

## 📋 **Overview**
This guide explains how to configure the ME Simulator to work when the backend and frontend are running on different machines or when accessing from remote clients.

## 🏗️ **Architecture Options**

### **Option 1: All Components on One Machine (Current Setup)**
```
[Machine A] Backend + Frontend + Browser
```
- Works locally with `localhost`
- No network configuration needed

### **Option 2: Backend on Server, Frontend on Client**
```
[Server Machine] Backend (Python app.py)
[Client Machine] Frontend (npm start) + Browser
```

### **Option 3: Backend on Server, Multiple Remote Clients**
```
[Server Machine] Backend (Python app.py)
[Client 1] Browser → Server IP
[Client 2] Browser → Server IP
[Client 3] Browser → Server IP
```

## 🔧 **Configuration Steps**

### **Step 1: Find Server Machine IP Address**

On the machine running the backend, find its IP address:

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., `192.168.1.100`)

**Linux/Mac:**
```bash
ip addr show
# or
ifconfig
```

### **Step 2: Update CORS Settings (Backend)**

The backend already includes common IP ranges, but you may need to add your specific network:

```python
# In app.py, update the origins list:
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.100:3000",  # Add your server IP
    "http://192.168.1.*:3000",    # Or allow entire subnet
    # WebSocket connections
    "ws://localhost:8000",
    "ws://127.0.0.1:8000", 
    "ws://192.168.1.100:8000",    # Add your server IP
    # Backend URLs
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.1.100:8000",  # Add your server IP
]
```

### **Step 3: Update Frontend Configuration**

#### **Option A: Using Settings Page (Recommended)**
1. Start the frontend locally first
2. Go to Settings tab
3. Update "WebSocket URL" from `ws://localhost:8000/ws` to `ws://SERVER_IP:8000/ws`
4. Update "Modbus Host" from `127.0.0.1` to `SERVER_IP`
5. Save settings

#### **Option B: Direct Code Change**
In `frontend/src/App.js`, update the default settings:

```javascript
const DEFAULT_SETTINGS = {
  websocketUrl: 'ws://192.168.1.100:8000/ws',  // Change to server IP
  modbusHost: '192.168.1.100',                 // Change to server IP
  modbusPort: 502,
  // ... other settings
};
```

### **Step 4: Firewall Configuration**

#### **Windows Server (Backend Machine)**
```powershell
# Allow Python through firewall
New-NetFirewallRule -DisplayName "ME Simulator Backend" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow

# Allow Modbus port
New-NetFirewallRule -DisplayName "ME Simulator Modbus" -Direction Inbound -Port 502 -Protocol TCP -Action Allow
```

#### **Linux Server**
```bash
# UFW (Ubuntu)
sudo ufw allow 8000/tcp
sudo ufw allow 502/tcp

# iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 502 -j ACCEPT
```

### **Step 5: Network Configuration**

#### **Port Forwarding (if needed)**
If machines are on different networks, configure router port forwarding:
- External Port 8000 → Internal IP:8000 (Backend)
- External Port 502 → Internal IP:502 (Modbus)

#### **VPN/Network Access**
Ensure machines can reach each other:
```cmd
# Test connectivity from client to server
ping 192.168.1.100
telnet 192.168.1.100 8000
```

## 🚀 **Deployment Scenarios**

### **Scenario 1: Development Setup**
```
[Developer Machine] Backend + Frontend
[Test Machine] Browser → Developer IP
```

**Configuration:**
1. Find developer machine IP: `192.168.1.100`
2. Update frontend settings: WebSocket URL = `ws://192.168.1.100:8000/ws`
3. Open browser on test machine: `http://192.168.1.100:3000`

### **Scenario 2: Production Setup**
```
[Server] Backend only
[Client Machines] Browser → Server IP
```

**Configuration:**
1. Build frontend for production: `npm run build`
2. Serve static files from backend
3. Access via: `http://SERVER_IP:8000`

### **Scenario 3: Separate Frontend Server**
```
[Server A] Backend (port 8000)
[Server B] Frontend (port 3000)
[Clients] Browser → Server B → Server A
```

**Configuration:**
1. Update frontend to point to Server A IP
2. Configure CORS to allow Server B
3. Access via: `http://SERVER_B_IP:3000`

## 📝 **Quick Setup Script**

Create a configuration script for easy setup:

```powershell
# setup-remote.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP
)

Write-Host "Configuring ME Simulator for remote access..." -ForegroundColor Green
Write-Host "Server IP: $ServerIP" -ForegroundColor Yellow

# Update frontend settings
$settingsFile = "frontend/src/App.js"
if (Test-Path $settingsFile) {
    (Get-Content $settingsFile) -replace 'ws://localhost:8000/ws', "ws://$ServerIP:8000/ws" | Set-Content $settingsFile
    (Get-Content $settingsFile) -replace '127.0.0.1', $ServerIP | Set-Content $settingsFile
    Write-Host "✅ Frontend configuration updated" -ForegroundColor Green
}

# Add firewall rules
try {
    New-NetFirewallRule -DisplayName "ME Simulator Backend" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "ME Simulator Modbus" -Direction Inbound -Port 502 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
    Write-Host "✅ Firewall rules added" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Could not add firewall rules (run as administrator)" -ForegroundColor Yellow
}

Write-Host "Configuration complete!" -ForegroundColor Green
Write-Host "Access the simulator at: http://$ServerIP:3000" -ForegroundColor Cyan
```

## 🔍 **Troubleshooting Remote Access**

### **Problem: Cannot Connect to Backend**
**Symptoms:** Browser shows "Connection lost" alert
**Solutions:**
1. Check server IP address: `ipconfig` or `ip addr`
2. Verify backend is running: `netstat -an | findstr :8000`
3. Test connectivity: `telnet SERVER_IP 8000`
4. Check firewall settings
5. Update WebSocket URL in settings

### **Problem: WebSocket Connection Fails**
**Symptoms:** Red connection alert, console errors
**Solutions:**
1. Verify WebSocket URL format: `ws://IP:8000/ws` (not `http://`)
2. Check CORS settings include client IP
3. Ensure no proxy/VPN blocking WebSocket
4. Try different browser

### **Problem: Modbus Commands Don't Work**
**Symptoms:** Engine starts but doesn't respond to commands
**Solutions:**
1. Check Modbus host setting in Settings page
2. Verify port 502 is open
3. Test Modbus connectivity: `telnet SERVER_IP 502`
4. Check if another service is using port 502

### **Problem: Settings Won't Save**
**Symptoms:** Settings revert after refresh
**Solutions:**
1. Check browser localStorage permissions
2. Verify API endpoint accessible: `http://SERVER_IP:8000/api/settings`
3. Check browser console for API errors

## 📊 **Network Requirements**

### **Ports Used**
- **8000/tcp** - FastAPI backend (HTTP/WebSocket)
- **502/tcp** - Modbus TCP server
- **3000/tcp** - React development server (if used)

### **Bandwidth**
- **WebSocket data:** ~1-2 KB/s per client
- **Initial load:** ~5-10 MB (React app)
- **API calls:** <1 KB per request

### **Latency**
- **Acceptable:** <100ms for good user experience
- **Maximum:** <500ms for usable experience

## 🎯 **Best Practices**

### **Security**
1. Use HTTPS/WSS in production
2. Implement authentication for settings API
3. Restrict CORS origins to known clients
4. Use VPN for remote access over internet

### **Performance**
1. Use production build for frontend: `npm run build`
2. Enable gzip compression
3. Use CDN for static assets
4. Monitor WebSocket connection count

### **Monitoring**
1. Log client connections and disconnections
2. Monitor system resources on server
3. Set up alerts for connection failures
4. Track API response times

## 📱 **Mobile Access**

The simulator is responsive and works on mobile devices:
1. Ensure mobile devices can reach server IP
2. Use same configuration as desktop clients
3. Consider touch-friendly controls for mobile UI

---

## 🎊 **Quick Reference**

### **Essential Configuration Checklist**
- [ ] Find server IP address
- [ ] Update WebSocket URL in settings
- [ ] Update Modbus host in settings  
- [ ] Configure firewall rules
- [ ] Test connectivity from client
- [ ] Verify CORS settings include client IPs
- [ ] Test full functionality (start/stop engine)

### **Common IP Ranges**
- **Local network:** `192.168.x.x` or `10.x.x.x`
- **Corporate network:** Varies (ask IT department)
- **Cloud servers:** Public IP from provider

**Your ME Simulator is now ready for multi-machine deployment!** 🚀 