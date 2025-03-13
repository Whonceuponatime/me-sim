import React, { useState, useEffect, useRef, useCallback, useMemo, memo } from 'react';
import { 
  Container, Grid, Paper, Typography, Button, 
  Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Alert, Tab, Tabs, Box,
  Card, CardContent, CardHeader, Divider,
  AppBar, Toolbar, LinearProgress,
  createTheme, ThemeProvider
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import GaugeChart from 'react-gauge-chart';
import AnimatedGauge from './components/AnimatedGauge';
import TopologyView from './components/TopologyView';
import logo from './assets/logo.png';

const WEBSOCKET_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
const RECONNECT_DELAY = 2000; // 2 seconds delay between reconnection attempts
const MAX_RECONNECT_ATTEMPTS = 5;

// Add engine configuration constants
const ENGINE_CONFIG = {
  rpm_max: 2000,
  rpm_min: 0,
  temp_max: 95,
  temp_min: 20,
  temp_warning: 75,
  temp_critical: 85,
  fuel_flow_max: 5.0,
  fuel_flow_min: 0,
  load_warning: 80,
  load_critical: 90
};

// Add sensor configuration constants
const SENSOR_CONFIG = {
  exhaust_temp: {
    min: 0,
    max: 600,
    warning: 450,
    critical: 500,
    unit: '°C'
  },
  lube_oil_pressure: {
    min: 0,
    max: 10,
    warning: 3,
    critical: 2,
    unit: 'bar'
  },
  cooling_water_temp: {
    min: 0,
    max: 100,
    warning: 75,
    critical: 85,
    unit: '°C'
  },
  turbocharger_speed: {
    min: 0,
    max: 150000,
    warning: 120000,
    critical: 130000,
    unit: 'rpm'
  }
};

// Create dark theme for marine look
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00ff00',
    },
    secondary: {
      main: '#ff9800',
    },
    background: {
      default: '#1a1a1a',
      paper: '#2d2d2d',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#2d2d2d',
          border: '1px solid #404040',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
  },
});

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [engineData, setEngineData] = useState({
    rpm: 0,
    temperature: 0,
    fuel_flow: 0,
    load: 0,
    status: 0,
    history: []
  });

  const [mqttData, setMqttData] = useState({
    exhaust_temp: { value: 0, unit: '°C' },
    lube_oil_pressure: { value: 0, unit: 'bar' },
    cooling_water_temp: { value: 0, unit: '°C' },
    turbocharger_speed: { value: 0, unit: 'rpm' }
  });

  const [plcData, setPlcData] = useState({
    mode: 'MANUAL',
    alarms: [],
    setpoints: {}
  });

  const [historicalData, setHistoricalData] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef(null);

  // Memoize the gauge values to prevent unnecessary re-renders
  const gaugeValues = useMemo(() => ({
    rpm: {
      value: engineData.rpm,
      normalized: engineData.rpm / ENGINE_CONFIG.rpm_max
    },
    temperature: {
      value: engineData.temperature,
      normalized: (engineData.temperature - ENGINE_CONFIG.temp_min) / 
                 (ENGINE_CONFIG.temp_max - ENGINE_CONFIG.temp_min)
    },
    fuelFlow: {
      value: engineData.fuel_flow,
      normalized: engineData.fuel_flow / ENGINE_CONFIG.fuel_flow_max
    },
    load: {
      value: engineData.load,
      normalized: engineData.load / 100
    }
  }), [engineData]);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      console.log('Attempting to connect to WebSocket...');
      const ws = new WebSocket(WEBSOCKET_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected successfully');
        setWsConnected(true);
        reconnectAttempts.current = 0; // Reset reconnection attempts on successful connection
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setWsConnected(false);
        
        // Clear any existing reconnection timeout
        if (reconnectTimeout.current) {
          clearTimeout(reconnectTimeout.current);
        }

        // Attempt to reconnect if we haven't exceeded max attempts
        if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          console.log(`Attempting to reconnect... (${reconnectAttempts.current + 1}/${MAX_RECONNECT_ATTEMPTS})`);
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current += 1;
            connectWebSocket();
          }, RECONNECT_DELAY);
        } else {
          console.error('Max reconnection attempts reached. Please refresh the page.');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Don't close the connection here, let the onclose handler deal with reconnection
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'modbus') {
            setEngineData(prevData => {
              const newHistoryPoint = {
                time: new Date().toLocaleTimeString(),
                ...data.engine,
                exhaust_temp: prevData.history.length > 0 
                  ? prevData.history[prevData.history.length - 1].exhaust_temp 
                  : 0,
                lube_oil_pressure: prevData.history.length > 0 
                  ? prevData.history[prevData.history.length - 1].lube_oil_pressure 
                  : 0,
                cooling_water_temp: prevData.history.length > 0 
                  ? prevData.history[prevData.history.length - 1].cooling_water_temp 
                  : 0,
                turbocharger_speed: prevData.history.length > 0 
                  ? prevData.history[prevData.history.length - 1].turbocharger_speed 
                  : 0
              };
              
              return {
                ...prevData,
                ...data.engine,
                history: [...prevData.history, newHistoryPoint].slice(-50)
              };
            });

            if (data.plc) {
              setPlcData(prevData => ({
                ...prevData,
                ...data.plc
              }));
            }
          } else if (data.type === 'mqtt') {
            setMqttData(prevData => ({
              ...prevData,
              ...data.sensors
            }));
            
            setEngineData(prevData => {
              if (prevData.history.length === 0) return prevData;
              
              const updatedHistory = [...prevData.history];
              const lastPoint = updatedHistory[updatedHistory.length - 1];
              updatedHistory[updatedHistory.length - 1] = {
                ...lastPoint,
                exhaust_temp: data.sensors.exhaust_temp.value,
                lube_oil_pressure: data.sensors.lube_oil_pressure.value,
                cooling_water_temp: data.sensors.cooling_water_temp.value,
                turbocharger_speed: data.sensors.turbocharger_speed.value
              };
              
              return {
                ...prevData,
                history: updatedHistory
              };
            });
          }
        } catch (error) {
          console.error('Error processing message:', error);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      // Attempt to reconnect after delay
      reconnectTimeout.current = setTimeout(() => {
        connectWebSocket();
      }, RECONNECT_DELAY);
    }
  }, []);

  // Cleanup on component unmount
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connectWebSocket]);

  const sendCommand = useCallback((command, data = {}) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        console.log('Sending command:', command);
        wsRef.current.send(JSON.stringify({ command, ...data }));
      } catch (error) {
        console.error('Error sending command:', error);
        connectWebSocket();
      }
    } else {
      console.warn('WebSocket not connected, reconnecting...');
      connectWebSocket();
    }
  }, [connectWebSocket]);

  const getStatusColor = (status) => {
    switch (status) {
      case 0: return 'grey';
      case 1: return 'green';
      case 2: return 'orange';
      case 3: return 'red';
      default: return 'grey';
    }
  };

  // Helper function for gauge colors
  const getGaugeColors = (value, warning, critical) => {
    if (value < warning) return ["#4caf50", "#ff9800"]; // Green to Orange
    if (value < critical) return ["#ff9800", "#f44336"]; // Orange to Red
    return ["#f44336"]; // Red
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  // Add SensorGauge component
  const SensorGauge = memo(({ label, value, config }) => {
    const normalizedValue = ((value - config.min) / (config.max - config.min)) * 100;
    
    let color = '#4caf50'; // Green
    if (value >= config.critical) {
      color = '#f44336'; // Red
    } else if (value >= config.warning) {
      color = '#ff9800'; // Orange
    }

    return (
      <Box sx={{ width: '100%', mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2">{label}</Typography>
          <Typography variant="body2" color="textSecondary">
            {value.toFixed(1)} {config.unit}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={normalizedValue}
          sx={{
            height: 10,
            borderRadius: 5,
            backgroundColor: '#e0e0e0',
            '& .MuiLinearProgress-bar': {
              backgroundColor: color,
              borderRadius: 5
            }
          }}
        />
      </Box>
    );
  });

  return (
    <ThemeProvider theme={darkTheme}>
      <Box sx={{ 
        minHeight: '100vh',
        backgroundColor: '#1a1a1a',
        pt: 2
      }}>
        <AppBar position="static" color="transparent" elevation={0} sx={{ borderBottom: '1px solid #404040', mb: 3 }}>
          <Toolbar>
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              width: '100%'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <img 
                  src={logo}
                  alt="Engine Control System Logo" 
                  style={{ 
                    height: '40px',
                    width: 'auto',
                    marginRight: '16px',
                    filter: 'brightness(1.2)'
                  }} 
                />
                <Typography variant="h5" sx={{ color: '#00ff00', fontWeight: 600 }}>
                  MAIN ENGINE CONTROL SYSTEM
                </Typography>
              </Box>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 2,
                '& .status-indicator': {
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  marginRight: 1
                }
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mr: 4 }}>
                  <Box 
                    className="status-indicator"
                    sx={{ 
                      backgroundColor: engineData.status === 1 ? '#00ff00' : '#ff0000',
                      boxShadow: engineData.status === 1 ? '0 0 10px #00ff00' : '0 0 10px #ff0000'
                    }} 
                  />
                  <Typography variant="body2" sx={{ color: engineData.status === 1 ? '#00ff00' : '#ff0000' }}>
                    {engineData.status === 1 ? 'ENGINE RUNNING' : 'ENGINE STOPPED'}
                  </Typography>
                </Box>
                <Button 
                  variant="contained" 
                  color={engineData.status === 1 ? "error" : "primary"}
                  size="large"
                  onClick={() => sendCommand(engineData.status === 1 ? 'stop_engine' : 'start_engine')}
                  sx={{ 
                    minWidth: 150,
                    height: 48,
                    fontSize: '1rem'
                  }}
                >
                  {engineData.status === 1 ? 'EMERGENCY STOP' : 'START ENGINE'}
                </Button>
              </Box>
            </Box>
          </Toolbar>
        </AppBar>

        <Container maxWidth="xl">
          <Grid container spacing={3}>
            {/* Main Engine Status Panel */}
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardHeader 
                  title={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Typography variant="h6">ENGINE STATUS</Typography>
                      <Box 
                        sx={{ 
                          width: 10, 
                          height: 10, 
                          borderRadius: '50%',
                          backgroundColor: engineData.status === 1 ? '#00ff00' : '#ff0000',
                          boxShadow: engineData.status === 1 ? '0 0 10px #00ff00' : '0 0 10px #ff0000'
                        }} 
                      />
                    </Box>
                  }
                />
                <CardContent>
                  <Box sx={{ mb: 4 }}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      OPERATION MODE
                    </Typography>
                    <Typography variant="h6" sx={{ color: '#00ff00' }}>
                      {plcData.mode}
                    </Typography>
                  </Box>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Box sx={{ textAlign: 'center', mb: 1 }}>
                        <Typography variant="h6" sx={{ color: 'textSecondary' }}>ENGINE RPM</Typography>
                      </Box>
                      <AnimatedGauge
                        id="rpm-gauge"
                        value={engineData.rpm}
                        normalizedValue={engineData.rpm / ENGINE_CONFIG.rpm_max}
                        label="RPM"
                        formatValue={(value) => `${value.toFixed(0)} RPM`}
                        colors={['#00ff00', '#ffff00', '#ff0000']}
                        textColor="#00ffff"
                        needleColor="#ffffff"
                        fontSize="28px"
                        fontWeight="bold"
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <Box sx={{ textAlign: 'center', mb: 1 }}>
                        <Typography variant="h6" sx={{ color: 'textSecondary' }}>ENGINE TEMP</Typography>
                      </Box>
                      <AnimatedGauge
                        id="temp-gauge"
                        value={engineData.temperature}
                        normalizedValue={engineData.temperature / ENGINE_CONFIG.temp_max}
                        label="TEMPERATURE"
                        formatValue={(value) => `${value.toFixed(1)}°C`}
                        colors={['#00ff00', '#ffff00', '#ff0000']}
                        textColor="#00ffff"
                        needleColor="#ffffff"
                        fontSize="28px"
                        fontWeight="bold"
                      />
                    </Grid>
                    <Grid item xs={4}>
                      <Box sx={{ textAlign: 'center', mb: 1 }}>
                        <Typography variant="h6" sx={{ color: 'textSecondary' }}>ENGINE LOAD</Typography>
                      </Box>
                      <AnimatedGauge
                        id="load-gauge"
                        value={engineData.load}
                        normalizedValue={engineData.load / 100}
                        label="LOAD"
                        formatValue={(value) => `${value.toFixed(0)}%`}
                        colors={['#00ff00', '#ffff00', '#ff0000']}
                        textColor="#00ffff"
                        needleColor="#ffffff"
                        fontSize="28px"
                        fontWeight="bold"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Performance Trends */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="PERFORMANCE TRENDS" />
                <CardContent>
                  <Box sx={{ height: 400 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={engineData.history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
                        <XAxis 
                          dataKey="time" 
                          stroke="#b0b0b0"
                          tick={{ fill: '#b0b0b0' }}
                        />
                        <YAxis 
                          yAxisId="left" 
                          stroke="#b0b0b0"
                          tick={{ fill: '#b0b0b0' }}
                        />
                        <YAxis 
                          yAxisId="right" 
                          orientation="right" 
                          stroke="#b0b0b0"
                          tick={{ fill: '#b0b0b0' }}
                        />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#2d2d2d',
                            border: '1px solid #404040',
                            borderRadius: 8
                          }}
                        />
                        <Legend />
                        <Line
                          yAxisId="left"
                          type="monotone"
                          dataKey="rpm"
                          stroke="#00ff00"
                          name="RPM"
                        />
                        <Line
                          yAxisId="left"
                          type="monotone"
                          dataKey="temperature"
                          stroke="#ff9800"
                          name="Temperature (°C)"
                        />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="load"
                          stroke="#29b6f6"
                          name="Load (%)"
                        />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="exhaust_temp"
                          stroke="#f44336"
                          name="Exhaust Temp (°C)"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Auxiliary Systems */}
            <Grid item xs={12} md={9}>
              <Card sx={{ height: '100%', minHeight: 400 }}>
                <CardHeader title="AUXILIARY SYSTEMS" />
                <CardContent>
                  <Grid container spacing={3}>
                    {Object.entries(SENSOR_CONFIG).map(([key, config]) => (
                      <Grid item xs={12} sm={6} md={3} key={key}>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" color="textSecondary" gutterBottom>
                            {key.split('_').map(word => word.toUpperCase()).join(' ')}
                          </Typography>
                          <Box sx={{ position: 'relative', height: 6, backgroundColor: '#404040', borderRadius: 3 }}>
                            <Box
                              sx={{
                                position: 'absolute',
                                height: '100%',
                                width: `${(mqttData[key].value / config.max) * 100}%`,
                                backgroundColor: mqttData[key].value >= config.critical ? '#ff0000' :
                                                  mqttData[key].value >= config.warning ? '#ffff00' : '#00ff00',
                                borderRadius: 3,
                                transition: 'all 0.3s ease'
                              }}
                            />
                          </Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                            <Typography variant="h6" sx={{ color: '#00ff00' }}>
                              {mqttData[key].value.toFixed(1)}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              {config.unit}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* System Parameters */}
            <Grid item xs={12} md={3}>
              <Card sx={{ height: '100%', minHeight: 400 }}>
                <CardHeader title="SYSTEM PARAMETERS" />
                <CardContent>
                  <Box sx={{ 
                    '& .parameter-row': {
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      mb: 2,
                      pb: 2,
                      borderBottom: '1px solid #404040'
                    }
                  }}>
                    <Box className="parameter-row">
                      <Typography color="textSecondary">FUEL FLOW</Typography>
                      <Typography sx={{ color: '#00ff00' }}>
                        {engineData.fuel_flow.toFixed(2)} t/h
                      </Typography>
                    </Box>
                    <Box className="parameter-row">
                      <Typography color="textSecondary">LUBE OIL</Typography>
                      <Typography sx={{ color: '#00ff00' }}>
                        {mqttData.lube_oil_pressure.value.toFixed(1)} bar
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Alarms and Warnings */}
            <Grid item xs={12}>
              <Card sx={{ height: '100%' }}>
                <CardHeader 
                  title="ALARMS & WARNINGS"
                  sx={{
                    '& .MuiCardHeader-title': {
                      color: plcData.alarms.length > 0 ? '#ff0000' : '#00ff00'
                    }
                  }}
                />
                <CardContent>
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    gap: 1,
                    maxHeight: 300,
                    overflowY: 'auto'
                  }}>
                    {plcData.alarms.length > 0 ? (
                      plcData.alarms.map((alarm, index) => (
                        <Alert 
                          key={index} 
                          severity="error"
                          sx={{ 
                            backgroundColor: 'rgba(255, 0, 0, 0.1)',
                            border: '1px solid #ff0000',
                            color: '#ff0000',
                            '& .MuiAlert-icon': {
                              color: '#ff0000'
                            }
                          }}
                        >
                          {alarm}
                        </Alert>
                      ))
                    ) : (
                      <Alert 
                        severity="success"
                        sx={{ 
                          backgroundColor: 'rgba(0, 255, 0, 0.1)',
                          border: '1px solid #00ff00',
                          color: '#00ff00',
                          '& .MuiAlert-icon': {
                            color: '#00ff00'
                          }
                        }}
                      >
                        NO ACTIVE ALARMS
                      </Alert>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

// Memoize the entire App component to prevent unnecessary re-renders
export default memo(App); 