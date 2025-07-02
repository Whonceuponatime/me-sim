#!/usr/bin/env python3
"""
Standalone MODBUS TCP Server for Engine Simulation
This server runs independently and serves actual MODBUS TCP packets
Can be deployed on separate machines (Linux VMs)
"""

import time
import random
import yaml
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path
from pyModbusTCP.server import ModbusServer
import argparse

class StandaloneEngineSimulator:
    def __init__(self, config_file=None, host="0.0.0.0", port=502):
        """Initialize the standalone engine simulator with MODBUS TCP server"""
        
        # Load configuration
        if config_file is None:
            config_file = Path(__file__).parent / 'config.yaml'
        
        try:
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {config_file} not found, using defaults")
            self.config = self._default_config()
        
        # Override host/port if provided
        if host != "0.0.0.0":
            self.config['modbus']['host'] = host
        if port != 502:
            self.config['modbus']['port'] = port
            
        print(f"Initializing MODBUS TCP Server on {self.config['modbus']['host']}:{self.config['modbus']['port']}")
        
        # Initialize Modbus server for actual TCP communication
        self.server = ModbusServer(
            host=self.config['modbus']['host'],
            port=self.config['modbus']['port'],
            no_block=True  # Non-blocking operation
        )
        
        # Engine state variables
        self._running = False
        self.current_rpm = 0
        self.current_temp = self.config['engine']['temp_min']
        self.current_fuel_flow = 0
        self.current_load = 0
        self.status = 0  # 0: Stopped, 1: Running, 2: Warning, 3: Alarm
        
        # Security monitoring
        self.last_status_check = time.time()
        self.unauthorized_attempts = 0
        self.security_events = []
        
        # Simulation control
        self.simulation_running = False
        self.simulation_thread = None
        
        # Initialize registers to default values
        self._initialize_registers()
        
    def _default_config(self):
        """Default configuration if config.yaml is not found"""
        return {
            'modbus': {'host': '0.0.0.0', 'port': 502},
            'engine': {
                'rpm_min': 600, 'rpm_max': 1200, 'rpm_normal': 900,
                'temp_min': 70, 'temp_max': 120, 'temp_normal': 85,
                'fuel_flow_min': 0.5, 'fuel_flow_max': 2.5, 'fuel_flow_normal': 1.5,
                'update_interval': 1.0
            },
            'registers': {'status': 0, 'rpm': 1, 'temp': 2, 'fuel_flow': 3, 'load': 4}
        }
    
    def _initialize_registers(self):
        """Initialize MODBUS registers with default values"""
        registers = self.config['registers']
        
        # Initialize holding registers
        initial_values = {
            registers['status']: 0,                                    # Engine stopped
            registers['rpm']: 0,                                      # 0 RPM
            registers['temp']: int(self.config['engine']['temp_min']), # Minimum temperature
            registers['fuel_flow']: 0,                                # No fuel flow
            registers['load']: 0                                      # No load
        }
        
        for reg_addr, value in initial_values.items():
            self.server.data_bank.set_holding_registers(reg_addr, [value])
        
        print("MODBUS registers initialized:")
        for name, addr in registers.items():
            print(f"  {name.upper()}: Register {addr} = {initial_values[addr]}")
    
    def start_server(self):
        """Start the MODBUS TCP server"""
        try:
            success = self.server.start()
            if success:
                print(f"✓ MODBUS TCP Server started successfully")
                print(f"  Host: {self.config['modbus']['host']}")
                print(f"  Port: {self.config['modbus']['port']}")
                print(f"  Registers: {list(self.config['registers'].values())}")
                print("\nWARNING: This server is running without authentication!")
                print("Any MODBUS client can connect and control the engine.")
                print("This demonstrates real-world SCADA/ICS security vulnerabilities.")
                return True
            else:
                print(f"✗ Failed to start MODBUS TCP server")
                return False
        except Exception as e:
            print(f"✗ Error starting MODBUS TCP server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MODBUS TCP server"""
        if self.server.is_run:
            self.server.stop()
            print("MODBUS TCP Server stopped")
    
    def start_simulation(self):
        """Start the engine simulation loop"""
        if self.simulation_running:
            print("Simulation already running")
            return
        
        self.simulation_running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
        print("✓ Engine simulation started")
    
    def stop_simulation(self):
        """Stop the engine simulation loop"""
        self.simulation_running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2)
        print("Engine simulation stopped")
    
    def _simulation_loop(self):
        """Main simulation loop - runs in separate thread"""
        print("Starting simulation loop...")
        loop_count = 0
        
        while self.simulation_running:
            try:
                # Check for external MODBUS commands
                self._check_external_commands()
                
                # Calculate engine parameters
                self._calculate_engine_parameters()
                
                # Update MODBUS registers
                self._update_modbus_registers()
                
                # Periodic status output
                loop_count += 1
                if loop_count % 10 == 0:  # Every 10 seconds
                    self._print_status()
                
                # Sleep for update interval
                time.sleep(self.config['engine']['update_interval'])
                
            except Exception as e:
                print(f"Error in simulation loop: {e}")
                time.sleep(1)
        
        print("Simulation loop ended")
    
    def _check_external_commands(self):
        """Check for external MODBUS commands (e.g., from vulnerability demo)"""
        try:
            registers = self.config['registers']
            current_status = self.server.data_bank.get_holding_registers(registers['status'], 1)
            
            if current_status:
                status_value = current_status[0]
                
                # Check if status was changed externally to stop the engine
                if status_value == 0 and self._running:
                    print("\n" + "!"*80)
                    print("!!! UNAUTHORIZED MODBUS COMMAND DETECTED !!!")
                    print("!!! EXTERNAL CLIENT SENT STOP COMMAND !!!")
                    print("!!! THIS DEMONSTRATES A SECURITY VULNERABILITY !!!")
                    print("!"*80)
                    
                    # Log security event
                    security_event = {
                        'timestamp': datetime.now().isoformat(),
                        'event': 'UNAUTHORIZED_STOP_COMMAND',
                        'description': 'External MODBUS client sent engine stop command',
                        'risk_level': 'CRITICAL'
                    }
                    self.security_events.append(security_event)
                    self.unauthorized_attempts += 1
                    
                    # Emergency stop the engine
                    self._emergency_stop()
                    
                # Check if status was changed externally to start the engine
                elif status_value == 1 and not self._running:
                    print("\n" + "!"*60)
                    print("!!! UNAUTHORIZED START COMMAND DETECTED !!!")
                    print("!!! EXTERNAL CLIENT SENT START COMMAND !!!")
                    print("!"*60)
                    
                    # Log security event
                    security_event = {
                        'timestamp': datetime.now().isoformat(),
                        'event': 'UNAUTHORIZED_START_COMMAND',
                        'description': 'External MODBUS client sent engine start command',
                        'risk_level': 'HIGH'
                    }
                    self.security_events.append(security_event)
                    
                    # Start the engine (demonstrate vulnerability)
                    self._running = True
                    print("Engine started by external command (vulnerability demonstrated)")
                    
        except Exception as e:
            print(f"Error checking external commands: {e}")
    
    def _emergency_stop(self):
        """Perform emergency engine shutdown"""
        print("[EMERGENCY STOP] Initiating emergency shutdown...")
        self._running = False
        self.status = 0
        
        # Reset all parameters immediately
        self.current_rpm = 0
        self.current_temp = self.config['engine']['temp_min']
        self.current_fuel_flow = 0
        self.current_load = 0
        
        print("[EMERGENCY STOP] Engine parameters reset to safe values")
        print("[ALARM] Multiple safety alarms would be triggered in real system")
    
    def _calculate_engine_parameters(self):
        """Calculate realistic engine parameters based on current state"""
        if not self._running:
            # Engine is stopping/stopped - gradually decrease parameters
            if self.current_rpm > 0:
                self.current_rpm = max(0, self.current_rpm - random.uniform(50, 100))
            if self.current_fuel_flow > 0:
                self.current_fuel_flow = max(0, self.current_fuel_flow - random.uniform(0.1, 0.2))
            if self.current_temp > self.config['engine']['temp_min']:
                self.current_temp = max(
                    self.config['engine']['temp_min'],
                    self.current_temp - random.uniform(1, 2)
                )
            if self.current_load > 0:
                self.current_load = max(0, self.current_load - random.uniform(5, 10))
            
            # When engine fully stops
            if self.current_rpm < 10:
                self.current_rpm = 0
                self.current_fuel_flow = 0
                self.current_load = 0
                self.status = 0
        else:
            # Engine is running - calculate operating parameters
            target_rpm = self.config['engine']['rpm_normal']
            rpm_fluctuation = random.uniform(-30, 30)
            
            if self.current_rpm < target_rpm:
                # Starting up
                self.current_rpm = min(
                    target_rpm,
                    self.current_rpm + random.uniform(80, 150)
                )
            else:
                # Normal operation with fluctuations
                self.current_rpm = max(
                    self.config['engine']['rpm_min'],
                    min(self.config['engine']['rpm_max'], target_rpm + rpm_fluctuation)
                )
            
            # Temperature calculation
            target_temp = self.config['engine']['temp_normal']
            if self.current_temp < target_temp:
                self.current_temp = min(
                    target_temp,
                    self.current_temp + random.uniform(1, 3)
                )
            else:
                temp_fluctuation = random.uniform(-2, 2)
                self.current_temp = max(
                    self.config['engine']['temp_min'],
                    min(self.config['engine']['temp_max'], target_temp + temp_fluctuation)
                )
            
            # Fuel flow calculation (proportional to RPM)
            rpm_ratio = self.current_rpm / self.config['engine']['rpm_max']
            base_fuel_flow = rpm_ratio * self.config['engine']['fuel_flow_normal']
            fuel_fluctuation = random.uniform(-0.2, 0.2)
            self.current_fuel_flow = max(0, base_fuel_flow + fuel_fluctuation)
            
            # Load calculation
            load_base = int(rpm_ratio * 100)
            load_fluctuation = random.randint(-5, 5)
            self.current_load = max(0, min(100, load_base + load_fluctuation))
            
            # Status calculation based on temperature
            if self.current_temp > self.config['engine']['temp_max'] * 0.95:
                self.status = 3  # Alarm
            elif self.current_temp > self.config['engine']['temp_max'] * 0.85:
                self.status = 2  # Warning
            else:
                self.status = 1  # Running normally
    
    def _update_modbus_registers(self):
        """Update MODBUS TCP registers with current engine parameters"""
        registers = self.config['registers']
        
        try:
            # Update all registers with current values
            self.server.data_bank.set_holding_registers(registers['status'], [self.status])
            self.server.data_bank.set_holding_registers(registers['rpm'], [int(self.current_rpm)])
            self.server.data_bank.set_holding_registers(registers['temp'], [int(self.current_temp)])
            self.server.data_bank.set_holding_registers(registers['fuel_flow'], [int(self.current_fuel_flow * 100)])  # Store as integer (x100)
            self.server.data_bank.set_holding_registers(registers['load'], [int(self.current_load)])
            
        except Exception as e:
            print(f"Error updating MODBUS registers: {e}")
    
    def _print_status(self):
        """Print current engine status"""
        status_names = {0: "STOPPED", 1: "RUNNING", 2: "WARNING", 3: "ALARM"}
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ENGINE STATUS:")
        print(f"  Status: {status_names.get(self.status, 'UNKNOWN')} ({self.status})")
        print(f"  RPM: {self.current_rpm:.1f}")
        print(f"  Temperature: {self.current_temp:.1f}°C")
        print(f"  Fuel Flow: {self.current_fuel_flow:.2f} t/h")
        print(f"  Load: {self.current_load}%")
        if self.unauthorized_attempts > 0:
            print(f"  Security Events: {len(self.security_events)}")
            print(f"  Unauthorized Attempts: {self.unauthorized_attempts}")
    
    def run_forever(self):
        """Run the server and simulation indefinitely"""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}. Shutting down...")
            self.shutdown()
            sys.exit(0)
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            print("Starting standalone MODBUS TCP engine simulator...")
            
            # Start MODBUS server
            if not self.start_server():
                print("Failed to start MODBUS server. Exiting.")
                return False
            
            # Start simulation
            self.start_simulation()
            
            print("\n" + "="*60)
            print("STANDALONE ENGINE SIMULATOR RUNNING")
            print("="*60)
            print("The engine is now controllable via MODBUS TCP:")
            print(f"  Host: {self.config['modbus']['host']}")
            print(f"  Port: {self.config['modbus']['port']}")
            print(f"  Status Register: {self.config['registers']['status']}")
            print("\nTo start engine: Write 1 to status register")
            print("To stop engine: Write 0 to status register")
            print("\nPress Ctrl+C to stop the server")
            print("="*60)
            
            # Keep running until interrupted
            while True:
                time.sleep(60)  # Wake up every minute
                
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        except Exception as e:
            print(f"Error running server: {e}")
        finally:
            self.shutdown()
        
        return True
    
    def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down engine simulator...")
        self.stop_simulation()
        self.stop_server()
        print("Shutdown complete")


def main():
    """Main entry point for standalone server"""
    parser = argparse.ArgumentParser(description='Standalone MODBUS TCP Engine Simulator')
    parser.add_argument('--host', default='0.0.0.0', help='MODBUS server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=502, help='MODBUS server port (default: 502)')
    parser.add_argument('--config', help='Path to configuration file (default: config.yaml)')
    
    args = parser.parse_args()
    
    # Create and run simulator
    simulator = StandaloneEngineSimulator(
        config_file=args.config,
        host=args.host,
        port=args.port
    )
    
    # Run forever
    simulator.run_forever()


if __name__ == "__main__":
    main() 