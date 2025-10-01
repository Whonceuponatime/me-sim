#!/usr/bin/env python3
"""
MODBUS TCP Traffic Generator
This script connects to the MODBUS server and continuously reads/writes registers
to generate actual MODBUS TCP packets that can be captured in Wireshark
"""

import time
import random
from pyModbusTCP.client import ModbusClient
import argparse
import threading
import signal
import sys

class ModbusTrafficGenerator:
    def __init__(self, host="192.168.20.192", port=502):
        self.host = host
        self.port = port
        self.client = None
        self.running = False
        self.registers = {
            'status': 0,
            'rpm': 1,
            'temp': 2,
            'fuel_flow': 3,
            'load': 4
        }
        
    def connect(self):
        """Connect to MODBUS server"""
        try:
            self.client = ModbusClient(host=self.host, port=self.port, auto_open=True, auto_close=True)
            if self.client.open():
                print(f"✓ Connected to MODBUS server at {self.host}:{self.port}")
                return True
            else:
                print(f"✗ Failed to connect to MODBUS server at {self.host}:{self.port}")
                return False
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def generate_traffic(self):
        """Generate continuous MODBUS TCP traffic"""
        print("Starting MODBUS TCP traffic generation...")
        print("This will create actual MODBUS packets visible in Wireshark")
        print("=" * 60)
        
        packet_count = 0
        
        while self.running:
            try:
                if not self.client.open():
                    print("Connection lost, attempting to reconnect...")
                    if not self.connect():
                        time.sleep(5)
                        continue
                
                # Read all registers to generate MODBUS TCP packets
                for reg_name, reg_addr in self.registers.items():
                    try:
                        # Read holding register - generates MODBUS TCP packet
                        result = self.client.read_holding_registers(reg_addr, 1)
                        packet_count += 1
                        
                        if result:
                            print(f"📡 MODBUS READ: {reg_name.upper()} = {result[0]} (Register {reg_addr})")
                        else:
                            print(f"❌ MODBUS READ FAILED: {reg_name.upper()} (Register {reg_addr})")
                        
                        # Small delay between reads to make packets visible
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"Error reading {reg_name}: {e}")
                
                # Write some test values occasionally
                if packet_count % 10 == 0:
                    try:
                        # Write a test value to generate write packets
                        test_value = random.randint(0, 100)
                        success = self.client.write_single_register(self.registers['load'], test_value)
                        if success:
                            print(f"📤 MODBUS WRITE: LOAD = {test_value} (Register {self.registers['load']})")
                        packet_count += 1
                    except Exception as e:
                        print(f"Error writing test value: {e}")
                
                # Close connection to simulate real client behavior
                self.client.close()
                
                # Wait before next cycle
                time.sleep(1)
                
            except Exception as e:
                print(f"Traffic generation error: {e}")
                time.sleep(1)
        
        print("MODBUS traffic generation stopped")
    
    def start(self):
        """Start traffic generation"""
        if not self.connect():
            return False
        
        self.running = True
        
        # Start traffic generation in a separate thread
        self.traffic_thread = threading.Thread(target=self.generate_traffic, daemon=True)
        self.traffic_thread.start()
        
        return True
    
    def stop(self):
        """Stop traffic generation"""
        self.running = False
        if self.client:
            self.client.close()
        print("Traffic generator stopped")

def main():
    parser = argparse.ArgumentParser(description='MODBUS TCP Traffic Generator')
    parser.add_argument('--host', default='192.168.20.192', help='MODBUS server host')
    parser.add_argument('--port', type=int, default=502, help='MODBUS server port')
    
    args = parser.parse_args()
    
    # Create traffic generator
    generator = ModbusTrafficGenerator(host=args.host, port=args.port)
    
    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}. Shutting down...")
        generator.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("MODBUS TCP Traffic Generator")
        print("=" * 40)
        print(f"Target: {args.host}:{args.port}")
        print("This will generate continuous MODBUS TCP packets")
        print("Monitor with Wireshark filter: tcp.port == 502")
        print("Press Ctrl+C to stop")
        print("=" * 40)
        
        if generator.start():
            # Keep running until interrupted
            while True:
                time.sleep(1)
        else:
            print("Failed to start traffic generator")
            return 1
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        generator.stop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
