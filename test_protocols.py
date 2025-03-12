import paho.mqtt.client as mqtt
from pyModbusTCP.client import ModbusClient
import time

def on_mqtt_connect(client, userdata, flags, rc):
    print(f"MQTT Connected with result code {rc}")
    client.subscribe("engine/#")

def on_mqtt_message(client, userdata, msg):
    print(f"MQTT << {msg.topic}: {msg.payload}")

# Test MQTT
print("Testing MQTT connection...")
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message

try:
    mqtt_client.connect("localhost", 1883, 60)
    mqtt_client.loop_start()
    print("MQTT client connected successfully")
except Exception as e:
    print(f"MQTT connection failed: {e}")

# Test Modbus TCP
print("\nTesting Modbus TCP connection...")
modbus_client = ModbusClient(host="localhost", port=502, auto_open=True)

if modbus_client.open():
    print("Modbus TCP connected successfully")
    # Try to read some registers
    regs = modbus_client.read_holding_registers(0, 5)
    if regs:
        print(f"Modbus TCP read registers: {regs}")
    else:
        print("Failed to read Modbus registers")
    modbus_client.close()
else:
    print("Modbus TCP connection failed")

# Keep script running for a few seconds to receive MQTT messages
print("\nWaiting for MQTT messages...")
time.sleep(5)
mqtt_client.loop_stop() 