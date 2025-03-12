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
        
        # Engine state
        self._running = False
        self.current_rpm = 0
        self.current_temp = self.config['engine']['temp_min']
        self.current_fuel_flow = 0
        self.current_load = 0
        self.status = 0  # 0: Stopped, 1: Running, 2: Warning, 3: Alarm
        
    @property
    def running(self):
        return self._running
        
    @running.setter
    def running(self, value):
        print(f"Setting engine running state to: {value}")
        self._running = value
        if value:
            self.status = 1
            # Write running status to Modbus register
            self.client.write_single_register(self.config['registers']['status'], 1)
        else:
            self.status = 0
            # Write stopped status to Modbus register
            self.client.write_single_register(self.config['registers']['status'], 0)
        
    def start_server(self):
        """Start the Modbus server and simulation loop"""
        try:
            self.server.start()
            print(f"Modbus server started on {self.config['modbus']['host']}:{self.config['modbus']['port']}")
            # Start simulation loop
            asyncio.create_task(self._simulation_loop())
            return True
        except Exception as e:
            print(f"Error starting Modbus server: {e}")
            return False
            
    async def _simulation_loop(self):
        """Async simulation loop"""
        while True:
            print(f"Simulation loop. Engine running: {self._running}")
            self.calculate_engine_parameters()
            self.update_modbus_registers()
            await asyncio.sleep(self.config['engine']['update_interval'])
            
    def calculate_engine_parameters(self):
        """Calculate realistic engine parameters based on current state"""
        if not self._running:
            # Engine is stopping
            self.current_rpm = max(0, self.current_rpm - random.uniform(50, 100))
            self.current_fuel_flow = max(0, self.current_fuel_flow - random.uniform(0.1, 0.2))
            self.current_temp = max(
                self.config['engine']['temp_min'],
                self.current_temp - random.uniform(1, 2)
            )
            if self.current_rpm < 10:  # Engine fully stopped
                self.status = 0
                self.client.write_single_register(self.config['registers']['status'], 0)
        else:
            # Engine is running/starting
            target_rpm = self.config['engine']['rpm_normal']
            rpm_fluctuation = random.uniform(-50, 50)
            
            if self.current_rpm < target_rpm:
                self.current_rpm = min(
                    target_rpm + rpm_fluctuation,
                    self.current_rpm + random.uniform(100, 200)
                )
            else:
                self.current_rpm = target_rpm + rpm_fluctuation
            
            # Temperature calculation
            target_temp = self.config['engine']['temp_normal']
            temp_fluctuation = random.uniform(-2, 2)
            
            if self.current_temp < target_temp:
                self.current_temp = min(
                    target_temp + temp_fluctuation,
                    self.current_temp + random.uniform(1, 3)
                )
            else:
                self.current_temp = target_temp + temp_fluctuation
            
            # Fuel flow calculation
            base_fuel_flow = (self.current_rpm / self.config['engine']['rpm_max']) * \
                           self.config['engine']['fuel_flow_normal']
            fuel_fluctuation = random.uniform(-0.3, 0.3)
            self.current_fuel_flow = max(0, base_fuel_flow + fuel_fluctuation)
            
            # Calculate load
            base_load = int((self.current_rpm - self.config['engine']['rpm_min']) / 
                          (self.config['engine']['rpm_max'] - self.config['engine']['rpm_min']) * 100)
            load_fluctuation = random.randint(-5, 5)
            self.current_load = max(0, min(100, base_load + load_fluctuation))
            
            # Update status based on parameters
            if self.current_temp > self.config['engine']['temp_max'] * 0.9:
                self.status = 2  # Warning
                self.client.write_single_register(self.config['registers']['status'], 2)
            elif self.current_temp > self.config['engine']['temp_max']:
                self.status = 3  # Alarm
                self.client.write_single_register(self.config['registers']['status'], 3)
            else:
                self.status = 1  # Running
                self.client.write_single_register(self.config['registers']['status'], 1)

    def update_modbus_registers(self):
        """Update Modbus registers with current engine parameters using explicit Modbus TCP communication"""
        registers = self.config['registers']
        
        # Write values to Modbus registers using client
        self.client.write_single_register(registers['rpm'], int(self.current_rpm))
        self.client.write_single_register(registers['temp'], int(self.current_temp))
        self.client.write_single_register(registers['fuel_flow'], int(self.current_fuel_flow * 100))
        self.client.write_single_register(registers['load'], self.current_load)
        self.client.write_single_register(registers['status'], self.status) 