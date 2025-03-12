import paho.mqtt.client as mqtt
import json
import random
import asyncio
from datetime import datetime

class MQTTSensor:
    def __init__(self, broker="localhost", port=1883, topic_prefix="engine"):
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.topic_prefix = topic_prefix
        self.connected = False
        
        # Sensor data
        self.sensors = {
            "exhaust_temp": {"min": 300, "max": 400, "unit": "°C"},
            "lube_oil_pressure": {"min": 2.5, "max": 3.5, "unit": "bar"},
            "cooling_water_temp": {"min": 70, "max": 85, "unit": "°C"},
            "turbocharger_speed": {"min": 10000, "max": 15000, "unit": "rpm"}
        }
        
        # Setup callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}")
        self.connected = True
        
    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with result code {rc}")
        self.connected = False
        
    def start(self):
        """Start MQTT client and connect to broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            return False
            
    def stop(self):
        """Stop MQTT client"""
        self.client.loop_stop()
        self.client.disconnect()
        
    def generate_sensor_data(self):
        """Generate random sensor data within defined ranges"""
        data = {}
        for sensor, config in self.sensors.items():
            value = random.uniform(config["min"], config["max"])
            data[sensor] = {
                "value": round(value, 2),
                "unit": config["unit"],
                "timestamp": datetime.now().isoformat()
            }
        return data
        
    async def publish_loop(self):
        """Continuously publish sensor data"""
        while True:
            if self.connected:
                data = self.generate_sensor_data()
                for sensor, values in data.items():
                    topic = f"{self.topic_prefix}/{sensor}"
                    self.client.publish(topic, json.dumps(values))
            await asyncio.sleep(1)  # Publish every second 