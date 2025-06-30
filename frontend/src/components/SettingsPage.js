import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, CardHeader, Grid, Typography,
  TextField, Button, Switch, FormControlLabel, Divider,
  Alert, Snackbar, Select, MenuItem, FormControl, InputLabel,
  Accordion, AccordionSummary, AccordionDetails, Slider,
  IconButton, Tooltip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SaveIcon from '@mui/icons-material/Save';
import RestoreIcon from '@mui/icons-material/Restore';
import SettingsIcon from '@mui/icons-material/Settings';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import SpeedIcon from '@mui/icons-material/Speed';
import ThermostatIcon from '@mui/icons-material/Thermostat';
import LocalGasStationIcon from '@mui/icons-material/LocalGasStation';

const SettingsPage = ({ onSettingsChange, currentSettings = {} }) => {
  const [settings, setSettings] = useState({
    // Connection Settings
    websocketUrl: 'ws://localhost:8000/ws',
    modbusHost: '127.0.0.1',
    modbusPort: 502,
    reconnectDelay: 2000,
    maxReconnectAttempts: 5,
    
    // Engine Configuration
    rpmMin: 600,
    rpmMax: 1200,
    rpmNormal: 900,
    tempMin: 70,
    tempMax: 120,
    tempNormal: 85,
    tempWarning: 90,
    tempCritical: 105,
    fuelFlowMin: 0.5,
    fuelFlowMax: 2.5,
    fuelFlowNormal: 1.5,
    
    // Update Intervals
    updateInterval: 1.0,
    chartUpdateInterval: 1000,
    maxHistoryPoints: 50,
    
    // Display Settings
    darkMode: true,
    showDebugInfo: false,
    enableSounds: false,
    enableAlarmFlashing: true,
    gaugeAnimationSpeed: 300,
    
    // Security Settings
    enableSecurityLogging: true,
    maxUnauthorizedAttempts: 3,
    securityAlertLevel: 'high',
    
    ...currentSettings
  });

  const [originalSettings, setOriginalSettings] = useState({});
  const [hasChanges, setHasChanges] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    setOriginalSettings({ ...settings });
  }, []);

  useEffect(() => {
    const changed = JSON.stringify(settings) !== JSON.stringify(originalSettings);
    setHasChanges(changed);
  }, [settings, originalSettings]);

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = async () => {
    try {
      // Validate settings
      if (settings.modbusPort < 1 || settings.modbusPort > 65535) {
        throw new Error('Modbus port must be between 1 and 65535');
      }
      if (settings.rpmMin >= settings.rpmMax) {
        throw new Error('RPM minimum must be less than maximum');
      }
      if (settings.tempMin >= settings.tempMax) {
        throw new Error('Temperature minimum must be less than maximum');
      }

      // Save to localStorage
      localStorage.setItem('engineSettings', JSON.stringify(settings));
      
      // Save engine settings to backend
      try {
        const engineSettings = {
          engine: {
            rpm_min: settings.rpmMin,
            rpm_max: settings.rpmMax,
            rpm_normal: settings.rpmNormal,
            temp_min: settings.tempMin,
            temp_max: settings.tempMax,
            temp_normal: settings.tempNormal,
            fuel_flow_min: settings.fuelFlowMin,
            fuel_flow_max: settings.fuelFlowMax,
            fuel_flow_normal: settings.fuelFlowNormal,
            update_interval: settings.updateInterval
          },
          modbus: {
            host: settings.modbusHost,
            port: settings.modbusPort
          }
        };

        const response = await fetch('/api/settings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(engineSettings)
        });

        const result = await response.json();
        if (result.status !== 'success') {
          console.warn('Backend settings update failed:', result.message);
        }
      } catch (backendError) {
        console.warn('Failed to update backend settings:', backendError);
        // Don't fail the entire save operation if backend update fails
      }
      
      // Notify parent component
      if (onSettingsChange) {
        onSettingsChange(settings);
      }

      setOriginalSettings({ ...settings });
      setSnackbar({
        open: true,
        message: 'Settings saved successfully!',
        severity: 'success'
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Error saving settings: ${error.message}`,
        severity: 'error'
      });
    }
  };

  const handleReset = () => {
    setSettings({ ...originalSettings });
    setSnackbar({
      open: true,
      message: 'Settings reset to last saved values',
      severity: 'info'
    });
  };

  const handleRestoreDefaults = () => {
    const defaultSettings = {
      websocketUrl: 'ws://localhost:8000/ws',
      modbusHost: '127.0.0.1',
      modbusPort: 502,
      reconnectDelay: 2000,
      maxReconnectAttempts: 5,
      rpmMin: 600,
      rpmMax: 1200,
      rpmNormal: 900,
      tempMin: 70,
      tempMax: 120,
      tempNormal: 85,
      tempWarning: 90,
      tempCritical: 105,
      fuelFlowMin: 0.5,
      fuelFlowMax: 2.5,
      fuelFlowNormal: 1.5,
      updateInterval: 1.0,
      chartUpdateInterval: 1000,
      maxHistoryPoints: 50,
      darkMode: true,
      showDebugInfo: false,
      enableSounds: false,
      enableAlarmFlashing: true,
      gaugeAnimationSpeed: 300,
      enableSecurityLogging: true,
      maxUnauthorizedAttempts: 3,
      securityAlertLevel: 'high'
    };
    
    setSettings(defaultSettings);
    setSnackbar({
      open: true,
      message: 'Settings restored to defaults',
      severity: 'info'
    });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SettingsIcon sx={{ mr: 2, color: '#00ff00' }} />
        <Typography variant="h4" sx={{ color: '#00ff00' }}>
          System Settings
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Connection Settings */}
        <Grid item xs={12} md={6}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <NetworkCheckIcon sx={{ mr: 1, color: '#00ff00' }} />
                <Typography variant="h6">Connection Settings</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="WebSocket URL"
                    value={settings.websocketUrl}
                    onChange={(e) => handleSettingChange('connection', 'websocketUrl', e.target.value)}
                    helperText="WebSocket connection URL for real-time data"
                  />
                </Grid>
                <Grid item xs={8}>
                  <TextField
                    fullWidth
                    label="Modbus Host"
                    value={settings.modbusHost}
                    onChange={(e) => handleSettingChange('connection', 'modbusHost', e.target.value)}
                    helperText="IP address of Modbus server"
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="Modbus Port"
                    type="number"
                    value={settings.modbusPort}
                    onChange={(e) => handleSettingChange('connection', 'modbusPort', parseInt(e.target.value))}
                    helperText="Port number"
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Reconnect Delay (ms)"
                    type="number"
                    value={settings.reconnectDelay}
                    onChange={(e) => handleSettingChange('connection', 'reconnectDelay', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Max Reconnect Attempts"
                    type="number"
                    value={settings.maxReconnectAttempts}
                    onChange={(e) => handleSettingChange('connection', 'maxReconnectAttempts', parseInt(e.target.value))}
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Engine Configuration */}
        <Grid item xs={12} md={6}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SpeedIcon sx={{ mr: 1, color: '#00ff00' }} />
                <Typography variant="h6">Engine Configuration</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="subtitle1" sx={{ mb: 2 }}>RPM Settings</Typography>
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="RPM Min"
                    type="number"
                    value={settings.rpmMin}
                    onChange={(e) => handleSettingChange('engine', 'rpmMin', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="RPM Normal"
                    type="number"
                    value={settings.rpmNormal}
                    onChange={(e) => handleSettingChange('engine', 'rpmNormal', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="RPM Max"
                    type="number"
                    value={settings.rpmMax}
                    onChange={(e) => handleSettingChange('engine', 'rpmMax', parseInt(e.target.value))}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle1" sx={{ mb: 2 }}>Temperature Settings (°C)</Typography>
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    fullWidth
                    label="Temp Min"
                    type="number"
                    value={settings.tempMin}
                    onChange={(e) => handleSettingChange('engine', 'tempMin', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    fullWidth
                    label="Temp Normal"
                    type="number"
                    value={settings.tempNormal}
                    onChange={(e) => handleSettingChange('engine', 'tempNormal', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    fullWidth
                    label="Temp Warning"
                    type="number"
                    value={settings.tempWarning}
                    onChange={(e) => handleSettingChange('engine', 'tempWarning', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={3}>
                  <TextField
                    fullWidth
                    label="Temp Max"
                    type="number"
                    value={settings.tempMax}
                    onChange={(e) => handleSettingChange('engine', 'tempMax', parseInt(e.target.value))}
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Display Settings */}
        <Grid item xs={12} md={6}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Display Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.darkMode}
                        onChange={(e) => handleSettingChange('display', 'darkMode', e.target.checked)}
                      />
                    }
                    label="Dark Mode"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.showDebugInfo}
                        onChange={(e) => handleSettingChange('display', 'showDebugInfo', e.target.checked)}
                      />
                    }
                    label="Show Debug Information"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enableAlarmFlashing}
                        onChange={(e) => handleSettingChange('display', 'enableAlarmFlashing', e.target.checked)}
                      />
                    }
                    label="Enable Alarm Flashing"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" gutterBottom>
                    Gauge Animation Speed: {settings.gaugeAnimationSpeed}ms
                  </Typography>
                  <Slider
                    value={settings.gaugeAnimationSpeed}
                    onChange={(e, value) => handleSettingChange('display', 'gaugeAnimationSpeed', value)}
                    min={100}
                    max={1000}
                    step={50}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Chart Update Interval (ms)"
                    type="number"
                    value={settings.chartUpdateInterval}
                    onChange={(e) => handleSettingChange('display', 'chartUpdateInterval', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Max History Points"
                    type="number"
                    value={settings.maxHistoryPoints}
                    onChange={(e) => handleSettingChange('display', 'maxHistoryPoints', parseInt(e.target.value))}
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Security Settings */}
        <Grid item xs={12} md={6}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Security Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.enableSecurityLogging}
                        onChange={(e) => handleSettingChange('security', 'enableSecurityLogging', e.target.checked)}
                      />
                    }
                    label="Enable Security Logging"
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Max Unauthorized Attempts"
                    type="number"
                    value={settings.maxUnauthorizedAttempts}
                    onChange={(e) => handleSettingChange('security', 'maxUnauthorizedAttempts', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>Security Alert Level</InputLabel>
                    <Select
                      value={settings.securityAlertLevel}
                      onChange={(e) => handleSettingChange('security', 'securityAlertLevel', e.target.value)}
                    >
                      <MenuItem value="low">Low</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="high">High</MenuItem>
                      <MenuItem value="critical">Critical</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Action Buttons */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', alignItems: 'center' }}>
                <Typography variant="body2" color="textSecondary">
                  {hasChanges ? 'You have unsaved changes' : 'All changes saved'}
                </Typography>
                <Button
                  variant="outlined"
                  onClick={handleRestoreDefaults}
                  startIcon={<RestoreIcon />}
                >
                  Restore Defaults
                </Button>
                <Button
                  variant="outlined"
                  onClick={handleReset}
                  disabled={!hasChanges}
                >
                  Reset
                </Button>
                <Button
                  variant="contained"
                  onClick={handleSave}
                  disabled={!hasChanges}
                  startIcon={<SaveIcon />}
                  sx={{ minWidth: 120 }}
                >
                  Save Settings
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SettingsPage; 