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
                print("\n" + "="*80)
                print("="*80)
                print("EMERGENCY MODE ACTIVATED")
                print("="*80)
                print("="*80)
                print("[PLC] Emergency stop triggered")
                self.engine.running = False
                self.alarms.append("EMERGENCY_STOP")
                self.alarms.append("SECURITY_BREACH")
                self.alarms.append("UNAUTHORIZED_ACCESS")
                self.alarms.append("SYSTEM_COMPROMISE")
                self.alarms.append("CRITICAL_FAILURE")
                # Force engine parameters to zero
                self.engine.current_rpm = 0
                self.engine.current_fuel_flow = 0
                self.engine.current_load = 0
                print("All systems have been secured.")
                print("Security protocols activated.")
                print("="*80)
                print("="*80)
    
    def set_setpoint(self, parameter: str, value: float):
        """Set a control setpoint"""
        if parameter in self.setpoints:
            self.setpoints[parameter] = value
    
    def check_alarms(self):
        """Check for alarm conditions"""
        self.alarms.clear()
        
        # Temperature alarms
        if self.engine.current_temp > self.setpoints["temperature_max"]:
            self.alarms.append("HIGH_TEMPERATURE")
        elif self.engine.current_temp > (self.setpoints["temperature_max"] * 0.9):
            self.alarms.append("TEMPERATURE_WARNING")
        
        # Fuel flow alarms
        if self.engine.current_fuel_flow > self.setpoints["fuel_flow_max"]:
            self.alarms.append("HIGH_FUEL_FLOW")
        elif self.engine.current_fuel_flow < 0.5:
            self.alarms.append("LOW_FUEL_FLOW")
        
        # RPM alarms
        if abs(self.engine.current_rpm - self.setpoints["rpm"]) > 100:
            self.alarms.append("RPM_DEVIATION")
        elif self.engine.current_rpm > (self.setpoints["rpm"] * 1.1):
            self.alarms.append("HIGH_RPM")
        elif self.engine.current_rpm < (self.setpoints["rpm"] * 0.8):
            self.alarms.append("LOW_RPM")
        
        # Load alarms
        if self.engine.current_load > 90:
            self.alarms.append("CRITICAL_LOAD")
        elif self.engine.current_load > 80:
            self.alarms.append("HIGH_LOAD")
        
        # Engine status alarms
        if not self.engine.running and self.mode != "EMERGENCY":
            self.alarms.append("ENGINE_STOPPED")
        
        # Mode-specific alarms
        if self.mode == "AUTO" and len(self.alarms) > 0:
            self.alarms.append("AUTO_MODE_ALARM")
        
        # Emergency actions
        if len(self.alarms) > 0 and self.mode == "AUTO":
            self.set_mode("EMERGENCY")
    
    async def _control_loop(self):
        """Main PLC control loop"""
        while True:
            # Check if engine status register was changed externally
            try:
                status_value = self.engine.server.data_bank.get_holding_registers(
                    self.engine.config['registers']['status'], 1)
                if status_value and status_value[0] == 0 and self.engine.running:
                    print("[PLC] External stop command detected, switching to EMERGENCY mode")
                    self.set_mode("EMERGENCY")
            except Exception as e:
                print(f"Error checking engine status: {e}")
            
            # Check alarms
            self.check_alarms()
            
            # If engine is stopped, don't run control logic
            if not self.engine.running:
                await asyncio.sleep(0.5)
                continue
                
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