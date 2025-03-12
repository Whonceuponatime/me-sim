import React, { memo } from 'react';
import { Box, Card, CardContent, CardHeader, Divider, Grid, Typography, Alert } from '@mui/material';

const TopologyView = memo(({ engineData, mqttData, plcData }) => {
  return (
    <Card>
      <CardHeader title="Engine Topology View" />
      <Divider />
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={12} md={8}>
            <Box
              sx={{
                position: 'relative',
                width: '100%',
                height: '600px',
                backgroundColor: '#f5f5f5',
                borderRadius: '8px',
                overflow: 'hidden'
              }}
            >
              {/* Engine Image */}
              <img
                src="/engine-topology.svg"
                alt="Engine Topology"
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain'
                }}
              />
              
              {/* Data Overlays */}
              <Box sx={{
                position: 'absolute',
                top: '20%',
                left: '20%',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ccc'
              }}>
                <Typography variant="subtitle2">Main Engine</Typography>
                <Typography>RPM: {engineData.rpm.toFixed(0)}</Typography>
                <Typography>Load: {engineData.load}%</Typography>
              </Box>

              <Box sx={{
                position: 'absolute',
                top: '40%',
                left: '60%',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ccc'
              }}>
                <Typography variant="subtitle2">Exhaust System</Typography>
                <Typography>Temperature: {mqttData.exhaust_temp.value.toFixed(1)}°C</Typography>
              </Box>

              <Box sx={{
                position: 'absolute',
                top: '60%',
                left: '30%',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ccc'
              }}>
                <Typography variant="subtitle2">Cooling System</Typography>
                <Typography>Water Temp: {mqttData.cooling_water_temp.value.toFixed(1)}°C</Typography>
              </Box>

              <Box sx={{
                position: 'absolute',
                top: '30%',
                right: '20%',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ccc'
              }}>
                <Typography variant="subtitle2">Turbocharger</Typography>
                <Typography>Speed: {mqttData.turbocharger_speed.value.toFixed(0)} RPM</Typography>
              </Box>

              <Box sx={{
                position: 'absolute',
                bottom: '20%',
                left: '40%',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #ccc'
              }}>
                <Typography variant="subtitle2">Lubrication System</Typography>
                <Typography>Oil Pressure: {mqttData.lube_oil_pressure.value.toFixed(2)} bar</Typography>
              </Box>
            </Box>
          </Grid>

          {/* PLC Status Panel */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title="PLC Status" />
              <Divider />
              <CardContent>
                <Typography variant="h6" gutterBottom>Mode: {plcData.mode}</Typography>
                <Typography variant="subtitle1" gutterBottom>Control Status</Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography>Engine Status: {
                    engineData.status === 0 ? 'Stopped' :
                    engineData.status === 1 ? 'Running' :
                    engineData.status === 2 ? 'Warning' : 'Alarm'
                  }</Typography>
                </Box>
                <Typography variant="subtitle1" gutterBottom>Active Alarms</Typography>
                {plcData.alarms.length > 0 ? (
                  plcData.alarms.map((alarm, index) => (
                    <Alert severity="error" key={index} sx={{ mb: 1 }}>
                      {alarm}
                    </Alert>
                  ))
                ) : (
                  <Alert severity="success">No active alarms</Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
});

export default TopologyView; 