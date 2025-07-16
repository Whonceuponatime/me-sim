"""
MODBUS to Web Bridge Service - Simplified Version
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
    def __init__(self, modbus_host="192.168.0.25", modbus_port=502, config_file=None):
        self.modbus_host = modbus_host
        self.modbus_port = modbus_port
        
        print(f"Bridge will connect via NETWORK IP: {modbus_host}:{modbus_port}")
        
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
            print(f"MODBUS TCP: Bridge -> {self.modbus_host}:{self.modbus_port}")
            
            if not self.client.open():
                raise Exception(f"Cannot connect to MODBUS backend at {self.modbus_host}:{self.modbus_port}")
            
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
                "connection": "connected",
                "modbus_host": self.modbus_host,
                "modbus_port": self.modbus_port
            }
            
        except Exception as e:
            print(f"MODBUS read error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "engine": {"status": 0, "rpm": 0, "temp": 0, "fuel_flow": 0, "load": 0},
                "connection": "disconnected",
                "error": str(e),
                "modbus_host": self.modbus_host,
                "modbus_port": self.modbus_port
            }
        finally:
            self.client.close()

    def start_engine(self):
        """Send start command to MODBUS backend"""
        try:
            print(f"MODBUS TCP START: Bridge -> {self.modbus_host}:{self.modbus_port}")
            
            if not self.client.open():
                raise Exception(f"Cannot connect to MODBUS backend at {self.modbus_host}:{self.modbus_port}")
            
            # Write 1 to status register to start engine
            success = self.client.write_single_register(self.registers['status'], 1)
            print(f"MODBUS Write: Register {self.registers['status']} = 1 (START)")
            
            if success:
                print("START command sent successfully via MODBUS TCP")
                return {
                    "status": "success", 
                    "command": "start", 
                    "message": "Engine start command sent",
                    "modbus_target": f"{self.modbus_host}:{self.modbus_port}"
                }
            else:
                raise Exception("Failed to send start command")
                
        except Exception as e:
            print(f"START command error: {e}")
            raise e
        finally:
            self.client.close()

    def stop_engine(self):
        """Send stop command to MODBUS backend"""
        try:
            print(f"MODBUS TCP STOP: Bridge -> {self.modbus_host}:{self.modbus_port}")
            
            if not self.client.open():
                raise Exception(f"Cannot connect to MODBUS backend at {self.modbus_host}:{self.modbus_port}")
            
            # Write 0 to status register to stop engine
            success = self.client.write_single_register(self.registers['status'], 0)
            print(f"MODBUS Write: Register {self.registers['status']} = 0 (STOP)")
            
            if success:
                print("STOP command sent successfully via MODBUS TCP")
                return {
                    "status": "success", 
                    "command": "stop", 
                    "message": "Engine stop command sent",
                    "modbus_target": f"{self.modbus_host}:{self.modbus_port}"
                }
            else:
                raise Exception("Failed to send stop command")
                
        except Exception as e:
            print(f"STOP command error: {e}")
            raise e
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
        result = bridge.start_engine()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending start command: {e}")

@app.post("/api/engine/stop")
async def stop_engine():
    """Send stop command to MODBUS backend"""
    global bridge
    
    if bridge is None:
        raise HTTPException(status_code=503, detail="Bridge not initialized")
    
    try:
        result = bridge.stop_engine()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending stop command: {e}")

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
            return {
                "status": "healthy", 
                "modbus": "connected",
                "target": f"{bridge.modbus_host}:{bridge.modbus_port}"
            }
        else:
            return {
                "status": "unhealthy", 
                "modbus": "disconnected",
                "target": f"{bridge.modbus_host}:{bridge.modbus_port}"
            }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "modbus": "error",
            "error": str(e),
            "target": f"{bridge.modbus_host}:{bridge.modbus_port}"
        }

def main():
    parser = argparse.ArgumentParser(description="MODBUS Bridge Service")
    parser.add_argument("--modbus-host", default="192.168.0.25", help="MODBUS server host")
    parser.add_argument("--modbus-port", type=int, default=502, help="MODBUS server port")
    parser.add_argument("--host", default="0.0.0.0", help="Bridge service host")
    parser.add_argument("--port", type=int, default=8000, help="Bridge service port")
    parser.add_argument("--config", help="Configuration file")
    
    args = parser.parse_args()
    
    # Initialize bridge
    global bridge
    bridge = ModbusBridge(
        modbus_host=args.modbus_host,
        modbus_port=args.modbus_port,
        config_file=args.config
    )
    
    print(f"Starting MODBUS Bridge Service on {args.host}:{args.port}")
    print(f"Connecting to MODBUS server at {args.modbus_host}:{args.modbus_port}")
    
    # Start the server
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main() 