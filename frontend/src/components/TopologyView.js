import React, { memo } from 'react';
import { Box, Card, CardContent, CardHeader, Divider, Grid, Typography, Alert, Paper } from '@mui/material';

const DataBox = ({ title, children, sx = {} }) => (
  <Paper
    elevation={0}
    sx={{
      p: 3,
      borderRadius: 2,
      backgroundColor: '#f8f9fa',
      height: '100%',
      ...sx
    }}
  >
    <Typography
      variant="subtitle2"
      sx={{
        fontSize: '0.875rem',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        color: '#666',
        mb: 1
      }}
    >
      {title}
    </Typography>
    {children}
  </Paper>
);

const TopologyView = memo(({ engineData, mqttData, plcData }) => {
  return (
    <Grid container spacing={3}>
      {/* Main Engine Data */}
      <Grid item xs={12} md={4}>
        <Card sx={{ borderRadius: 2, boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <CardHeader 
            title={
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                Main Engine
              </Typography>
            }
          />
          <Divider />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <DataBox title="Engine Status">
                  <Typography variant="h5" sx={{ fontWeight: 500, color: engineData.status === 1 ? '#4caf50' : '#666' }}>
                    {engineData.status === 1 ? 'Running' : 'Stopped'}
                  </Typography>
                </DataBox>
              </Grid>
              <Grid item xs={6}>
                <DataBox title="RPM">
                  <Typography variant="h5" sx={{ fontWeight: 500 }}>
                    {engineData.rpm.toFixed(0)}
                  </Typography>
                </DataBox>
              </Grid>
              <Grid item xs={6}>
                <DataBox title="Load">
                  <Typography variant="h5" sx={{ fontWeight: 500 }}>
                    {engineData.load}%
                  </Typography>
                </DataBox>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Temperature Systems */}
      <Grid item xs={12} md={4}>
        <Card sx={{ borderRadius: 2, boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <CardHeader 
            title={
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                Temperature Systems
              </Typography>
            }
          />
          <Divider />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <DataBox title="Engine Temp">
                  <Typography variant="h5" sx={{ fontWeight: 500 }}>
                    {engineData.temperature.toFixed(1)}°C
                  </Typography>
                </DataBox>
              </Grid>
              <Grid item xs={6}>
                <DataBox title="Exhaust Temp">
                  <Typography variant="h5" sx={{ fontWeight: 500 }}>
                    {mqttData.exhaust_temp.value.toFixed(1)}°C
                  </Typography>
                </DataBox>
              </Grid>
              <Grid item xs={12}>
                <DataBox title="Cooling Water">
                  <Typography variant="h5" sx={{ fontWeight: 500 }}>
                    {mqttData.cooling_water_temp.value.toFixed(1)}°C
                  </Typography>
                </DataBox>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Auxiliary Systems */}
      <Grid item xs={12} md={4}>
        <Card sx={{ borderRadius: 2, boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <CardHeader 
            title={
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                Auxiliary Systems
              </Typography>
            }
          />
          <Divider />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <DataBox title="Turbocharger">
                  <Typography variant="h5" sx={{ fontWeight: 500 }}>
                    {mqttData.turbocharger_speed.value.toFixed(0)} RPM
                  </Typography>
                </DataBox>
              </Grid>
              <Grid item xs={12}>
                <DataBox title="Lubrication System">
                  <Typography variant="h5" sx={{ fontWeight: 500 }}>
                    {mqttData.lube_oil_pressure.value.toFixed(2)} bar
                  </Typography>
                </DataBox>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* System Status */}
      <Grid item xs={12}>
        <Card sx={{ borderRadius: 2, boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <CardHeader 
            title={
              <Typography variant="h6" sx={{ fontWeight: 500 }}>
                System Status
              </Typography>
            }
          />
          <Divider />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <DataBox title="Operation Mode">
                  <Typography variant="h5" sx={{ fontWeight: 500 }}>
                    {plcData.mode}
                  </Typography>
                </DataBox>
              </Grid>
              <Grid item xs={12} md={8}>
                <DataBox 
                  title="Active Alarms"
                  sx={{
                    backgroundColor: plcData.alarms.length > 0 ? '#fff3f3' : '#f0f7f0'
                  }}
                >
                  {plcData.alarms.length > 0 ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {plcData.alarms.map((alarm, index) => (
                        <Alert 
                          key={index} 
                          severity="error"
                          sx={{ 
                            borderRadius: 1,
                            '& .MuiAlert-message': { fontWeight: 500 }
                          }}
                        >
                          {alarm}
                        </Alert>
                      ))}
                    </Box>
                  ) : (
                    <Alert 
                      severity="success"
                      sx={{ 
                        borderRadius: 1,
                        '& .MuiAlert-message': { fontWeight: 500 }
                      }}
                    >
                      All systems operating normally
                    </Alert>
                  )}
                </DataBox>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
});

export default TopologyView; 