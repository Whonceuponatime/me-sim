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
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import SecurityIcon from '@mui/icons-material/Security';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import SpeedIcon from '@mui/icons-material/Speed';
import ThermostatIcon from '@mui/icons-material/Thermostat';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

// Dynamic WebSocket URL configuration
const getWebSocketURL = async () => {
  try {
    // First, try to load from remote_settings.json
    const response = await fetch('/remote_settings.json');
    if (response.ok) {
      const settings = await response.json();
      if (settings.websocketUrl) {
        console.log('Using WebSocket URL from remote_settings.json:', settings.websocketUrl);
        return settings.websocketUrl;
      }
    }
  } catch (error) {
    console.log('Could not load remote_settings.json, using dynamic detection');
  }

  // Fallback: Detect current host and construct WebSocket URL
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.hostname;
  const port = 8000; // Backend port
  
  // If we're on localhost, try the local backend
  if (host === 'localhost' || host === '127.0.0.1') {
    return `${protocol}//${host}:${port}/ws`;
  }
  
  // For other hosts, assume backend is on the same host
  return `${protocol}//${host}:${port}/ws`;
};

// Get API configuration for REST API mode
const getAPIConfig = async () => {
  try {
    const response = await fetch('/remote_settings.json');
    if (response.ok) {
      const settings = await response.json();
      return {
        apiBaseUrl: settings.apiBaseUrl,
        dataUpdateInterval: settings.dataUpdateInterval || 2000,
        useRestAPI: settings.deployment?.dataSource === 'rest_api' || settings.websocketUrl === null
      };
    }
  } catch (error) {
    console.log('Could not load API config from remote_settings.json');
  }
  
  return {
    apiBaseUrl: null,
    dataUpdateInterval: 2000,
    useRestAPI: false
  };
};

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
  const [apiConnected, setApiConnected] = useState(false);
  const [useRestAPI, setUseRestAPI] = useState(false);
  const [apiConfig, setApiConfig] = useState({ apiBaseUrl: null, dataUpdateInterval: 2000 });
  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef(null);
  const apiPollingRef = useRef(null);

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

  // REST API functions for bridge mode (moved before useEffect)
  const fetchEngineData = useCallback(async () => {
    if (!apiConfig.apiBaseUrl) return;

    try {
      const response = await fetch(`${apiConfig.apiBaseUrl}/status`);
      if (response.ok) {
        const data = await response.json();
        console.log('API data received:', data);
        
        setApiConnected(true);
        
        if (data.engine) {
          setEngineData(prevData => {
            const newHistoryPoint = {
              time: new Date().toLocaleTimeString(),
              status: data.engine.status || 0,
              rpm: data.engine.rpm || 0,
              temperature: data.engine.temp || 0,
              fuel_flow: data.engine.fuel_flow || 0,
              load: data.engine.load || 0,
              exhaust_temp: 0,
              lube_oil_pressure: 0,
              cooling_water_temp: 0,
              turbocharger_speed: 0
            };
            
            return {
              rpm: data.engine.rpm || 0,
              temperature: data.engine.temp || 0,
              fuel_flow: data.engine.fuel_flow || 0,
              load: data.engine.load || 0,
              status: data.engine.status || 0,
              history: [...(prevData.history || []), newHistoryPoint].slice(-50)
            };
          });
        }
      } else {
        console.error('API request failed:', response.status);
        setApiConnected(false);
      }
    } catch (error) {
      console.error('Error fetching engine data:', error);
      setApiConnected(false);
    }
  }, [apiConfig.apiBaseUrl]);

  const sendAPICommand = useCallback(async (command, data = {}) => {
    if (!apiConfig.apiBaseUrl) {
      console.error('API base URL not configured');
      return;
    }

    try {
      let endpoint;
      let method = 'POST';
      
      switch (command) {
        case 'start_engine':
          endpoint = `${apiConfig.apiBaseUrl}/engine/start`;
          break;
        case 'stop_engine':
          endpoint = `${apiConfig.apiBaseUrl}/engine/stop`;
          break;
        default:
          console.warn('Unknown command:', command);
          return;
      }

      const response = await fetch(endpoint, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Command sent successfully:', result);
        // Fetch updated data immediately
        setTimeout(fetchEngineData, 500);
      } else {
        console.error('Command failed:', response.status);
      }
    } catch (error) {
      console.error('Error sending command:', error);
    }
  }, [apiConfig.apiBaseUrl, fetchEngineData]);

  const connectWebSocket = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const websocketUrl = await getWebSocketURL();
      console.log('Attempting to connect to WebSocket:', websocketUrl);
      const ws = new WebSocket(websocketUrl);
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
          reconnectTimeout.current = setTimeout(async () => {
            reconnectAttempts.current += 1;
            await connectWebSocket();
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
      reconnectTimeout.current = setTimeout(async () => {
        await connectWebSocket();
      }, RECONNECT_DELAY);
    }
  }, []);

  // Initialize connection based on configuration
  useEffect(() => {
    const initConnection = async () => {
      try {
        // Get API configuration
        const config = await getAPIConfig();
        console.log('Configuration loaded:', config);
        
        setApiConfig(config);
        setUseRestAPI(config.useRestAPI);
        
        if (config.useRestAPI && config.apiBaseUrl) {
          console.log('Using REST API mode');
          setWsConnected(false);
          // Start API polling after a short delay to ensure state is updated
          setTimeout(() => {
            const fetchData = async () => {
              try {
                const response = await fetch(`${config.apiBaseUrl}/status`);
                if (response.ok) {
                  const data = await response.json();
                  console.log('Initial API data received:', data);
                  setApiConnected(true);
                  
                  if (data.engine) {
                    setEngineData({
                      rpm: data.engine.rpm || 0,
                      temperature: data.engine.temp || 0,
                      fuel_flow: data.engine.fuel_flow || 0,
                      load: data.engine.load || 0,
                      status: data.engine.status || 0,
                      history: []
                    });
                  }
                } else {
                  setApiConnected(false);
                }
              } catch (error) {
                console.error('Error fetching initial data:', error);
                setApiConnected(false);
              }
            };

            // Fetch initial data
            fetchData();
            
            // Set up polling
            const pollingInterval = setInterval(fetchData, config.dataUpdateInterval);
            apiPollingRef.current = pollingInterval;
          }, 1000);
        } else {
          console.log('Using WebSocket mode');
          setApiConnected(false);
      await connectWebSocket();
        }
      } catch (error) {
        console.error('Failed to initialize connection:', error);
        // Fallback to WebSocket mode
        setUseRestAPI(false);
        await connectWebSocket();
      }
    };

    initConnection();

    // Cleanup function
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (apiPollingRef.current) {
        clearInterval(apiPollingRef.current);
        apiPollingRef.current = null;
      }
    };
  }, [connectWebSocket]);

  const startAPIPolling = useCallback(() => {
    if (apiPollingRef.current) {
      clearInterval(apiPollingRef.current);
    }
    
    if (!apiConfig.apiBaseUrl) {
      console.warn('Cannot start API polling: no API base URL configured');
      return;
    }
    
    // Start polling immediately
    fetchEngineData();
    
    // Set up polling interval
    apiPollingRef.current = setInterval(() => {
      fetchEngineData();
    }, apiConfig.dataUpdateInterval || 2000);
    
    console.log(`Started API polling every ${apiConfig.dataUpdateInterval || 2000}ms`);
  }, [fetchEngineData, apiConfig.apiBaseUrl, apiConfig.dataUpdateInterval]);

  const stopAPIPolling = useCallback(() => {
    if (apiPollingRef.current) {
      clearInterval(apiPollingRef.current);
      apiPollingRef.current = null;
      console.log('Stopped API polling');
    }
  }, []);

  const sendCommand = useCallback((command, data = {}) => {
    if (useRestAPI) {
      sendAPICommand(command, data);
    } else {
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
    }
  }, [useRestAPI, sendAPICommand, connectWebSocket]);

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

  // Add alarm icon mapping
  const getAlarmIcon = (alarm) => {
    const alarmLower = alarm.toLowerCase();
    if (alarmLower.includes('security') || alarmLower.includes('unauthorized')) {
      return <SecurityIcon />;
    } else if (alarmLower.includes('emergency') || alarmLower.includes('critical')) {
      return <ErrorIcon />;
    } else if (alarmLower.includes('warning')) {
      return <WarningIcon />;
    } else if (alarmLower.includes('power') || alarmLower.includes('engine')) {
      return <PowerSettingsNewIcon />;
    } else if (alarmLower.includes('speed') || alarmLower.includes('rpm')) {
      return <SpeedIcon />;
    } else if (alarmLower.includes('temp') || alarmLower.includes('temperature')) {
      return <ThermostatIcon />;
    } else {
      return <WarningIcon />;
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
    <Box sx={{ 
      minHeight: '100vh',
        backgroundColor: '#1a1a1a',
        pt: 2
    }}>
        <AppBar position="static" sx={{ backgroundColor: '#1a1a1a', mb: 3 }}>
        <Toolbar>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
              <img src={logo} alt="Engine Control System Logo" style={{ height: 40 }} />
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                Engine Control System
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mr: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box 
                    className="status-indicator"
                    sx={{ 
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: engineData.status === 1 ? '#00ff00' : '#ff0000',
                      boxShadow: engineData.status === 1 ? '0 0 10px #00ff00' : '0 0 10px #ff0000',
                      mr: 1
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
              <Tabs value={currentTab} onChange={handleTabChange} textColor="inherit">
                <Tab label="Dashboard" />
                <Tab label="Topology" />
                <Tab label="Trends" />
              </Tabs>
          </Box>
        </Toolbar>
      </AppBar>

        {(!wsConnected && !useRestAPI) && (
          <Alert severity="error" sx={{ mb: 3 }}>
            WebSocket connection lost. Attempting to reconnect...
          </Alert>
        )}

        {(!apiConnected && useRestAPI) && (
          <Alert severity="error" sx={{ mb: 3 }}>
            API connection failed. Check if bridge service is running.
          </Alert>
        )}

        {(useRestAPI && apiConnected) && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Connected to MODBUS bridge API
          </Alert>
        )}

        <Container maxWidth="xl">
          {currentTab === 0 && (
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

                    {/* Engine Status Alarms */}
                    <Box sx={{ mt: 4 }}>
                      <Box sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 1, 
                        mb: 2,
                        borderBottom: '1px solid #404040',
                        pb: 1
                      }}>
                        {plcData.alarms.length > 0 ? 
                          <ErrorIcon sx={{ color: '#ff0000' }} /> : 
                          <CheckCircleIcon sx={{ color: '#00ff00' }} />
                        }
                        <Typography variant="subtitle1" sx={{ 
                          color: plcData.alarms.length > 0 ? '#ff0000' : '#00ff00',
                          fontWeight: 500
                        }}>
                          ENGINE ALARMS
                        </Typography>
                      </Box>
                      <Box sx={{ 
                        display: 'flex',
                        flexDirection: 'column', 
                        gap: 1,
                        maxHeight: 150,
                        overflowY: 'auto'
                      }}>
                        {plcData.alarms.length > 0 ? (
                          plcData.alarms.slice(0, 3).map((alarm, index) => (
                            <Box
                              key={index}
                              sx={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 1,
                                p: 1,
                                backgroundColor: 'rgba(255, 0, 0, 0.1)',
                                border: '1px solid #ff0000',
                                borderRadius: 1
                              }}
                            >
                              {getAlarmIcon(alarm)}
                        <Typography 
                                variant="body2" 
                          sx={{ 
                                  color: '#ff0000',
                            fontWeight: 500,
                                  flex: 1
                          }}
                        >
                                {alarm}
                        </Typography>
                            </Box>
                          ))
                        ) : (
                          <Box
                            sx={{
                          display: 'flex',
                          alignItems: 'center',
                              gap: 1,
                              p: 1,
                              backgroundColor: 'rgba(0, 255, 0, 0.1)',
                              border: '1px solid #00ff00',
                              borderRadius: 1
                            }}
                          >
                            <CheckCircleIcon sx={{ color: '#00ff00' }} />
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                color: '#00ff00',
                                fontWeight: 500
                              }}
                            >
                              NO ACTIVE ALARMS
                            </Typography>
                          </Box>
                        )}
                        {plcData.alarms.length > 3 && (
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              color: '#ff0000',
                              textAlign: 'center',
                              mt: 1
                            }}
                          >
                            +{plcData.alarms.length - 3} more alarms
                          </Typography>
                        )}
                      </Box>
                        </Box>
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
                  title={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {plcData.alarms.length > 0 ? <ErrorIcon sx={{ color: '#ff0000' }} /> : <CheckCircleIcon sx={{ color: '#00ff00' }} />}
                        <Typography variant="h6" sx={{ color: plcData.alarms.length > 0 ? '#ff0000' : '#00ff00' }}>
                          ALARMS & WARNINGS
                    </Typography>
                      </Box>
                  }
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
                            icon={getAlarmIcon(alarm)}
                        severity="error" 
                        sx={{ 
                              backgroundColor: 'rgba(255, 0, 0, 0.1)',
                              border: '1px solid #ff0000',
                              color: '#ff0000',
                              '& .MuiAlert-icon': {
                                color: '#ff0000',
                                fontSize: '1.5rem'
                              },
                              display: 'flex',
                              alignItems: 'center',
                              py: 1
                            }}
                          >
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {alarm}
                            </Typography>
                      </Alert>
                    ))
                  ) : (
                    <Alert 
                          icon={<CheckCircleIcon />}
                      severity="success"
                          sx={{ 
                            backgroundColor: 'rgba(0, 255, 0, 0.1)',
                            border: '1px solid #00ff00',
                            color: '#00ff00',
                            '& .MuiAlert-icon': {
                              color: '#00ff00',
                              fontSize: '1.5rem'
                            },
                            display: 'flex',
                            alignItems: 'center',
                            py: 1
                          }}
                        >
                          <Typography variant="body1" sx={{ fontWeight: 500 }}>
                            NO ACTIVE ALARMS
                          </Typography>
                    </Alert>
                  )}
                    </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          )}
          
          {currentTab === 1 && (
          <TopologyView
            engineData={engineData}
            mqttData={mqttData}
            plcData={plcData}
          />
        )}
          
          {currentTab === 2 && (
            // Trends content
            <Grid container spacing={3}>
              {/* ... existing trends content ... */}
            </Grid>
          )}
      </Container>
    </Box>
    </ThemeProvider>
  );
}

// Memoize the entire App component to prevent unnecessary re-renders
export default memo(App); 