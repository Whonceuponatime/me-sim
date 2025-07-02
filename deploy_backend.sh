#!/bin/bash
# Deployment script for MODBUS TCP Engine Simulator Backend
# Run this on your Linux VM to set up the standalone backend

set -e  # Exit on any error

echo "=========================================="
echo "MODBUS TCP Engine Simulator Backend Setup"
echo "=========================================="

# Check if running as root for port 502
if [ "$EUID" -ne 0 ] && [ "$1" != "--port=5020" ]; then
    echo "WARNING: Running without root privileges."
    echo "Port 502 requires root access. Use --port=5020 for non-root deployment."
    echo "Run: sudo $0  OR  $0 --port=5020"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create logs directory
mkdir -p logs

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv_backend" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv_backend
fi

# Activate virtual environment
source venv_backend/bin/activate

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if config file exists
if [ ! -f "config_linux.yaml" ]; then
    echo "Error: config_linux.yaml not found!"
    echo "Please ensure all files are properly deployed."
    exit 1
fi

# Determine port to use
MODBUS_PORT=502
if [ "$1" = "--port=5020" ]; then
    MODBUS_PORT=5020
    echo "Using alternative port 5020 (non-root)"
fi

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/engine-simulator.service"
if [ "$EUID" -eq 0 ]; then
    echo "Creating systemd service..."
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=MODBUS TCP Engine Simulator
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/venv_backend/bin
ExecStart=$SCRIPT_DIR/venv_backend/bin/python $SCRIPT_DIR/standalone_backend.py --host 0.0.0.0 --port $MODBUS_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable engine-simulator.service
    
    echo "Service created and enabled."
    echo "To start: systemctl start engine-simulator"
    echo "To check status: systemctl status engine-simulator"
    echo "To view logs: journalctl -u engine-simulator -f"
fi

# Configure firewall
if command -v ufw &> /dev/null; then
    echo "Configuring firewall..."
    ufw allow $MODBUS_PORT/tcp comment "MODBUS TCP Engine Simulator"
    if [ $MODBUS_PORT -eq 502 ] && [ "$1" != "--no-alt-port" ]; then
        ufw allow 5020/tcp comment "MODBUS TCP Alternative Port"
    fi
fi

# Get network information
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo "Backend deployed successfully!"
echo ""
echo "Network Information:"
echo "  Server IP: $IP_ADDRESS"
echo "  MODBUS Port: $MODBUS_PORT"
echo "  Service: engine-simulator"
echo ""
echo "To start the service manually:"
echo "  systemctl start engine-simulator"
echo ""
echo "To test from another machine:"
echo "  python demonstrate_vulnerability_remote.py $IP_ADDRESS --port $MODBUS_PORT"
echo ""
echo "Frontend configuration:"
echo "  Update frontend/public/remote_settings.json:"
echo "  \"modbusHost\": \"$IP_ADDRESS\""
echo "  \"modbusPort\": $MODBUS_PORT"
echo ""
echo "==========================================" 