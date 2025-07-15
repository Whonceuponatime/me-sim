#!/bin/bash

# Linux VM Backend Startup Script
# This script starts the MODBUS TCP server on the Linux VM

echo "=========================================="
echo "  ME-SIM Linux VM Backend Startup"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "standalone_backend.py" ]; then
    echo "❌ Error: standalone_backend.py not found in current directory"
    echo "Please run this script from the me-sim project directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please create virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "🔍 Checking dependencies..."
python -c "import pyModbusTCP" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: pyModbusTCP not installed"
    echo "Please install dependencies: pip install -r requirements.txt"
    exit 1
fi

# Check if config file exists
if [ ! -f "config_linux.yaml" ]; then
    echo "❌ Error: config_linux.yaml not found"
    echo "Please ensure the configuration file exists"
    exit 1
fi

# Check if running as root (needed for port 502)
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Warning: Not running as root"
    echo "Port 502 requires root privileges"
    echo "You may need to run: sudo $0"
    echo ""
    echo "Alternatively, you can use a different port:"
    echo "  python standalone_backend.py --port 5020"
fi

# Display network information
echo "🌐 Network Configuration:"
echo "  - Backend IP: $(hostname -I | awk '{print $1}')"
echo "  - MODBUS Port: 502"
echo "  - Config File: config_linux.yaml"
echo ""

# Check if port 502 is available
if command -v netstat >/dev/null 2>&1; then
    if netstat -tlnp 2>/dev/null | grep -q ":502 "; then
        echo "⚠️  Warning: Port 502 is already in use"
        echo "Please stop any existing MODBUS services"
    fi
fi

echo "🚀 Starting MODBUS TCP Server..."
echo "   Press Ctrl+C to stop the server"
echo ""

# Start the backend server
python standalone_backend.py \
    --config config_linux.yaml \
    --host 0.0.0.0 \
    --port 502

echo ""
echo "✅ Backend server stopped" 