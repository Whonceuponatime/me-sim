import React, { memo } from 'react';
import { Box, Typography, Grid, Paper } from '@mui/material';

const ComponentBox = ({ title, value, unit, status, children }) => (
  <Paper
    elevation={3}
    sx={{
      p: 2,
      borderRadius: 2,
      backgroundColor: '#1a1a1a',
      border: '1px solid #333',
      position: 'relative',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '2px',
        background: 'linear-gradient(90deg, #00ff00, #333)',
        opacity: status === 1 ? 1 : 0.3
      }
    }}
  >
    <Typography variant="subtitle2" sx={{ color: '#666', mb: 1, textTransform: 'uppercase' }}>
      {title}
    </Typography>
    {value && (
      <Typography variant="h6" sx={{ color: '#00ff00', fontFamily: 'monospace' }}>
        {value} {unit}
      </Typography>
    )}
    {children}
  </Paper>
);

const ConnectionLine = ({ direction = 'horizontal', color = '#00ff00' }) => (
  <Box
    sx={{
      position: 'relative',
      width: direction === 'horizontal' ? '100%' : '2px',
      height: direction === 'horizontal' ? '2px' : '100%',
      backgroundColor: color,
      opacity: 0.5,
      '&::after': {
        content: '""',
        position: 'absolute',
        width: direction === 'horizontal' ? '10px' : '2px',
        height: direction === 'horizontal' ? '2px' : '10px',
        backgroundColor: color,
        right: direction === 'horizontal' ? 0 : 'auto',
        bottom: direction === 'horizontal' ? 'auto' : 0
      }
    }}
  />
);

const TopologyView = memo(({ engineData, mqttData, plcData }) => {
  return (
    <Box sx={{ p: 3, backgroundColor: '#0a0a0a', borderRadius: 2, minHeight: '80vh' }}>
      <Grid container spacing={3}>
        {/* PLC Controller */}
        <Grid item xs={12} md={3}>
          <ComponentBox 
            title="PLC CONTROLLER"
            status={engineData.status}
          >
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>Mode: {plcData.mode}</Typography>
              <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>Status: {engineData.status === 1 ? 'ONLINE' : 'OFFLINE'}</Typography>
              <Typography variant="body2" sx={{ color: '#666' }}>Alarms: {plcData.alarms.length}</Typography>
            </Box>
          </ComponentBox>
        </Grid>

        {/* Connection Lines */}
        <Grid item xs={12} md={1} sx={{ display: 'flex', alignItems: 'center' }}>
          <ConnectionLine />
        </Grid>

        {/* Main Engine Block */}
        <Grid item xs={12} md={4}>
          <ComponentBox 
            title="MAIN ENGINE"
            status={engineData.status}
          >
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>RPM</Typography>
                  <Typography variant="h6" sx={{ color: '#00ff00', fontFamily: 'monospace' }}>
                    {engineData.rpm}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>TEMP</Typography>
                  <Typography variant="h6" sx={{ color: '#00ff00', fontFamily: 'monospace' }}>
                    {engineData.temperature}°C
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>LOAD</Typography>
                  <Typography variant="h6" sx={{ color: '#00ff00', fontFamily: 'monospace' }}>
                    {engineData.load}%
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </ComponentBox>
        </Grid>

        {/* Connection Lines */}
        <Grid item xs={12} md={1} sx={{ display: 'flex', alignItems: 'center' }}>
          <ConnectionLine />
        </Grid>

        {/* Sensors Block */}
        <Grid item xs={12} md={3}>
          <ComponentBox 
            title="SENSORS"
            status={engineData.status}
          >
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                Exhaust: {mqttData.exhaust_temp.value.toFixed(1)}°C
              </Typography>
              <Typography variant="body2" sx={{ color: '#666', mb: 1 }}>
                Lube Oil: {mqttData.lube_oil_pressure.value.toFixed(1)} bar
              </Typography>
              <Typography variant="body2" sx={{ color: '#666' }}>
                Cooling: {mqttData.cooling_water_temp.value.toFixed(1)}°C
              </Typography>
            </Box>
          </ComponentBox>
        </Grid>

        {/* Auxiliary Systems */}
        <Grid item xs={12}>
          <Box sx={{ mt: 4, position: 'relative' }}>
            <ConnectionLine direction="vertical" />
            <Grid container spacing={3} sx={{ mt: 2 }}>
              <Grid item xs={12} md={3}>
                <ComponentBox 
                  title="TURBOCHARGER"
                  value={mqttData.turbocharger_speed.value.toFixed(0)}
                  unit="RPM"
                  status={engineData.status}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <ComponentBox 
                  title="LUBRICATION"
                  value={mqttData.lube_oil_pressure.value.toFixed(1)}
                  unit="bar"
                  status={engineData.status}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <ComponentBox 
                  title="COOLING"
                  value={mqttData.cooling_water_temp.value.toFixed(1)}
                  unit="°C"
                  status={engineData.status}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <ComponentBox 
                  title="FUEL SYSTEM"
                  value={engineData.fuel_flow.toFixed(2)}
                  unit="t/h"
                  status={engineData.status}
                />
              </Grid>
            </Grid>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
});

export default TopologyView; 