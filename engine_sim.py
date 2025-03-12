#!/usr/bin/env python3

import time
import random
import yaml
import numpy as np
from pyModbusTCP.server import ModbusServer, DataBank

class MainEngineSimulator:
    def __init__(self, config_file='config.yaml'):
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize Modbus server
        self.server = ModbusServer(
            host=self.config['modbus']['host'],
            port=self.config['modbus']['port'],
            no_block=True
        )
        
        # Engine state
        self.running = False
        self.current_rpm = 0
        self.current_temp = self.config['engine']['temp_min']
        self.current_fuel_flow = 0
        self.current_load = 0
        self.status = 0  # 0: Stopped, 1: Running, 2: Warning, 3: Alarm
        
    def start_server(self):
        """Start the Modbus server"""
        try:
            self.server.start()
            print(f"Modbus server started on {self.config['modbus']['host']}:{self.config['modbus']['port']}")
            return True
        except Exception as e:
            print(f"Error starting Modbus server: {e}")
            return False
            
    def calculate_engine_parameters(self):
        """Calculate realistic engine parameters based on current state"""
        if not self.running:
            self.current_rpm = max(0, self.current_rpm - random.uniform(50, 100))
            self.current_fuel_flow = max(0, self.current_fuel_flow - random.uniform(0.1, 0.2))
            self.current_temp = max(
                self.config['engine']['temp_min'],
                self.current_temp - random.uniform(1, 2)
            )
        else:
            # RPM calculation with small fluctuations
            target_rpm = self.config['engine']['rpm_normal']
            rpm_fluctuation = random.uniform(-20, 20)
            self.current_rpm = min(
                self.config['engine']['rpm_max'],
                max(self.config['engine']['rpm_min'],
                    target_rpm + rpm_fluctuation)
            )
            
            # Temperature calculation
            self.current_temp = min(
                self.config['engine']['temp_max'],
                self.current_temp + random.uniform(-0.5, 1)
            )
            
            # Fuel flow calculation based on RPM
            base_fuel_flow = (self.current_rpm / self.config['engine']['rpm_max']) * self.config['engine']['fuel_flow_normal']
            fuel_fluctuation = random.uniform(-0.1, 0.1)
            self.current_fuel_flow = max(0, base_fuel_flow + fuel_fluctuation)
            
            # Calculate load (0-100%)
            self.current_load = int((self.current_rpm - self.config['engine']['rpm_min']) / 
                                  (self.config['engine']['rpm_max'] - self.config['engine']['rpm_min']) * 100)
            
            # Update status based on parameters
            if self.current_temp > self.config['engine']['temp_max'] * 0.9:
                self.status = 2  # Warning
            elif self.current_temp > self.config['engine']['temp_max']:
                self.status = 3  # Alarm
            else:
                self.status = 1  # Running

    def update_modbus_registers(self):
        """Update Modbus registers with current engine parameters"""
        registers = self.config['registers']
        
        # Update all registers using the newer API
        self.server.data_bank.set_holding_registers(
            registers['rpm'], [int(self.current_rpm)])
        self.server.data_bank.set_holding_registers(
            registers['temp'], [int(self.current_temp)])
        self.server.data_bank.set_holding_registers(
            registers['fuel_flow'], [int(self.current_fuel_flow * 100)])
        self.server.data_bank.set_holding_registers(
            registers['load'], [self.current_load])
        self.server.data_bank.set_holding_registers(
            registers['status'], [self.status])

    def run(self):
        """Main simulation loop"""
        if not self.start_server():
            return
        
        print("Main Engine Simulation Running...")
        print("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while True:
                self.calculate_engine_parameters()
                self.update_modbus_registers()
                time.sleep(self.config['engine']['update_interval'])
                
        except KeyboardInterrupt:
            print("\nShutting down engine simulation...")
            self.running = False
            self.server.stop()
            print("Simulation stopped")

if __name__ == "__main__":
    simulator = MainEngineSimulator()
    simulator.run() 