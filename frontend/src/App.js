import React, { useState, useEffect, useRef, useCallback, useMemo, memo } from 'react';
import { 
  Container, Grid, Paper, Typography, Button, 
  Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Alert, Tab, Tabs, Box,
  Card, CardContent, CardHeader, Divider,
  AppBar, Toolbar
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import GaugeChart from 'react-gauge-chart';
import AnimatedGauge from './components/AnimatedGauge';
import TopologyView from './components/TopologyView';

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
  const getGaugeColors = (value, { warning, critical }) => {
    if (value < warning) return ["#00FF00", "#FFA500"];
    if (value < critical) return ["#FFA500", "#FF0000"];
    return ["#FF0000"];
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  return (
    <Box sx={{ 
      minHeight: '100vh',
      backgroundColor: '#f5f7fa'
    }}>
      <AppBar position="static" color="default" elevation={0} sx={{ backgroundColor: 'white', borderBottom: '1px solid #e0e0e0' }}>
        <Toolbar>
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            width: '100%'
          }}>
            <img 
              src="/resources/logo.png" 
              alt="SEACURE Logo" 
              style={{
                height: '40px',
                objectFit: 'contain'
              }}
            />
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Button 
                variant="contained" 
                color="success"
                size="large"
                onClick={() => sendCommand('start_engine')}
                disabled={engineData.status === 1}
                sx={{ 
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 3
                }}
              >
                {engineData.status === 1 ? 'Engine Running' : 'Start Engine'}
              </Button>
              <Button 
                variant="contained" 
                color="error"
                size="large"
                onClick={() => sendCommand('stop_engine')}
                disabled={engineData.status === 0}
                sx={{ 
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 3
                }}
              >
                Stop Engine
              </Button>
            </Box>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ 
          borderRadius: 2,
          backgroundColor: 'white',
          mb: 3,
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <Tabs 
            value={currentTab} 
            onChange={handleTabChange}
            sx={{ 
              '& .MuiTab-root': {
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 500,
                minHeight: 56
              }
            }}
          >
            <Tab label="Dashboard" />
            <Tab label="Topology View" />
          </Tabs>
        </Box>

        {currentTab === 0 ? (
          <Grid container spacing={3}>
            {/* Gauges Section */}
            <Grid item xs={12}>
              <Grid container spacing={3}>
                {[
                  {
                    id: "rpm-gauge",
                    value: engineData.rpm,
                    normalizedValue: engineData.rpm / ENGINE_CONFIG.rpm_max,
                    label: "Engine RPM",
                    format: v => v.toFixed(0),
                    colors: ["#00FF00", "#FF0000"]
                  },
                  {
                    id: "temp-gauge",
                    value: engineData.temperature,
                    normalizedValue: (engineData.temperature - ENGINE_CONFIG.temp_min) / 
                                   (ENGINE_CONFIG.temp_max - ENGINE_CONFIG.temp_min),
                    label: "Temperature",
                    format: v => `${v.toFixed(1)}°C`,
                    colors: getGaugeColors(engineData.temperature, {
                      warning: ENGINE_CONFIG.temp_warning,
                      critical: ENGINE_CONFIG.temp_critical
                    })
                  },
                  {
                    id: "fuel-gauge",
                    value: engineData.fuel_flow,
                    normalizedValue: engineData.fuel_flow / ENGINE_CONFIG.fuel_flow_max,
                    label: "Fuel Flow",
                    format: v => `${v.toFixed(2)} t/h`,
                    colors: ["#00FF00", "#FF0000"]
                  },
                  {
                    id: "load-gauge",
                    value: engineData.load,
                    normalizedValue: engineData.load / 100,
                    label: "Engine Load",
                    format: v => `${v.toFixed(0)}%`,
                    colors: getGaugeColors(engineData.load, {
                      warning: ENGINE_CONFIG.load_warning,
                      critical: ENGINE_CONFIG.load_critical
                    })
                  }
                ].map(gauge => (
                  <Grid item xs={12} md={3} key={gauge.id}>
                    <Card sx={{ 
                      borderRadius: 2,
                      boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                      height: '100%'
                    }}>
                      <CardContent sx={{
                        height: 280,
                        display: 'flex',
                        flexDirection: 'column'
                      }}>
                        <Typography 
                          variant="h6" 
                          gutterBottom 
                          sx={{ 
                            fontWeight: 500,
                            mb: 2
                          }}
                        >
                          {gauge.label}
                        </Typography>
                        <Box sx={{ 
                          flex: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          minHeight: 200
                        }}>
                          <AnimatedGauge
                            id={gauge.id}
                            value={gauge.value}
                            normalizedValue={gauge.normalizedValue}
                            label={gauge.label}
                            formatValue={gauge.format}
                            colors={gauge.colors}
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Grid>

            {/* Charts Section */}
            <Grid item xs={12} md={6}>
              <Card sx={{ 
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
              }}>
                <CardHeader 
                  title={
                    <Typography variant="h6" sx={{ fontWeight: 500 }}>
                      Engine Performance
                    </Typography>
                  }
                />
                <Divider />
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={engineData.history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="time" stroke="#666" />
                      <YAxis yAxisId="left" stroke="#8884d8" />
                      <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: 'none',
                          borderRadius: 8,
                          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                        }}
                      />
                      <Legend />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="rpm" 
                        stroke="#8884d8" 
                        dot={false}
                        name="RPM"
                        strokeWidth={2}
                      />
                      <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="load" 
                        stroke="#82ca9d" 
                        dot={false}
                        name="Load %"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card sx={{ 
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
              }}>
                <CardHeader 
                  title={
                    <Typography variant="h6" sx={{ fontWeight: 500 }}>
                      Temperature Monitoring
                    </Typography>
                  }
                />
                <Divider />
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={engineData.history}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="time" stroke="#666" />
                      <YAxis domain={[0, 'auto']} stroke="#666" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: 'none',
                          borderRadius: 8,
                          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                        }}
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="temperature" 
                        stroke="#ff7300" 
                        dot={false}
                        name="Engine Temp"
                        strokeWidth={2}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="exhaust_temp" 
                        stroke="#ff0000" 
                        dot={false}
                        name="Exhaust Temp"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            {/* MQTT Sensors Panel */}
            <Grid item xs={12}>
              <Card sx={{ 
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
              }}>
                <CardHeader 
                  title={
                    <Typography variant="h6" sx={{ fontWeight: 500 }}>
                      Sensor Data
                    </Typography>
                  }
                />
                <Divider />
                <CardContent>
                  <Grid container spacing={3}>
                    {Object.entries(mqttData).map(([sensor, data]) => (
                      <Grid item xs={12} md={3} key={sensor}>
                        <Paper 
                          elevation={0} 
                          sx={{ 
                            p: 2, 
                            borderRadius: 2,
                            backgroundColor: '#f8f9fa',
                            height: '100%'
                          }}
                        >
                          <Typography 
                            color="textSecondary" 
                            gutterBottom
                            sx={{ 
                              fontSize: '0.875rem',
                              textTransform: 'uppercase',
                              letterSpacing: '0.1em'
                            }}
                          >
                            {sensor.replace(/_/g, ' ')}
                          </Typography>
                          <Typography 
                            variant="h4" 
                            sx={{ 
                              fontWeight: 500,
                              color: '#1a1a1a'
                            }}
                          >
                            {data.value.toFixed(2)}
                            <Typography 
                              component="span" 
                              sx={{ 
                                fontSize: '1rem',
                                color: '#666',
                                ml: 1
                              }}
                            >
                              {data.unit}
                            </Typography>
                          </Typography>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Alarms Panel */}
            <Grid item xs={12}>
              <Card sx={{ 
                borderRadius: 2,
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
              }}>
                <CardHeader 
                  title={
                    <Typography variant="h6" sx={{ fontWeight: 500 }}>
                      System Alerts
                    </Typography>
                  }
                />
                <Divider />
                <CardContent>
                  {plcData.alarms.length > 0 ? (
                    plcData.alarms.map((alarm, index) => (
                      <Alert 
                        severity="error" 
                        key={index} 
                        sx={{ 
                          mb: 1,
                          borderRadius: 1
                        }}
                      >
                        {alarm}
                      </Alert>
                    ))
                  ) : (
                    <Alert 
                      severity="success"
                      sx={{ borderRadius: 1 }}
                    >
                      All systems operating normally
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        ) : (
          <TopologyView
            engineData={engineData}
            mqttData={mqttData}
            plcData={plcData}
          />
        )}
      </Container>
    </Box>
  );
}

// Memoize the entire App component to prevent unnecessary re-renders
export default memo(App); 