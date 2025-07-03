#!/usr/bin/env python3
"""
Generate Continuous MODBUS TCP Traffic for Wireshark Analysis
This script creates constant MODBUS traffic visible in network captures
"""

import time
import argparse
from pyModbusTCP.client import ModbusClient
from datetime import datetime

def generate_continuous_traffic(host, port, interval=1.0):
    """Generate continuous MODBUS TCP traffic"""
    
    print(f"🚀 Generating MODBUS TCP traffic to {host}:{port}")
    print(f"📊 Polling interval: {interval}s")
    print(f"🔍 Monitor in Wireshark with: tcp.port == {port} or modbus")
    print("=" * 60)
    
    client = ModbusClient(host=host, port=port, auto_open=True, auto_close=False)
    
    packet_count = 0
    
    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            try:
                # Open connection
                if not client.is_open:
                    if not client.open():
                        print(f"[{timestamp}] ❌ Cannot connect to {host}:{port}")
                        time.sleep(interval)
                        continue
                
                # Read all engine registers in sequence
                registers = {
                    'STATUS': 0,
                    'RPM': 1, 
                    'TEMP': 2,
                    'FUEL_FLOW': 3,
                    'LOAD': 4
                }
                
                print(f"[{timestamp}] 📡 MODBUS TCP Packet Burst #{packet_count + 1}")
                
                for reg_name, reg_addr in registers.items():
                    try:
                        # Each read generates 2 packets: request + response
                        values = client.read_holding_registers(reg_addr, 1)
                        
                        if values:
                            packet_count += 2  # Request + Response
                            display_value = values[0]
                            
                            # Convert fuel flow from stored int to display float
                            if reg_name == 'FUEL_FLOW':
                                display_value = display_value / 100.0
                            
                            print(f"    → {reg_name}: {display_value} (Reg {reg_addr}) [Packets: +2]")
                        else:
                            print(f"    → {reg_name}: READ FAILED (Reg {reg_addr})")
                            
                    except Exception as e:
                        print(f"    → {reg_name}: ERROR - {e}")
                
                print(f"    📊 Total MODBUS packets sent: {packet_count}")
                print()
                
            except Exception as e:
                print(f"[{timestamp}] ❌ Communication error: {e}")
                client.close()
                time.sleep(1)
                continue
            
            # Wait for next cycle
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Traffic generation stopped")
        print(f"📊 Total MODBUS TCP packets generated: {packet_count}")
        
    finally:
        client.close()
        print("🔌 Connection closed")

def main():
    parser = argparse.ArgumentParser(description='Generate continuous MODBUS TCP traffic for Wireshark analysis')
    parser.add_argument('host', help='MODBUS server host IP')
    parser.add_argument('--port', '-p', type=int, default=502, help='MODBUS server port (default: 502)')
    parser.add_argument('--interval', '-i', type=float, default=1.0, help='Polling interval in seconds (default: 1.0)')
    parser.add_argument('--fast', action='store_true', help='Fast polling (0.2s interval)')
    parser.add_argument('--burst', action='store_true', help='Burst mode (0.1s interval)')
    
    args = parser.parse_args()
    
    if args.fast:
        args.interval = 0.2
    elif args.burst:
        args.interval = 0.1
    
    print("🎯 MODBUS TCP Traffic Generator for Wireshark Analysis")
    print("=" * 60)
    print(f"Target: {args.host}:{args.port}")
    print(f"Interval: {args.interval}s")
    print(f"Expected rate: ~{10/args.interval:.1f} packets/second")
    print("=" * 60)
    
    generate_continuous_traffic(args.host, args.port, args.interval)

if __name__ == "__main__":
    main() 