#!/usr/bin/env python3
"""
Simple test script to verify Python is working
"""

import sys
import os

print("Python test script")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Virtual environment: {os.environ.get('VIRTUAL_ENV', 'Not in virtual environment')}")

# Test basic imports
try:
    import fastapi
    print("✓ FastAPI imported successfully")
except ImportError as e:
    print(f"✗ FastAPI import failed: {e}")

try:
    from pyModbusTCP.client import ModbusClient
    print("✓ pyModbusTCP imported successfully")
except ImportError as e:
    print(f"✗ pyModbusTCP import failed: {e}")

print("Test completed!") 