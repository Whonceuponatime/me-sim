#!/usr/bin/env python3
"""
Backend Test Script

This script tests the backend simulation without the frontend
to isolate potential issues.
"""

import asyncio
import websockets
import json
import time

async def test_backend():
    """Test the backend WebSocket connection and engine simulation"""
    print("Testing Backend Connection...")
    
    # Load the WebSocket URL from settings
    try:
        with open('remote_settings.json', 'r') as f:
            settings = json.load(f)
            websocket_url = settings['websocketUrl']
    except:
        websocket_url = 'ws://localhost:8000/ws'
    
    print(f"Connecting to: {websocket_url}")
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✓ Connected to backend!")
            
            # Send start engine command
            print("\n1. Testing start engine command...")
            await websocket.send(json.dumps({"command": "start_engine"}))
            
            # Wait for responses and print them
            print("Waiting for responses...")
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < 30:  # Test for 30 seconds
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    if data.get('type') == 'modbus':
                        engine_data = data.get('engine', {})
                        print(f"[{message_count:2d}] RPM: {engine_data.get('rpm', 0):6.1f}, "
                              f"Temp: {engine_data.get('temperature', 0):5.1f}°C, "
                              f"Flow: {engine_data.get('fuel_flow', 0):4.2f}, "
                              f"Load: {engine_data.get('load', 0):3d}%, "
                              f"Status: {engine_data.get('status', 0)}")
                        
                        # Check if values are changing
                        if message_count > 5:
                            rpm = engine_data.get('rpm', 0)
                            if rpm > 0:
                                print("✓ Engine parameters are updating correctly!")
                                break
                            elif message_count > 10:
                                print("⚠ Engine is running but RPM is still 0 - simulation issue detected!")
                                break
                    
                except asyncio.TimeoutError:
                    print("⚠ No messages received in 2 seconds")
                    continue
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break
            
            # Test stop engine
            print("\n2. Testing stop engine command...")
            await websocket.send(json.dumps({"command": "stop_engine"}))
            
            # Wait a bit for stop response
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"Stop response: {data}")
            except asyncio.TimeoutError:
                print("⚠ No stop response received")
            
            print("\n✓ Backend test completed!")
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure the backend is running: python app.py")
        print("2. Check if the WebSocket URL is correct")
        print("3. Verify firewall settings")
        return False
    
    return True

async def main():
    print("ME Simulator - Backend Test")
    print("=" * 40)
    
    result = await test_backend()
    
    if result:
        print("\n✓ Backend test passed!")
        print("If the frontend still doesn't work, the issue is in the frontend connection.")
    else:
        print("\n✗ Backend test failed!")
        print("Fix the backend issues before testing the frontend.")

if __name__ == "__main__":
    asyncio.run(main()) 