# Engine Simulator - Settings & RPM Fix

## Overview
This document describes the fixes and enhancements made to the Marine Engine Simulator system.

## 🔧 Issues Fixed

### 1. RPM Not Increasing Issue
**Problem**: When starting the engine, the RPM was not increasing from 0, making the engine appear non-functional.

**Root Cause**: The engine startup logic was not properly initializing the RPM from the minimum value and the acceleration logic had timing issues.

**Solution**: 
- Enhanced the `calculate_engine_parameters()` method in `engine/simulator.py`
- Added proper startup sequence that begins from `rpm_min` when engine starts
- Implemented realistic acceleration with gradual RPM increase (20-50 RPM per update cycle)
- Added debug logging to track engine startup progression
- Fixed temperature and fuel flow calculations to be more realistic

**Result**: Engine now properly starts up and reaches target RPM with realistic acceleration.

## 🎛️ New Features Added

### 2. Dynamic Settings Page
**Feature**: Added a comprehensive settings page that allows real-time configuration of system parameters.

**Components Added**:
- `frontend/src/components/SettingsPage.js` - Main settings interface
- API endpoints in `app.py` for settings management
- Settings state management in `App.js`

**Settings Categories**:

#### Connection Settings
- WebSocket URL configuration
- Modbus host and port settings
- Reconnection parameters (delay, max attempts)

#### Engine Configuration
- RPM ranges (min, normal, max)
- Temperature thresholds (min, normal, warning, max)
- Fuel flow parameters
- Update intervals

#### Display Settings
- Dark mode toggle
- Debug information display
- Alarm flashing controls
- Gauge animation speed
- Chart update intervals
- History point limits

#### Security Settings
- Security logging controls
- Unauthorized attempt limits
- Alert level configuration

## 🚀 How to Use Settings

### Frontend Settings
1. Navigate to the "Settings" tab in the web interface
2. Modify any parameters in the expandable sections
3. Click "Save Settings" to apply changes
4. Settings are automatically saved to browser localStorage
5. Backend engine parameters are updated via API calls

### Backend Settings
Settings are automatically synchronized with the backend:
- Engine parameters update the simulator configuration
- Modbus settings can be changed (requires restart for full effect)
- Configuration is saved to `config.yaml`

### Settings Persistence
- Frontend settings: Stored in browser localStorage
- Backend settings: Saved to `config.yaml` file
- Settings survive browser refresh and application restart

## 🔄 Dynamic Configuration

### Real-time Updates
- WebSocket reconnection when URL changes
- Gauge scaling updates when RPM/temperature ranges change
- History buffer size adjusts dynamically
- Animation speeds change immediately

### Validation
- Port number validation (1-65535)
- RPM min/max validation
- Temperature range validation
- Error handling with user feedback

## 📊 API Endpoints

### GET /api/settings
Returns current system configuration:
```json
{
  "engine": { "rpm_min": 600, "rpm_max": 1200, ... },
  "modbus": { "host": "0.0.0.0", "port": 502 },
  "registers": { "status": 0, "rpm": 1, ... }
}
```

### POST /api/settings
Updates system configuration:
```json
{
  "engine": { "rpm_min": 700, "rpm_max": 1300, ... },
  "modbus": { "host": "192.168.1.100", "port": 502 }
}
```

## 🧪 Testing

The RPM fix has been tested and verified:
- Engine starts from minimum RPM (600)
- Accelerates realistically to target RPM (900)
- Shows proper progression in logs
- Stops correctly when commanded

## 📝 Configuration Files

### config.yaml
Updated to support dynamic configuration:
```yaml
engine:
  rpm_min: 600
  rpm_max: 1200
  rpm_normal: 900
  temp_min: 70
  temp_max: 120
  temp_normal: 85
  update_interval: 1.0
```

## 🔒 Security Considerations

- Settings validation prevents invalid configurations
- Backend settings require proper API access
- Security logging can be enabled/disabled
- Unauthorized access attempt tracking

## 🚀 Future Enhancements

Potential improvements:
- User authentication for settings access
- Settings profiles/presets
- Remote configuration management
- Settings backup/restore functionality
- Advanced validation rules

## 📞 Troubleshooting

### Common Issues
1. **Settings not saving**: Check browser console for API errors
2. **WebSocket not connecting**: Verify URL format and server status
3. **RPM still not increasing**: Check engine configuration in settings
4. **Backend settings not applying**: Verify API endpoint accessibility

### Debug Mode
Enable "Show Debug Information" in Display Settings to see:
- WebSocket connection status
- Settings validation messages
- API call responses
- Engine state transitions 