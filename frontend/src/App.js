import React, { useState, useEffect, useRef, useCallback, useMemo, memo } from 'react';
import { 
  Container, Grid, Paper, Typography, Button, 
  Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Alert, Tab, Tabs, Box,
  Card, CardContent, CardHeader, Divider
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import GaugeChart from 'react-gauge-chart';

const WEBSOCKET_URL = 'ws://localhost:8000/ws';

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

// Create a custom animated gauge component
const AnimatedGauge = memo(({ id, value, normalizedValue, label, formatValue, colors }) => {
  const [animatedValue, setAnimatedValue] = useState(0);
  const prevValueRef = useRef(normalizedValue);
  const animationFrameRef = useRef();

  useEffect(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    const startValue = prevValueRef.current;
    const endValue = normalizedValue;
    const duration = 1000;
    const startTime = performance.now();

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const easeProgress = progress < 0.5
        ? 4 * progress * progress * progress
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;

      const currentValue = startValue + (endValue - startValue) * easeProgress;
      setAnimatedValue(currentValue);

      if (progress < 1) {
        animationFrameRef.current = requestAnimationFrame(animate);
      } else {
        prevValueRef.current = endValue;
      }
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [normalizedValue]);

  return (
    <Card sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      minHeight: '250px', // Add fixed minimum height
      position: 'relative' // Add relative positioning
    }}>
      <CardContent sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        padding: '16px !important' // Override default padding
      }}>
        <Typography 
          color="textSecondary" 
          gutterBottom
          sx={{ mb: 1 }}
        >
          {label}
        </Typography>
        <Box sx={{ 
          flex: 1,
          position: 'relative',
          '& > div': { // Target the gauge chart container
            position: 'absolute !important',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
          }
        }}>
          <GaugeChart
            id={id}
            nrOfLevels={20}
            percent={animatedValue}
            colors={colors}
            arcWidth={0.3}
            textColor="#000000"
            formatTextValue={() => formatValue(value)}
            cornerRadius={3}
            marginInPercent={0.02}
            animate={false}
          />
        </Box>
      </CardContent>
    </Card>
  );
});

function App() {
  const [tabValue, setTabValue] = useState(0);
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

    const ws = new WebSocket(WEBSOCKET_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to server');
      setWsConnected(true);
    };

    ws.onclose = () => {
      console.log('Disconnected from server');
      setWsConnected(false);
      // Add delay before reconnecting to prevent rapid reconnection attempts
      setTimeout(() => {
        connectWebSocket();
      }, 2000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'modbus') {
          setEngineData(prevData => {
            const newHistoryPoint = {
              time: new Date().toLocaleTimeString(),
              ...data.engine,
              // Add the latest MQTT values to the history point
              exhaust_temp: mqttData.exhaust_temp.value,
              lube_oil_pressure: mqttData.lube_oil_pressure.value,
              cooling_water_temp: mqttData.cooling_water_temp.value,
              turbocharger_speed: mqttData.turbocharger_speed.value
            };
            
            return {
              ...prevData,
              rpm: data.engine.rpm,
              temperature: data.engine.temperature,
              fuel_flow: data.engine.fuel_flow,
              load: data.engine.load,
              status: data.engine.status,
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
          
          // Update the last history point with new MQTT data
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
  }, []);

  // Cleanup on component unmount
  useEffect(() => {
    connectWebSocket();
    return () => {
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

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Main Control Panel */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardHeader 
              title="Engine Control Panel"
              action={
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button 
                    variant="contained" 
                    color="success"
                    onClick={() => {
                      console.log('Start button clicked');
                      sendCommand('start_engine');
                    }}
                    disabled={engineData.status === 1}
                  >
                    Start Engine ({engineData.status === 1 ? 'Running' : 'Stopped'})
                  </Button>
                  <Button 
                    variant="contained" 
                    color="error"
                    onClick={() => sendCommand('stop_engine')}
                    disabled={engineData.status === 0}
                  >
                    Stop Engine
                  </Button>
                </Box>
              }
            />
            <Divider />
            <CardContent>
              <Grid container spacing={3}>
                {/* Engine Status Cards with Gauges */}
                <Grid item xs={12} md={3}>
                  <AnimatedGauge
                    id="rpm-gauge"
                    value={engineData.rpm}
                    normalizedValue={engineData.rpm / ENGINE_CONFIG.rpm_max}
                    label="RPM"
                    formatValue={v => v.toFixed(0)}
                    colors={["#00FF00", "#FF0000"]}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <AnimatedGauge
                    id="temp-gauge"
                    value={engineData.temperature}
                    normalizedValue={(engineData.temperature - ENGINE_CONFIG.temp_min) / 
                                   (ENGINE_CONFIG.temp_max - ENGINE_CONFIG.temp_min)}
                    label="Temperature"
                    formatValue={v => `${v.toFixed(1)}°C`}
                    colors={getGaugeColors(engineData.temperature, {
                      warning: ENGINE_CONFIG.temp_warning,
                      critical: ENGINE_CONFIG.temp_critical
                    })}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <AnimatedGauge
                    id="fuel-gauge"
                    value={engineData.fuel_flow}
                    normalizedValue={engineData.fuel_flow / ENGINE_CONFIG.fuel_flow_max}
                    label="Fuel Flow"
                    formatValue={v => `${v.toFixed(2)} t/h`}
                    colors={["#00FF00", "#FF0000"]}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <AnimatedGauge
                    id="load-gauge"
                    value={engineData.load}
                    normalizedValue={engineData.load / 100}
                    label="Load"
                    formatValue={v => `${v.toFixed(0)}%`}
                    colors={getGaugeColors(engineData.load, {
                      warning: ENGINE_CONFIG.load_warning,
                      critical: ENGINE_CONFIG.load_critical
                    })}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Trend Charts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Engine Performance" />
            <Divider />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={engineData.history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="rpm" 
                    stroke="#8884d8" 
                    dot={false}
                    name="RPM"
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="load" 
                    stroke="#82ca9d" 
                    dot={false}
                    name="Load %"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Temperature Monitoring" />
            <Divider />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={engineData.history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 'auto']} />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="temperature" 
                    stroke="#ff7300" 
                    dot={false}
                    name="Engine Temp"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="exhaust_temp" 
                    stroke="#ff0000" 
                    dot={false}
                    name="Exhaust Temp"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* MQTT Sensors Panel */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="MQTT Sensor Data" />
            <Divider />
            <CardContent>
              <Grid container spacing={3}>
                {Object.entries(mqttData).map(([sensor, data]) => (
                  <Grid item xs={12} md={3} key={sensor}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom>
                          {sensor.replace(/_/g, ' ').toUpperCase()}
                        </Typography>
                        <Typography variant="h4">
                          {data.value.toFixed(2)} {data.unit}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Alarms Panel */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Alarms and Warnings" />
            <Divider />
            <CardContent>
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
    </Container>
  );
}

// Memoize the entire App component to prevent unnecessary re-renders
export default memo(App); 