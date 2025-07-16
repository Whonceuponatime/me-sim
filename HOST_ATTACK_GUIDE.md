# Host Machine Attack Guide

## Overview
This guide shows how to run attack scripts from your host machine to demonstrate MODBUS TCP vulnerabilities against the Linux VM's industrial control system.

## Network Setup
```
Host Machine (Windows) ←→ Linux VM (MODBUS Server: Port 502)
Host Machine (Windows) ←→ Windows VM (Bridge: Port 8000, Frontend: Port 3000)
```

## Prerequisites

### 1. Install Python Dependencies
```bash
pip install pyModbusTCP
```

### 2. Verify Network Connectivity
- Ensure all 3 machines are on the same network
- Verify you can ping the Linux VM from your host machine
- Confirm MODBUS port 502 is accessible

## Attack Scripts

### Main Attack Script: `host_attack_script.py`
A comprehensive attack tool that can:
- Scan for MODBUS services
- Read current engine state
- Execute unauthorized engine stop/start commands
- Manipulate engine parameters
- Perform continuous monitoring and interference

### Quick Launcher: `run_attack.bat`
Windows batch script that:
- Checks Python installation
- Installs required packages
- Provides interactive menu
- Runs attack scripts

## Attack Types

### 1. Scan (`--attack scan`)
- Scans target IP for open MODBUS port
- Verifies MODBUS TCP service is running
- Useful for reconnaissance

### 2. Read Current State (`--attack read`)
- Reads all engine registers
- Shows current RPM, temperature, fuel flow, etc.
- Non-destructive reconnaissance

### 3. Unauthorized Engine Stop (`--attack stop`)
- Sends stop command to engine
- Demonstrates lack of authentication
- Shows critical security vulnerability

### 4. Unauthorized Engine Start (`--attack start`)
- Sends start command to engine
- Shows unauthorized access to critical controls
- Demonstrates control system vulnerabilities

### 5. Parameter Manipulation (`--attack params`)
- Injects dangerous parameter values
- Sets RPM to dangerous levels
- Shows lack of input validation

### 6. Continuous Monitoring (`--attack monitor`)
- Monitors engine state in real-time
- Interferes with normal operation
- Demonstrates persistent attack capabilities

### 7. Full Attack Sequence (`--attack full`)
- Executes all attacks in sequence
- Complete vulnerability demonstration
- Shows comprehensive security assessment

## Running Attacks

### Method 1: Using the Batch Script (Recommended)
```bash
# Double-click run_attack.bat
# Or run from command line:
run_attack.bat
```

### Method 2: Direct Python Execution
```bash
# Basic scan
python host_attack_script.py 192.168.1.100 --attack scan

# Read current state
python host_attack_script.py 192.168.1.100 --attack read

# Unauthorized stop
python host_attack_script.py 192.168.1.100 --attack stop

# Full attack sequence
python host_attack_script.py 192.168.1.100 --attack full
```

## Attack Demonstration Steps

### Step 1: Setup Verification
1. Ensure Linux VM is running the MODBUS server
2. Verify Windows VM bridge is running
3. Confirm frontend can control the engine
4. Note the Linux VM's IP address

### Step 2: Reconnaissance
```bash
python host_attack_script.py <LINUX_VM_IP> --attack scan
python host_attack_script.py <LINUX_VM_IP> --attack read
```

### Step 3: Vulnerability Demonstration
```bash
# Show unauthorized control access
python host_attack_script.py <LINUX_VM_IP> --attack stop
python host_attack_script.py <LINUX_VM_IP> --attack start

# Show parameter manipulation
python host_attack_script.py <LINUX_VM_IP> --attack params

# Show continuous interference
python host_attack_script.py <LINUX_VM_IP> --attack monitor
```

### Step 4: Full Attack Sequence
```bash
python host_attack_script.py <LINUX_VM_IP> --attack full
```

## Security Implications Demonstrated

### 1. No Authentication
- Anyone on the network can send commands
- No username/password required
- No access control mechanisms

### 2. No Encryption
- All MODBUS traffic is unencrypted
- Commands can be intercepted and modified
- No confidentiality protection

### 3. No Input Validation
- Dangerous parameter values accepted
- No range checking on critical values
- Engine can be damaged by malicious inputs

### 4. No Logging
- Unauthorized commands not logged
- No audit trail for security events
- No detection capabilities

### 5. No Access Control
- No role-based permissions
- No network segmentation
- No firewall rules protecting MODBUS

## Real-World Impact

### Industrial Consequences
- **Safety**: Unauthorized engine stops could cause accidents
- **Production**: Malicious interference could halt operations
- **Equipment**: Dangerous parameters could damage machinery
- **Financial**: Production losses from unauthorized control

### Security Lessons
- Industrial control systems need proper security
- Network segmentation is critical
- Authentication and encryption are essential
- Monitoring and logging are required
- Input validation prevents damage

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if Linux VM is running
   - Verify MODBUS server is started
   - Check network connectivity

2. **Python Not Found**
   - Install Python or activate virtual environment
   - Run `python --version` to verify

3. **Missing Dependencies**
   - Run `pip install pyModbusTCP`
   - Check Python environment

4. **Attack Not Working**
   - Verify target IP is correct
   - Check if engine is in expected state
   - Ensure network allows MODBUS traffic

### Verification Commands
```bash
# Test network connectivity
ping <LINUX_VM_IP>

# Test MODBUS port
telnet <LINUX_VM_IP> 502

# Check Python installation
python --version
pip list | findstr pyModbusTCP
```

## Safety Notes

⚠️ **Important**: This is a demonstration environment only!
- Do not run these attacks against real industrial systems
- The attacks are designed to show vulnerabilities
- Use only in controlled, isolated environments
- Follow responsible disclosure practices

## Next Steps

1. Run the attack scripts against your Linux VM
2. Observe the effects on the frontend display
3. Document the security implications
4. Consider implementing security measures
5. Explore additional attack vectors 