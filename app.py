from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import json
from typing import Dict, Set
from datetime import datetime

from engine.simulator import MainEngineSimulator
from plc.controller import PLCController
from sensors.mqtt_sensor import MQTTSensor

# Component placeholders
simulator = None
plc = None
mqtt_sensor = None

async def broadcast_state():
    """Broadcast engine and sensor states to all connected clients"""
    while True:
        if connections:
            # Make a copy of connections set to avoid runtime error
            current_connections = connections.copy()
            
            # Modbus data
            modbus_state = {
                "type": "modbus",
                "timestamp": datetime.now().isoformat(),
                "engine": {
                    "rpm": simulator.current_rpm,
                    "temperature": simulator.current_temp,
                    "fuel_flow": simulator.current_fuel_flow,
                    "load": simulator.current_load,
                    "status": simulator.status
                },
                "plc": {
                    "mode": plc.mode,
                    "alarms": plc.alarms,
                    "setpoints": plc.setpoints
                }
            }
            
            for connection in current_connections:
                try:
                    if connection not in connections:
                        continue
                    await connection.send_json(modbus_state)
                    
                    # Only send MQTT data if sensor is available
                    if mqtt_sensor:
                        await asyncio.sleep(0.1)  # Small delay between messages
                        if connection not in connections:
                            continue
                        mqtt_state = {
                            "type": "mqtt",
                            "timestamp": datetime.now().isoformat(),
                            "sensors": mqtt_sensor.generate_sensor_data()
                        }
                        await connection.send_json(mqtt_state)
                except Exception as e:
                    print(f"Error broadcasting to client: {e}")
                    try:
                        connections.remove(connection)
                    except KeyError:
                        pass  # Connection was already removed
        
        await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    global simulator, plc, mqtt_sensor
    
    # Startup
    print("Starting up application...")
    
    # Initialize components
    simulator = MainEngineSimulator()
    plc = PLCController(simulator)
    
    # Connect simulator with PLC controller
    simulator.set_plc_controller(plc)
    
    # Start Modbus server
    simulator.start_server()
    
    try:
        # Initialize and start MQTT sensor (optional)
        mqtt_sensor = MQTTSensor()
        mqtt_sensor.start()
        # Start MQTT publisher
        asyncio.create_task(mqtt_sensor.publish_loop())
    except Exception as e:
        print(f"MQTT sensor initialization failed (non-critical): {e}")
        mqtt_sensor = None
    
    # Start state broadcaster
    asyncio.create_task(broadcast_state())
    
    yield
    
    # Shutdown
    print("Shutting down application...")
    if mqtt_sensor:
        mqtt_sensor.stop()

app = FastAPI(title="ME Simulator", lifespan=lifespan)

# Define allowed origins - Add your network IPs here
origins = [
    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    
    # Common private network ranges (192.168.x.x)
    "http://192.168.1.*:3000",
    "http://192.168.0.*:3000", 
    "http://192.168.2.*:3000",
    
    # Common private network ranges (10.x.x.x)
    "http://10.*.*.*:3000",
    
    # WebSocket connections
    "ws://localhost:8000",
    "ws://127.0.0.1:8000",
    "ws://0.0.0.0:8000",
    "ws://192.168.1.*:8000",
    "ws://192.168.0.*:8000",
    "ws://192.168.2.*:8000", 
    "ws://10.*.*.*:8000",
    
    # Backend URLs
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "http://192.168.1.*:8000",
    "http://192.168.0.*:8000",
    "http://192.168.2.*:8000",
    "http://10.*.*.*:8000"
]

# CORS middleware - Allow all origins for development/demo
# For production, replace "*" with specific origins list
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for cross-machine access
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Serve static files (React frontend)
app.mount("/static", StaticFiles(directory="frontend/build"), name="static")

# WebSocket connections store
connections: Set[WebSocket] = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client = getattr(websocket, "client", "Unknown client")
    print(f"WebSocket connection attempt from {client}")
    try:
        print("Attempting WebSocket handshake...")
        await websocket.accept()
        print(f"WebSocket connection accepted from {client}")
        connections.add(websocket)
        print(f"Added to connections pool. Active connections: {len(connections)}")
        
        while True:
            try:
                data = await websocket.receive_json()
                print(f"Received command from {client}: {data}")
                
                if "command" in data:
                    if data["command"] == "start_engine":
                        print(f"Starting engine for {client}...")
                        simulator.running = True
                        response = {
                            "type": "modbus",
                            "engine": {
                                "status": simulator.status,
                                "rpm": simulator.current_rpm,
                                "temperature": simulator.current_temp,
                                "fuel_flow": simulator.current_fuel_flow,
                                "load": simulator.current_load
                            }
                        }
                        print(f"Sending response to {client}: {response}")
                        await websocket.send_json(response)
                    elif data["command"] == "stop_engine":
                        print(f"Stopping engine for {client}...")
                        simulator.running = False
                        response = {
                            "status": "ok",
                            "command": "stop_engine",
                            "engine_status": simulator.status
                        }
                        print(f"Sending response to {client}: {response}")
                        await websocket.send_json(response)
                    elif data["command"] == "set_mode":
                        print(f"Setting mode for {client}: {data['mode']}")
                        plc.set_mode(data["mode"])
                    elif data["command"] == "set_setpoint":
                        print(f"Setting setpoint for {client}: {data['parameter']} = {data['value']}")
                        plc.set_setpoint(data["parameter"], data["value"])
                    
                    # Send acknowledgment
                    ack = {"status": "ok", "command": data["command"]}
                    print(f"Sending acknowledgment to {client}: {ack}")
                    await websocket.send_json(ack)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON received from {client}: {e}")
                continue
            except Exception as e:
                print(f"Error processing WebSocket message from {client}: {e}")
                if websocket in connections:
                    connections.remove(websocket)
                break
    except WebSocketDisconnect:
        print(f"WebSocket client {client} disconnected normally")
    except Exception as e:
        print(f"WebSocket error with {client}: {e}")
    finally:
        if websocket in connections:
            connections.remove(websocket)
        print(f"WebSocket connection closed for {client}. Active connections: {len(connections)}")

@app.get("/api/status")
async def get_status():
    """Get current status of all components"""
    return {
        "engine": {
            "rpm": simulator.current_rpm,
            "temperature": simulator.current_temp,
            "fuel_flow": simulator.current_fuel_flow,
            "load": simulator.current_load,
            "status": simulator.status
        },
        "plc": {
            "mode": plc.mode,
            "alarms": plc.alarms,
            "setpoints": plc.setpoints
        },
        "mqtt_sensors": mqtt_sensor.generate_sensor_data() if mqtt_sensor else {}
    }

@app.get("/api/settings")
async def get_settings():
    """Get current system settings"""
    return {
        "engine": simulator.config.get('engine', {}),
        "modbus": simulator.config.get('modbus', {}),
        "registers": simulator.config.get('registers', {})
    }

@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update system settings"""
    try:
        # Update engine configuration if provided
        if 'engine' in settings:
            engine_settings = settings['engine']
            for key, value in engine_settings.items():
                if key in simulator.config['engine']:
                    simulator.config['engine'][key] = value
                    print(f"Updated engine setting: {key} = {value}")
        
        # Update modbus configuration if provided
        if 'modbus' in settings:
            modbus_settings = settings['modbus']
            for key, value in modbus_settings.items():
                if key in simulator.config['modbus']:
                    simulator.config['modbus'][key] = value
                    print(f"Updated modbus setting: {key} = {value}")
        
        # Save updated config to file
        import yaml
        from pathlib import Path
        config_file = Path(__file__).parent / 'config.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(simulator.config, f, default_flow_style=False)
        
        return {"status": "success", "message": "Settings updated successfully"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import asyncio
    
    async def main():
        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()

    # Run the async main function
    asyncio.run(main()) 