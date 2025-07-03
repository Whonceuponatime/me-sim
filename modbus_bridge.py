#!/usr/bin/env python3
"""
MODBUS to Web Bridge Service
Reads data from standalone MODBUS backend and serves it to frontend via REST API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyModbusTCP.client import ModbusClient
import yaml
import asyncio
import uvicorn
from datetime import datetime
from pathlib import Path
import argparse

app = FastAPI(title="MODBUS Bridge Service")

# CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):(3000|8000)",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class ModbusBridge:
    def __init__(self, modbus_host="192.168.0.25", modbus_port=5020, config_file=None):
        self.modbus_host = modbus_host
        self.modbus_port = modbus_port
        
        # Load configuration
        if config_file is None:
            config_file = Path(__file__).parent / 'config.yaml'
        
        try:
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = self._default_config()
        
        self.registers = self.config['registers']
        
        # MODBUS client
        self.client = ModbusClient(host=modbus_host, port=modbus_port, auto_open=True, auto_close=True)
        
        print(f"MODBUS Bridge initialized: {modbus_host}:{modbus_port}")
    
    def _default_config(self):
        return {
            'registers': {
                'status': 0, 'rpm': 1, 'temp': 2, 'fuel_flow': 3, 'load': 4
            }
        }
    
    def read_engine_data(self):
        """Read current engine data from MODBUS backend"""
        try:
            if not self.client.open():
                raise Exception("Cannot connect to MODBUS backend")
            
            engine_data = {}
            
            for reg_name, reg_addr in self.registers.items():
                try:
                    value = self.client.read_holding_registers(reg_addr, 1)
                    if value:
                        raw_value = value[0]
                        
                        # Convert special values
                        if reg_name == 'fuel_flow':
                            display_value = raw_value / 100.0
                        else:
                            display_value = raw_value
                        
                        engine_data[reg_name] = display_value
                    else:
                        engine_data[reg_name] = 0
                        
                except Exception as e:
                    print(f"Error reading {reg_name}: {e}")
                    engine_data[reg_name] = 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "engine": engine_data,
                "connection": "connected"
            }
            
        except Exception as e:
            print(f"MODBUS read error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "engine": {"status": 0, "rpm": 0, "temp": 0, "fuel_flow": 0, "load": 0},
                "connection": "disconnected",
                "error": str(e)
            }
        finally:
            self.client.close()

# Global bridge instance
bridge = None

@app.on_event("startup")
async def startup_event():
    global bridge
    # Will be initialized when first endpoint is called
    pass

@app.get("/api/status")
async def get_engine_status():
    """Get current engine status from MODBUS backend"""
    global bridge
    
    if bridge is None:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    data = bridge.read_engine_data()
    return data

@app.get("/api/engine")
async def get_engine_data():
    """Get engine data (alias for /api/status)"""
    return await get_engine_status()

@app.post("/api/engine/start")
async def start_engine():
    """Send start command to MODBUS backend"""
    global bridge
    
    if bridge is None:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    try:
        if not bridge.client.open():
            raise Exception("Cannot connect to MODBUS backend")
        
        # Write 1 to status register to start engine
        success = bridge.client.write_single_register(bridge.registers['status'], 1)
        
        if success:
            return {"status": "success", "command": "start", "message": "Engine start command sent"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send start command")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending start command: {e}")
    finally:
        bridge.client.close()

@app.post("/api/engine/stop")
async def stop_engine():
    """Send stop command to MODBUS backend"""
    global bridge
    
    if bridge is None:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    try:
        if not bridge.client.open():
            raise Exception("Cannot connect to MODBUS backend")
        
        # Write 0 to status register to stop engine
        success = bridge.client.write_single_register(bridge.registers['status'], 0)
        
        if success:
            return {"status": "success", "command": "stop", "message": "Engine stop command sent"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send stop command")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending stop command: {e}")
    finally:
        bridge.client.close()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    global bridge
    
    if bridge is None:
        return {"status": "bridge not initialized"}
    
    # Test MODBUS connection
    try:
        if bridge.client.open():
            bridge.client.close()
            return {"status": "healthy", "modbus": "connected"}
        else:
            return {"status": "unhealthy", "modbus": "disconnected"}
    except Exception as e:
        return {"status": "unhealthy", "modbus": "error", "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description='MODBUS to Web Bridge Service')
    parser.add_argument('--modbus-host', default='192.168.0.25', help='MODBUS backend host')
    parser.add_argument('--modbus-port', type=int, default=5020, help='MODBUS backend port')
    parser.add_argument('--web-host', default='0.0.0.0', help='Web service host')
    parser.add_argument('--web-port', type=int, default=8000, help='Web service port')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    global bridge
    bridge = ModbusBridge(
        modbus_host=args.modbus_host,
        modbus_port=args.modbus_port,
        config_file=args.config
    )
    
    print(f"Starting MODBUS Bridge Service...")
    print(f"MODBUS Backend: {args.modbus_host}:{args.modbus_port}")
    print(f"Web Service: {args.web_host}:{args.web_port}")
    print(f"Frontend can access: http://{args.web_host}:{args.web_port}/api/status")
    
    uvicorn.run(app, host=args.web_host, port=args.web_port)

if __name__ == "__main__":
    main() 