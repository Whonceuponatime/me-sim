#!/bin/bash
# Linux startup script for MODBUS TCP Backend
# This script runs the backend on Linux VM (192.168.20.192)

echo "=========================================="
echo "Starting MODBUS TCP Backend on Linux"
echo "=========================================="
echo "Backend IP: 192.168.20.192"
echo "Backend Port: 502"
echo "Frontend IP: 192.168.20.100"
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check if config file exists
if [ ! -f "config_linux.yaml" ]; then
    echo "Error: config_linux.yaml not found"
    exit 1
fi

echo "Starting MODBUS TCP Server..."
echo "The server will listen on 0.0.0.0:502 (all interfaces)"
echo "Frontend can connect from 192.168.20.100"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="

# Run the backend
python3 standalone_backend.py --host 0.0.0.0 --port 502

echo ""
echo "Backend stopped."
