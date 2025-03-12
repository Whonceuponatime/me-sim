from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from typing import Dict, Set
from datetime import datetime

from engine.simulator import MainEngineSimulator
from plc.controller import PLCController
from sensors.mqtt_sensor import MQTTSensor

app = FastAPI(title="ME Simulator")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (React frontend)
app.mount("/static", StaticFiles(directory="frontend/build"), name="static")

# WebSocket connections store
connections: Set[WebSocket] = set()

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
            
            # MQTT sensor data
            mqtt_state = {
                "type": "mqtt",
                "timestamp": datetime.now().isoformat(),
                "sensors": mqtt_sensor.generate_sensor_data()
            }
            
            for connection in current_connections:
                try:
                    await connection.send_json(modbus_state)
                    await asyncio.sleep(0.1)  # Small delay between messages
                    await connection.send_json(mqtt_state)
                except:
                    connections.remove(connection)
        
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    """Start all components"""
    global simulator, plc, mqtt_sensor
    
    # Initialize components
    simulator = MainEngineSimulator()
    plc = PLCController(simulator)
    mqtt_sensor = MQTTSensor()
    
    # Start Modbus server
    simulator.start_server()
    
    # Start MQTT client
    mqtt_sensor.start()
    
    # Start state broadcaster
    asyncio.create_task(broadcast_state())
    
    # Start MQTT publisher
    asyncio.create_task(mqtt_sensor.publish_loop())

@app.on_event("shutdown")
async def shutdown_event():
    """Stop all components"""
    mqtt_sensor.stop()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
                print(f"Received command: {data}")  # Debug log
                
                if "command" in data:
                    if data["command"] == "start_engine":
                        print("Starting engine...")  # Debug log
                        simulator.running = True
                        # Send immediate feedback
                        await websocket.send_json({
                            "type": "modbus",
                            "engine": {
                                "status": simulator.status,
                                "rpm": simulator.current_rpm,
                                "temperature": simulator.current_temp,
                                "fuel_flow": simulator.current_fuel_flow,
                                "load": simulator.current_load
                            }
                        })
                    elif data["command"] == "stop_engine":
                        print("Stopping engine...")  # Add logging
                        simulator.running = False
                        await websocket.send_json({
                            "status": "ok",
                            "command": "stop_engine",
                            "engine_status": simulator.status
                        })
                    elif data["command"] == "set_mode":
                        plc.set_mode(data["mode"])
                    elif data["command"] == "set_setpoint":
                        plc.set_setpoint(data["parameter"], data["value"])
                    # Send acknowledgment
                    await websocket.send_json({"status": "ok", "command": data["command"]})
            except Exception as e:
                print(f"Error in websocket: {e}")  # Debug log
    except:
        connections.remove(websocket)

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
        "mqtt_sensors": mqtt_sensor.generate_sensor_data()
    }

if __name__ == "__main__":
    import asyncio
    
    async def main():
        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()

    # Run the async main function
    asyncio.run(main()) 