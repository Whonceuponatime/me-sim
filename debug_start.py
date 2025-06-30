#!/usr/bin/env python3
"""
Debug Startup Script for ME Simulator

This script starts the simulator with enhanced debugging
to help identify and fix issues.
"""

import subprocess
import sys
import os
import time
import asyncio
from pathlib import Path

def run_backend_test():
    """Run the backend test to verify simulation is working"""
    print("Running backend test to verify simulation...")
    try:
        result = subprocess.run([sys.executable, 'test_backend.py'], 
                              capture_output=True, text=True, timeout=60)
        
        print("Backend Test Output:")
        print("-" * 40)
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        print("-" * 40)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Backend test timed out - this might indicate the simulation is not working")
        return False
    except Exception as e:
        print(f"Error running backend test: {e}")
        return False

def start_backend_debug():
    """Start backend with debug output"""
    print("Starting backend with debug output...")
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
    
    return subprocess.Popen([sys.executable, 'app.py'], 
                          env=env, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.STDOUT,
                          universal_newlines=True,
                          bufsize=1)

def monitor_backend_output(process):
    """Monitor backend output for key messages"""
    print("Monitoring backend output...")
    print("=" * 60)
    
    simulation_started = False
    modbus_started = False
    
    while True:
        line = process.stdout.readline()
        if not line:
            break
            
        print(line.rstrip())
        
        # Check for key messages
        if "Simulation loop started successfully" in line:
            simulation_started = True
            print("✓ SIMULATION LOOP DETECTED!")
        
        if "Modbus server started" in line:
            modbus_started = True
            print("✓ MODBUS SERVER DETECTED!")
        
        if "[SIM] Loop" in line and "Running=True" in line:
            print("✓ SIMULATION RUNNING DETECTED!")
        
        if "[BROADCAST] Sending" in line:
            print("✓ DATA BROADCAST DETECTED!")
            
        # Check for errors
        if "Error" in line or "Exception" in line:
            print("⚠ ERROR DETECTED!")

def main():
    print("ME Simulator - Debug Startup")
    print("=" * 50)
    
    # Check if files exist
    required_files = ['app.py', 'test_backend.py', 'config.yaml']
    for file in required_files:
        if not Path(file).exists():
            print(f"✗ Required file missing: {file}")
            return 1
    
    print("✓ All required files found")
    
    # Start backend with debug monitoring
    print("\nStarting backend with debug monitoring...")
    print("Watch for the following messages:")
    print("- ✓ SIMULATION LOOP DETECTED")
    print("- ✓ SIMULATION RUNNING DETECTED")
    print("- ✓ DATA BROADCAST DETECTED")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        backend_process = start_backend_debug()
        
        # Monitor output
        monitor_backend_output(backend_process)
        
        # If we get here, the process ended
        print(f"\nBackend process ended with code: {backend_process.returncode}")
        
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        try:
            backend_process.terminate()
            backend_process.wait(timeout=5)
        except:
            backend_process.kill()
        print("Backend stopped.")
    
    return 0

if __name__ == "__main__":
    exit(main()) 