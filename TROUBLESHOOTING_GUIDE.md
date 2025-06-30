# ME Simulator - Troubleshooting Guide

## 🔧 Issues Fixed

### 1. RPM Not Increasing ✅ FIXED
**Problem**: Engine RPM was not increasing when started.

**Solution Applied**:
- Enhanced startup logic in `engine/simulator.py`
- Added proper RPM initialization from minimum value (600 RPM)
- Implemented realistic acceleration (20-50 RPM per cycle)
- Fixed temperature and fuel flow calculations

### 2. Excessive Logging ✅ FIXED
**Problem**: Console was spammed with "ENGINE STOPPED" messages.

**Solution Applied**:
- Modified logging to only show stop message once
- Reduced repetitive debug output
- Added conditional logging based on engine state

### 3. FastAPI Deprecation Warnings ✅ FIXED
**Problem**: Deprecated `@app.on_event` decorators causing warnings.

**Solution Applied**:
- Updated to modern `lifespan` event handler
- Cleaner startup and shutdown process

### 4. Settings Page ✅ ADDED
**New Feature**: Comprehensive settings management.

**Components Added**:
- Dynamic settings interface
- Real-time configuration updates
- Backend API integration
- Persistent storage

## 🚀 How to Start the System

### Method 1: Using PowerShell Scripts (Recommended)
```powershell
# Terminal 1: Start Backend
.\start_backend.ps1

# Terminal 2: Start Frontend  
.\start_frontend.ps1
```

### Method 2: Manual Commands
```powershell
# Terminal 1: Backend
.\venv\Scripts\Activate.ps1
python app.py

# Terminal 2: Frontend
cd frontend
npm start
```

### Method 3: Command Prompt (if PowerShell issues)
```cmd
# Terminal 1: Backend
venv\Scripts\activate.bat
python app.py

# Terminal 2: Frontend
cd frontend
npm start
```

## 🔍 Testing the Fixes

### Test 1: Direct Engine Test
Run the simple test to verify engine functionality:
```powershell
python simple_test.py
```

Expected output:
```
✅ SUCCESS: RPM is increasing! Engine is working correctly.
```

### Test 2: Full System Test
1. Start backend: `python app.py`
2. Start frontend: `cd frontend && npm start`
3. Open browser: `http://localhost:3000`
4. Click "START ENGINE" button
5. Watch RPM gauge increase from 0 to ~900 RPM

### Test 3: Settings Page Test
1. Navigate to "Settings" tab in web interface
2. Modify engine parameters (e.g., change RPM max from 1200 to 1500)
3. Click "Save Settings"
4. Restart engine and verify new limits apply

## ⚠️ Common Issues & Solutions

### Issue: PowerShell Execution Policy
**Error**: Scripts cannot be executed
**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Python Not Found
**Error**: 'python' is not recognized
**Solutions**:
1. Use full path: `.\venv\Scripts\python.exe`
2. Activate venv first: `.\venv\Scripts\Activate.ps1`
3. Use Command Prompt instead of PowerShell

### Issue: Port Already in Use
**Error**: Address already in use (port 8000 or 3000)
**Solutions**:
1. Kill existing processes:
   ```powershell
   netstat -ano | findstr :8000
   taskkill /PID <PID_NUMBER> /F
   ```
2. Use different ports in settings

### Issue: WebSocket Connection Failed
**Error**: WebSocket connection errors in browser console
**Solutions**:
1. Verify backend is running on correct port
2. Check firewall settings
3. Update WebSocket URL in settings if needed

### Issue: RPM Still Not Increasing
**Troubleshooting Steps**:
1. Run `python simple_test.py` to test engine directly
2. Check browser console for WebSocket errors
3. Verify "START ENGINE" button sends command
4. Check backend logs for command reception

## 📊 Verification Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts and loads in browser
- [ ] WebSocket connection established (no red alert)
- [ ] "START ENGINE" button changes to "EMERGENCY STOP"
- [ ] RPM gauge shows increasing values (600→900)
- [ ] Temperature gauge shows warming (70→85°C)
- [ ] Load gauge shows increasing percentage
- [ ] Settings page loads and saves changes
- [ ] Engine stops when "EMERGENCY STOP" clicked

## 🔧 System Requirements

### Backend Requirements
- Python 3.8+
- Virtual environment activated
- Required packages installed (see requirements.txt)
- Port 8000 available

### Frontend Requirements
- Node.js 14+
- npm packages installed
- Port 3000 available
- Modern web browser

### Network Requirements
- WebSocket support
- CORS enabled
- Local network access (if testing on separate machines)

## 📝 Configuration Files

### Key Files Modified
- `engine/simulator.py` - Fixed RPM calculation
- `app.py` - Updated event handlers, added settings API
- `frontend/src/App.js` - Added settings integration
- `frontend/src/components/SettingsPage.js` - New settings interface

### Configuration Files
- `config.yaml` - Engine parameters
- `frontend/package.json` - Frontend dependencies
- `requirements.txt` - Backend dependencies

## 🆘 Getting Help

### Debug Mode
Enable debug information in Settings → Display Settings → "Show Debug Information"

### Log Files
Check console output for:
- Backend: Terminal running `python app.py`
- Frontend: Terminal running `npm start`
- Browser: Developer Tools → Console

### Contact Information
If issues persist, provide:
1. Error messages from console
2. Browser developer tools console output
3. Operating system and Python version
4. Steps taken before error occurred

## 🎯 Expected Behavior

### Normal Startup Sequence
1. Backend starts → "Modbus server started"
2. Frontend starts → "Compiled successfully"
3. Browser opens → Dashboard loads
4. Click START ENGINE → RPM increases 600→900
5. All gauges show realistic values
6. Settings page allows configuration changes

### Performance Indicators
- Engine startup time: ~5-10 seconds to reach target RPM
- WebSocket updates: Every 1 second
- Gauge animations: Smooth transitions
- Settings changes: Applied immediately 