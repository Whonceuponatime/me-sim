#!/usr/bin/env python3
"""
ME Simulator Remote Access Configuration Script
This script helps configure the system for access from different machines.
"""

import json
import socket
import subprocess
import sys
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
        return "127.0.0.1"

def update_frontend_settings(server_ip):
    """Update frontend default settings for remote access"""
    app_js_path = Path("frontend/src/App.js")
    
    if not app_js_path.exists():
        print(f"❌ Frontend file not found: {app_js_path}")
        return False
    
    try:
        # Read the file
        with open(app_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace localhost references with server IP
        content = content.replace(
            "websocketUrl: 'ws://localhost:8000/ws'",
            f"websocketUrl: 'ws://{server_ip}:8000/ws'"
        )
        content = content.replace(
            "modbusHost: '127.0.0.1'",
            f"modbusHost: '{server_ip}'"
        )
        
        # Write back
        with open(app_js_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Updated frontend settings to use {server_ip}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating frontend settings: {e}")
        return False

def create_settings_file(server_ip):
    """Create a settings file for easy configuration"""
    settings = {
        "websocketUrl": f"ws://{server_ip}:8000/ws",
        "modbusHost": server_ip,
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
    
    settings_path = Path("remote_settings.json")
    try:
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✅ Created settings file: {settings_path}")
        return True
    except Exception as e:
        print(f"❌ Error creating settings file: {e}")
        return False

def check_firewall_windows():
    """Check and suggest firewall configuration for Windows"""
    try:
        # Check if running as administrator
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        
        if not is_admin:
            print("⚠️  For firewall configuration, run this script as Administrator")
            return False
        
        # Try to add firewall rules
        commands = [
            'netsh advfirewall firewall add rule name="ME Simulator Backend" dir=in action=allow protocol=TCP localport=8000',
            'netsh advfirewall firewall add rule name="ME Simulator Modbus" dir=in action=allow protocol=TCP localport=502'
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
                print(f"✅ Added firewall rule for port {8000 if '8000' in cmd else 502}")
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not add firewall rule: {cmd}")
        
        return True
        
    except ImportError:
        print("⚠️  Cannot check firewall on this system")
        return False

def test_connectivity(server_ip):
    """Test if the server ports are accessible"""
    import socket
    
    ports = [8000, 502]
    results = {}
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((server_ip, port))
            sock.close()
            
            if result == 0:
                results[port] = "✅ Open"
            else:
                results[port] = "❌ Closed/Filtered"
                
        except Exception as e:
            results[port] = f"❌ Error: {e}"
    
    print(f"\n🔍 Port connectivity test for {server_ip}:")
    for port, status in results.items():
        service = "Backend" if port == 8000 else "Modbus"
        print(f"   Port {port} ({service}): {status}")
    
    return all("✅" in status for status in results.values())

def main():
    """Main configuration function"""
    print("🌐 ME Simulator Remote Access Configuration")
    print("=" * 50)
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"📍 Detected local IP: {local_ip}")
    
    # Ask user for server IP
    server_ip = input(f"\n🔧 Enter server IP address (press Enter for {local_ip}): ").strip()
    if not server_ip:
        server_ip = local_ip
    
    print(f"\n🚀 Configuring for server IP: {server_ip}")
    print("-" * 30)
    
    # Update frontend settings
    if update_frontend_settings(server_ip):
        print("✅ Frontend configuration updated")
    
    # Create settings file
    if create_settings_file(server_ip):
        print("✅ Settings file created")
    
    # Check firewall (Windows only)
    if sys.platform == "win32":
        print("\n🔥 Checking firewall configuration...")
        check_firewall_windows()
    
    # Test connectivity
    print("\n🔍 Testing connectivity...")
    if test_connectivity(server_ip):
        print("✅ All ports are accessible")
    else:
        print("⚠️  Some ports are not accessible - check firewall/network")
    
    # Final instructions
    print("\n" + "=" * 50)
    print("🎉 Configuration Complete!")
    print("\n📝 Next Steps:")
    print(f"1. Start backend: python app.py")
    print(f"2. Start frontend: cd frontend && npm start")
    print(f"3. Access from any machine: http://{server_ip}:3000")
    print(f"4. Or use settings file in browser localStorage")
    
    print(f"\n🔧 Manual Configuration:")
    print(f"   WebSocket URL: ws://{server_ip}:8000/ws")
    print(f"   Modbus Host: {server_ip}")
    
    print(f"\n🛠️  Troubleshooting:")
    print(f"   Test backend: http://{server_ip}:8000/api/status")
    print(f"   Test connectivity: telnet {server_ip} 8000")
    
    if server_ip != local_ip:
        print(f"\n⚠️  Note: You configured for {server_ip} but this machine is {local_ip}")
        print("   Make sure the backend is running on the correct machine!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration cancelled by user")
    except Exception as e:
        print(f"\n❌ Configuration failed: {e}")
        import traceback
        traceback.print_exc() 