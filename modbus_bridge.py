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
    def __init__(self, modbus_host="192.168.20.192", modbus_port=502, config_file=None):
        # FORCE network interface usage - even if bridge and backend are on same machine
        # This ensures MODBUS traffic is visible in network captures
        if modbus_host in ["localhost", "127.0.0.1"]:
            print("⚠️  WARNING: Using localhost will hide MODBUS traffic from network capture!")
            print("🔧 Forcing network interface for Wireshark visibility...")
            modbus_host = "192.168.20.192"  # Force network IP
            
        self.modbus_host = modbus_host
        self.modbus_port = modbus_port
        
        print(f"🌐 Bridge will connect via NETWORK IP: {modbus_host}:{modbus_port}")
        print(f"📡 This ensures MODBUS traffic is visible in Wireshark!")
        
        # Load configuration
        if config_file is None:
            config_file = Path(__file__).parent / 'config_linux.yaml'
        
        try:
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = self._default_config()
        
        self.registers = self.config['registers']
        
        # MODBUS client - explicitly use network interface
        self.client = ModbusClient(host=modbus_host, port=modbus_port, auto_open=True, auto_close=True)
        
        print(f"MODBUS Bridge initialized: {modbus_host}:{modbus_port}")
        print(f"🎯 Monitor traffic with: ip.addr == {modbus_host} and tcp.port == {modbus_port}")
    
    def _default_config(self):
        return {
            'registers': {
                'status': 0, 'rpm': 1, 'temp': 2, 'fuel_flow': 3, 'load': 4
            }
        }
    
    def read_engine_data(self):
        """Read current engine data from MODBUS backend"""
        try:
            print(f"📡 MODBUS TCP: Bridge → {self.modbus_host}:{self.modbus_port}")
            
            if not self.client.open():
                raise Exception(f"Cannot connect to MODBUS backend at {self.modbus_host}:{self.modbus_port}")
            
            engine_data = {}
            packet_count = 0
            
            for reg_name, reg_addr in self.registers.items():
                try:
                    print(f"   → Reading {reg_name} (register {reg_addr})")
                    value = self.client.read_holding_registers(reg_addr, 1)
                    packet_count += 2  # Request + Response
                    
                    if value:
                        raw_value = value[0]
                        
                        # Convert special values
                        if reg_name == 'fuel_flow':
                            display_value = raw_value / 100.0
                        else:
                            display_value = raw_value
                        
                        engine_data[reg_name] = display_value
                        print(f"   ← Response: {display_value}")
                    else:
                        engine_data[reg_name] = 0
                        print(f"   ← No response for {reg_name}")
                        
                except Exception as e:
                    print(f"❌ Error reading {reg_name}: {e}")
                    engine_data[reg_name] = 0
            
            print(f"📊 Generated {packet_count} MODBUS TCP packets")
            
            return {
                "timestamp": datetime.now().isoformat(),
                "engine": engine_data,
                "connection": "connected",
                "modbus_host": self.modbus_host,
                "modbus_port": self.modbus_port,
                "packets_sent": packet_count
            }
            
        except Exception as e:
            print(f"❌ MODBUS read error: {e}")
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
        print(f"🚀 MODBUS TCP START: Bridge → {bridge.modbus_host}:{bridge.modbus_port}")
        
        if not bridge.client.open():
            raise Exception(f"Cannot connect to MODBUS backend at {bridge.modbus_host}:{bridge.modbus_port}")
        
        # Write 1 to status register to start engine
        success = bridge.client.write_single_register(bridge.registers['status'], 1)
        print(f"📤 MODBUS Write: Register {bridge.registers['status']} = 1 (START)")
        
        if success:
            print("✅ START command sent successfully via MODBUS TCP")
            return {
                "status": "success", 
                "command": "start", 
                "message": "Engine start command sent",
                "modbus_target": f"{bridge.modbus_host}:{bridge.modbus_port}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send start command")
            
    except Exception as e:
        print(f"❌ START command error: {e}")
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
        print(f"🛑 MODBUS TCP STOP: Bridge → {bridge.modbus_host}:{bridge.modbus_port}")
        
        if not bridge.client.open():
            raise Exception(f"Cannot connect to MODBUS backend at {bridge.modbus_host}:{bridge.modbus_port}")
        
        # Write 0 to status register to stop engine
        success = bridge.client.write_single_register(bridge.registers['status'], 0)
        print(f"📤 MODBUS Write: Register {bridge.registers['status']} = 0 (STOP)")
        
        if success:
            print("✅ STOP command sent successfully via MODBUS TCP")
            return {
                "status": "success", 
                "command": "stop", 
                "message": "Engine stop command sent",
                "modbus_target": f"{bridge.modbus_host}:{bridge.modbus_port}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send stop command")
            
    except Exception as e:
        print(f"❌ STOP command error: {e}")
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
        print(f"🔍 Health check: Testing MODBUS connection to {bridge.modbus_host}:{bridge.modbus_port}")
        if bridge.client.open():
            bridge.client.close()
            print("✅ MODBUS connection healthy")
            return {
                "status": "healthy", 
                "modbus": "connected",
                "target": f"{bridge.modbus_host}:{bridge.modbus_port}"
            }
        else:
            print("❌ MODBUS connection failed")
            return {
                "status": "unhealthy", 
                "modbus": "disconnected",
                "target": f"{bridge.modbus_host}:{bridge.modbus_port}"
            }
    except Exception as e:
        print(f"❌ MODBUS health check error: {e}")
        return {
            "status": "unhealthy", 
            "modbus": "error", 
            "error": str(e),
            "target": f"{bridge.modbus_host}:{bridge.modbus_port}"
        }

def main():
    parser = argparse.ArgumentParser(description='MODBUS to Web Bridge Service')
    parser.add_argument('--modbus-host', default='192.168.20.192', help='MODBUS backend host (use network IP for Wireshark visibility)')
    parser.add_argument('--modbus-port', type=int, default=502, help='MODBUS backend port')
    parser.add_argument('--web-host', default='192.168.20.100', help='Web service host')
    parser.add_argument('--web-port', type=int, default=8000, help='Web service port')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    global bridge
    bridge = ModbusBridge(
        modbus_host=args.modbus_host,
        modbus_port=args.modbus_port,
        config_file=args.config
    )
    
    print(f"🚀 Starting MODBUS Bridge Service...")
    print(f"📡 MODBUS Backend: {args.modbus_host}:{args.modbus_port}")
    print(f"🌐 Web Service: {args.web_host}:{args.web_port}")
    print(f"🔗 Frontend can access: http://{args.web_host}:{args.web_port}/api/status")
    print("=" * 60)
    print(f"🎯 Wireshark filter: ip.addr == {args.modbus_host} and tcp.port == {args.modbus_port}")
    print("📊 Every frontend poll will generate ~10 MODBUS TCP packets!")
    print("=" * 60)
    
    uvicorn.run(app, host=args.web_host, port=args.web_port)

if __name__ == "__main__":
    main() 