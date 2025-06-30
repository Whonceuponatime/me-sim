import time
import random
import yaml
import numpy as np
from pyModbusTCP.server import ModbusServer
from pyModbusTCP.client import ModbusClient
import asyncio
from pathlib import Path

class MainEngineSimulator:
    def __init__(self, config_file=None):
        # Load configuration
        if config_file is None:
            config_file = Path(__file__).parent.parent / 'config.yaml'
            
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize Modbus server
        self.server = ModbusServer(
            host=self.config['modbus']['host'],
            port=self.config['modbus']['port'],
            no_block=True
        )
        
        # Initialize Modbus client for explicit communication
        self.client = ModbusClient(
            host=self.config['modbus']['host'],
            port=self.config['modbus']['port'],
            auto_open=True
        )
        
        # Initialize separate client for status checking
        self.status_client = ModbusClient(
            host=self.config['modbus']['host'],
            port=self.config['modbus']['port'],
            auto_open=True
        )
        
        # Engine state
        self._running = False
        self.current_rpm = 0
        self.current_temp = self.config['engine']['temp_min']
        self.current_fuel_flow = 0
        self.current_load = 0
        self.status = 0  # 0: Stopped, 1: Running, 2: Warning, 3: Alarm
        
        # Security logging
        self.last_access = {}
        self.unauthorized_attempts = 0
        
    def _update_status(self, new_status):
        """Centralized method to update engine status"""
        # Only allow status changes if engine is running or being stopped
        if new_status == 0 or self._running:
            self.status = new_status
            self.server.data_bank.set_holding_registers(self.config['registers']['status'], [new_status])
        
    @property
    def running(self):
        return self._running
        
    @running.setter
    def running(self, value):
        """Set engine running state and handle status changes"""
        print(f"Setting engine running state to: {value}")
        self._running = value
        if value:
            self._update_status(1)
            print("[ENGINE STARTED] Engine is now running")
        else:
            self._update_status(0)
            print("[ENGINE STOPPING] Engine shutdown initiated")
            print("[ALARM] Engine shutdown alarm triggered")
            # Reset parameters to initial values
            self.current_rpm = 0
            self.current_temp = self.config['engine']['temp_min']
            self.current_fuel_flow = 0
            self.current_load = 0
            # Force update registers
            self.update_modbus_registers()
            
    def start_server(self):
        """Start the Modbus server and simulation loop"""
        try:
            self.server.start()
            print(f"Modbus server started on {self.config['modbus']['host']}:{self.config['modbus']['port']}")
            print("WARNING: This is a proof of concept - Modbus server is running without authentication!")
            print("Any client can send commands to control the engine.")
            print("To demonstrate, use: modbus-cli -r 1 -w 0x00 0 -h <server_ip>")
            # Start simulation loop
            asyncio.create_task(self._simulation_loop())
            return True
        except Exception as e:
            print(f"Error starting Modbus server: {e}")
            return False
            
    async def _simulation_loop(self):
        """Async simulation loop"""
        print(f"Simulation loop. Engine running: {self._running}")
        while True:
            self.calculate_engine_parameters()
            self.update_modbus_registers()
            await asyncio.sleep(self.config['engine']['update_interval'])
            
    def calculate_engine_parameters(self):
        """Calculate realistic engine parameters based on current state"""
        if not self._running:
            # Engine is stopping - gradually decrease all parameters
            if self.current_rpm > 0:
                self.current_rpm = max(0, self.current_rpm - random.uniform(50, 100))
                self.current_fuel_flow = max(0, self.current_fuel_flow - random.uniform(0.1, 0.2))
                self.current_temp = max(
                    self.config['engine']['temp_min'],
                    self.current_temp - random.uniform(1, 2)
                )
                self.current_load = max(0, self.current_load - random.uniform(5, 10))
            
            # When engine fully stops, set all parameters to zero (only once)
            if self.current_rpm <= 10 and self.current_rpm > 0:
                self.current_rpm = 0
                self.current_fuel_flow = 0
                self.current_load = 0
                self._update_status(0)
                print("\n[ENGINE STOPPED] Engine has been shut down")
                print("All parameters have been reset to zero")
        else:
            # Engine is running/starting - ensure proper startup sequence
            target_rpm = self.config['engine']['rpm_normal']
            
            # If engine just started, begin from minimum RPM
            if self.current_rpm == 0:
                self.current_rpm = self.config['engine']['rpm_min']
                print(f"[ENGINE STARTUP] Starting from {self.current_rpm} RPM")
            
            # Gradual RPM increase with realistic acceleration
            if self.current_rpm < target_rpm:
                rpm_increase = random.uniform(20, 50)  # Realistic acceleration rate
                self.current_rpm = min(target_rpm, self.current_rpm + rpm_increase)
                print(f"[ENGINE ACCELERATION] RPM: {self.current_rpm:.0f} -> Target: {target_rpm}")
            else:
                # Add normal fluctuation around target RPM
                rpm_fluctuation = random.uniform(-25, 25)
                self.current_rpm = max(target_rpm - 50, min(target_rpm + 50, target_rpm + rpm_fluctuation))
            
            # Temperature calculation - gradual warmup
            target_temp = self.config['engine']['temp_normal']
            
            if self.current_temp < target_temp:
                temp_increase = random.uniform(0.5, 2.0)  # Gradual temperature rise
                self.current_temp = min(target_temp, self.current_temp + temp_increase)
            else:
                temp_fluctuation = random.uniform(-1, 1)
                self.current_temp = target_temp + temp_fluctuation
            
            # Fuel flow calculation based on actual RPM
            rpm_ratio = self.current_rpm / self.config['engine']['rpm_max']
            base_fuel_flow = rpm_ratio * self.config['engine']['fuel_flow_normal']
            fuel_fluctuation = random.uniform(-0.1, 0.1)
            self.current_fuel_flow = max(0.1, base_fuel_flow + fuel_fluctuation)
            
            # Calculate load based on RPM
            if self.current_rpm > self.config['engine']['rpm_min']:
                rpm_range = self.config['engine']['rpm_max'] - self.config['engine']['rpm_min']
                current_range = self.current_rpm - self.config['engine']['rpm_min']
                base_load = int((current_range / rpm_range) * 100)
                load_fluctuation = random.randint(-3, 3)
                self.current_load = max(0, min(100, base_load + load_fluctuation))
            else:
                self.current_load = 0
            
            # Update status based on parameters
            if self.current_temp > self.config['engine']['temp_max'] * 0.95:
                self._update_status(3)  # Alarm
            elif self.current_temp > self.config['engine']['temp_max'] * 0.9:
                self._update_status(2)  # Warning
            else:
                self._update_status(1)  # Running

    def update_modbus_registers(self):
        """Update Modbus registers with current engine parameters"""
        registers = self.config['registers']
        
        # Check if status register was changed externally
        try:
            status_value = self.server.data_bank.get_holding_registers(registers['status'], 1)
            if status_value and status_value[0] == 0 and self._running:
                print("\n" + "!"*80)
                print("!"*80)
                print("!"*80)
                print("!!! SECURITY BREACH DETECTED !!!")
                print("!"*80)
                print("!"*80)
                print("!"*80)
                
                # Set engine to emergency stop
                self._running = False
                self.current_rpm = 0
                self.current_temp = self.config['engine']['temp_min']
                self.current_fuel_flow = 0
                self.current_load = 0
                self.status = 0
                self.unauthorized_attempts += 1
                
                # Force update registers
                self.server.data_bank.set_holding_registers(registers['rpm'], [0])
                self.server.data_bank.set_holding_registers(registers['temp'], [int(self.config['engine']['temp_min'])])
                self.server.data_bank.set_holding_registers(registers['fuel_flow'], [0])
                self.server.data_bank.set_holding_registers(registers['load'], [0])
                self.server.data_bank.set_holding_registers(registers['status'], [0])
                
                # Add security alarms to PLC
                if hasattr(self, 'plc_controller'):
                    self.plc_controller.alarms.extend([
                        "SECURITY_BREACH",
                        "UNAUTHORIZED_ACCESS",
                        "SYSTEM_COMPROMISE",
                        "CRITICAL_FAILURE",
                        "EMERGENCY_STOP"
                    ])
                    self.plc_controller.set_mode("EMERGENCY")
        except Exception as e:
            print(f"Error checking status register: {e}")
        
        # Write values directly to server registers
        self.server.data_bank.set_holding_registers(registers['rpm'], [int(self.current_rpm)])
        self.server.data_bank.set_holding_registers(registers['temp'], [int(self.current_temp)])
        self.server.data_bank.set_holding_registers(registers['fuel_flow'], [int(self.current_fuel_flow * 100)])
        self.server.data_bank.set_holding_registers(registers['load'], [self.current_load])
        self.server.data_bank.set_holding_registers(registers['status'], [self.status])
        
    def set_plc_controller(self, plc_controller):
        """Set the PLC controller reference"""
        self.plc_controller = plc_controller 