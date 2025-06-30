#!/usr/bin/env python3
"""
Quick Start Script for Remote ME Simulator

This script automatically configures and starts the ME Simulator
for remote access across multiple machines.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def run_configure_ip():
    """Run the IP configuration helper"""
    try:
        result = subprocess.run([sys.executable, 'configure_ip.py'], 
                              capture_output=False, 
                              text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running IP configuration: {e}")
        return False

def start_backend():
    """Start the backend server"""
    print("Starting backend server...")
    try:
        return subprocess.Popen([sys.executable, 'app.py'])
    except Exception as e:
        print(f"Error starting backend: {e}")
        return None

def start_frontend():
    """Start the frontend server"""
    print("Starting frontend server...")
    try:
        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            print("Frontend directory not found!")
            return None
        
        # Check if node_modules exists
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("Installing frontend dependencies...")
            install_result = subprocess.run(['npm', 'install'], 
                                          cwd=frontend_dir, 
                                          capture_output=True, 
                                          text=True)
            if install_result.returncode != 0:
                print(f"Error installing dependencies: {install_result.stderr}")
                return None
        
        return subprocess.Popen(['npm', 'start'], cwd=frontend_dir)
    except Exception as e:
        print(f"Error starting frontend: {e}")
        return None

def main():
    print("ME Simulator - Quick Remote Start")
    print("=" * 40)
    
    # Step 1: Configure IP
    print("\n1. Configuring IP address...")
    if not run_configure_ip():
        print("IP configuration failed or was cancelled.")
        return 1
    
    # Step 2: Start backend
    print("\n2. Starting backend server...")
    backend_process = start_backend()
    if not backend_process:
        print("Failed to start backend server.")
        return 1
    
    # Wait a bit for backend to start
    time.sleep(3)
    
    # Step 3: Start frontend
    print("\n3. Starting frontend server...")
    frontend_process = start_frontend()
    if not frontend_process:
        print("Failed to start frontend server.")
        if backend_process:
            backend_process.terminate()
        return 1
    
    print("\n" + "=" * 50)
    print("✓ ME Simulator started successfully!")
    print("=" * 50)
    print("\nAccess the simulator:")
    print("- Local: http://localhost:3000")
    print("- Remote: http://[YOUR_IP]:3000")
    print("\nPress Ctrl+C to stop all servers")
    print("=" * 50)
    
    # Wait and handle shutdown
    try:
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("\nBackend server stopped.")
                break
            if frontend_process.poll() is not None:
                print("\nFrontend server stopped.")
                break
                
    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        
        # Terminate processes
        try:
            if frontend_process and frontend_process.poll() is None:
                frontend_process.terminate()
                print("✓ Frontend server stopped")
        except:
            pass
            
        try:
            if backend_process and backend_process.poll() is None:
                backend_process.terminate()
                print("✓ Backend server stopped")
        except:
            pass
        
        print("Shutdown complete.")
    
    return 0

if __name__ == "__main__":
    exit(main()) 