#!/bin/bash

# Linux Network Diagnostic Script
# This script checks if the MODBUS server is properly configured and accessible

echo "=========================================="
echo "  Linux VM Network Diagnostic"
echo "=========================================="

# Get the IP address of this machine
LINUX_IP=$(hostname -I | awk '{print $1}')
echo "Linux VM IP: $LINUX_IP"
echo ""

# Test 1: Check if MODBUS server is running
echo "1. Checking if MODBUS server is running..."
if sudo netstat -tlnp 2>/dev/null | grep -q ":502 "; then
    echo "   ✓ MODBUS server is listening on port 502"
    sudo netstat -tlnp | grep ":502 "
else
    echo "   ✗ MODBUS server is NOT listening on port 502"
fi

# Test 2: Check if server is bound to all interfaces
echo ""
echo "2. Checking server binding..."
if sudo ss -tlnp 2>/dev/null | grep -q ":502 "; then
    echo "   ✓ Server is bound to port 502"
    sudo ss -tlnp | grep ":502 "
else
    echo "   ✗ Server is not bound to port 502"
fi

# Test 3: Check firewall status
echo ""
echo "3. Checking firewall status..."
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null)
    echo "   UFW Status:"
    echo "$UFW_STATUS"
    
    # Check if port 502 is allowed
    if echo "$UFW_STATUS" | grep -q "502/tcp"; then
        echo "   ✓ Port 502 is allowed in firewall"
    else
        echo "   ✗ Port 502 is NOT allowed in firewall"
        echo "   Run: sudo ufw allow 502/tcp"
    fi
else
    echo "   UFW not installed, checking iptables..."
    if sudo iptables -L 2>/dev/null | grep -q "502"; then
        echo "   ✓ Port 502 found in iptables rules"
    else
        echo "   ✗ Port 502 not found in iptables rules"
    fi
fi

# Test 4: Check network interfaces
echo ""
echo "4. Checking network interfaces..."
echo "   Active interfaces:"
ip addr show | grep -E "^[0-9]+:|inet " | grep -v "127.0.0.1" | while read line; do
    if [[ $line =~ ^[0-9]+: ]]; then
        echo "   $line"
    elif [[ $line =~ inet ]]; then
        echo "     $line"
    fi
done

# Test 5: Test local connectivity
echo ""
echo "5. Testing local connectivity..."
if nc -z localhost 502 2>/dev/null; then
    echo "   ✓ Port 502 is accessible locally"
else
    echo "   ✗ Port 502 is NOT accessible locally"
fi

# Test 6: Check if server is running with correct parameters
echo ""
echo "6. Checking server process..."
if pgrep -f "standalone_backend.py" >/dev/null; then
    echo "   ✓ standalone_backend.py is running"
    ps aux | grep "standalone_backend.py" | grep -v grep
else
    echo "   ✗ standalone_backend.py is NOT running"
fi

echo ""
echo "=========================================="
echo "  Troubleshooting Steps"
echo "=========================================="

echo "If MODBUS server is not accessible, try these steps:"
echo ""
echo "1. Restart the MODBUS server:"
echo "   sudo pkill -f standalone_backend.py"
echo "   ./start_linux_backend.sh"
echo ""
echo "2. Check if server is bound to correct interface:"
echo "   The server should be bound to 0.0.0.0:502"
echo "   Check config_linux.yaml for host: 0.0.0.0"
echo ""
echo "3. Allow port 502 in firewall:"
echo "   sudo ufw allow 502/tcp"
echo "   sudo ufw reload"
echo ""
echo "4. Test from another machine:"
echo "   telnet $LINUX_IP 502"
echo ""
echo "5. Check server logs for errors:"
echo "   Look for any error messages in the server output"
echo ""
echo "6. Verify network configuration:"
echo "   Both VMs should be on the same subnet"
echo "   Windows VM should be able to ping Linux VM" 