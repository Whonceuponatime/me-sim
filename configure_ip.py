#!/usr/bin/env python3
"""
IP Configuration Helper for ME Simulator

This script helps you configure the correct IP address for remote access
to the engine simulator when running on different machines.
"""

import socket
import json
import os
from pathlib import Path

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            # Fallback method
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except Exception:
            return "127.0.0.1"

def update_remote_settings(ip_address):
    """Update the remote_settings.json file with the new IP address"""
    settings_file = Path("remote_settings.json")
    frontend_settings = Path("frontend/public/remote_settings.json")
    
    # Default settings template
    default_settings = {
        "websocketUrl": f"ws://{ip_address}:8000/ws",
        "modbusHost": ip_address,
        "modbusPort": 502,
        "reconnectDelay": 2000,
        "maxReconnectAttempts": 5,
        "rpmMin": 600,
        "rpmMax": 1200,
        "rpmNormal": 900,
        "tempMin": 70,
        "tempMax": 120,
        "tempNormal": 85,
        "tempWarning": 90,
        "tempCritical": 105,
        "fuelFlowMin": 0.5,
        "fuelFlowMax": 2.5,
        "fuelFlowNormal": 1.5,
        "updateInterval": 1.0,
        "chartUpdateInterval": 1000,
        "maxHistoryPoints": 50,
        "darkMode": True,
        "showDebugInfo": False,
        "enableSounds": False,
        "enableAlarmFlashing": True,
        "gaugeAnimationSpeed": 300,
        "enableSecurityLogging": True,
        "maxUnauthorizedAttempts": 3,
        "securityAlertLevel": "high"
    }
    
    # Load existing settings if they exist
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                existing_settings = json.load(f)
            # Update IP-related settings
            existing_settings["websocketUrl"] = f"ws://{ip_address}:8000/ws"
            existing_settings["modbusHost"] = ip_address
            settings = existing_settings
        except Exception as e:
            print(f"Warning: Could not read existing settings: {e}")
            settings = default_settings
    else:
        settings = default_settings
    
    # Write updated settings
    try:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✓ Updated {settings_file}")
        
        # Also update frontend settings
        frontend_settings.parent.mkdir(parents=True, exist_ok=True)
        with open(frontend_settings, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✓ Updated {frontend_settings}")
        
        return True
    except Exception as e:
        print(f"Error updating settings: {e}")
        return False

def main():
    print("ME Simulator - IP Configuration Helper")
    print("=" * 40)
    
    # Get current IP
    current_ip = get_local_ip()
    print(f"Detected local IP address: {current_ip}")
    
    # Ask user for confirmation or manual IP
    print("\nOptions:")
    print("1. Use detected IP address")
    print("2. Enter IP address manually")
    print("3. List all available network interfaces")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "2":
        custom_ip = input("Enter the IP address to use: ").strip()
        if custom_ip:
            current_ip = custom_ip
    elif choice == "3":
        print("\nAvailable network interfaces:")
        try:
            # Get all network interfaces
            import subprocess
            if os.name == 'nt':  # Windows
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                print(result.stdout)
            else:  # Linux/macOS
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                print(result.stdout)
        except Exception as e:
            print(f"Could not list interfaces: {e}")
        
        custom_ip = input("\nEnter the IP address to use: ").strip()
        if custom_ip:
            current_ip = custom_ip
    
    # Update settings
    print(f"\nConfiguring simulator for IP address: {current_ip}")
    
    if update_remote_settings(current_ip):
        print("\n✓ Configuration completed successfully!")
        print(f"\nTo run the simulator on other machines:")
        print(f"1. Ensure this machine ({current_ip}) is running the backend")
        print(f"2. Other machines can access the frontend at: http://{current_ip}:3000")
        print(f"3. The frontend will automatically connect to: ws://{current_ip}:8000/ws")
        print(f"\nMake sure port 8000 (backend) and 3000 (frontend) are open in your firewall!")
    else:
        print("\n✗ Configuration failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 