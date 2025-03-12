from typing import Dict, List
import asyncio

class PLCController:
    def __init__(self, engine_simulator):
        self.engine = engine_simulator
        self.mode = "MANUAL"  # MANUAL, AUTO, EMERGENCY
        self.alarms: List[str] = []
        self.setpoints = {
            "rpm": 900,
            "temperature_max": 110,
            "fuel_flow_max": 2.0
        }
        
        # Start the control loop
        asyncio.create_task(self._control_loop())
    
    def set_mode(self, mode: str):
        """Set PLC operation mode"""
        if mode in ["MANUAL", "AUTO", "EMERGENCY"]:
            self.mode = mode
            if mode == "EMERGENCY":
                self.engine.running = False
    
    def set_setpoint(self, parameter: str, value: float):
        """Set a control setpoint"""
        if parameter in self.setpoints:
            self.setpoints[parameter] = value
    
    def check_alarms(self):
        """Check for alarm conditions"""
        self.alarms.clear()
        
        # Check temperature
        if self.engine.current_temp > self.setpoints["temperature_max"]:
            self.alarms.append("HIGH_TEMPERATURE")
        
        # Check fuel flow
        if self.engine.current_fuel_flow > self.setpoints["fuel_flow_max"]:
            self.alarms.append("HIGH_FUEL_FLOW")
        
        # Check RPM deviation
        if abs(self.engine.current_rpm - self.setpoints["rpm"]) > 100:
            self.alarms.append("RPM_DEVIATION")
        
        # Emergency actions
        if len(self.alarms) > 0 and self.mode == "AUTO":
            self.set_mode("EMERGENCY")
    
    async def _control_loop(self):
        """Main PLC control loop"""
        while True:
            # Check alarms
            self.check_alarms()
            
            # Automatic control logic
            if self.mode == "AUTO" and self.engine.running:
                # RPM control
                rpm_error = self.setpoints["rpm"] - self.engine.current_rpm
                if abs(rpm_error) > 20:
                    # Adjust fuel flow to control RPM
                    new_fuel_flow = self.engine.current_fuel_flow
                    if rpm_error > 0:
                        new_fuel_flow += 0.1
                    else:
                        new_fuel_flow -= 0.1
                    
                    # Update engine parameter (in real system, this would be done via Modbus)
                    self.engine.current_fuel_flow = max(0, min(new_fuel_flow, self.setpoints["fuel_flow_max"]))
            
            await asyncio.sleep(0.5)  # Control loop interval 