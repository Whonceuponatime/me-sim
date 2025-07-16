# Network Connectivity Test Script
# This script tests connectivity between Windows VM and Linux VM

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Network Connectivity Test" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Get Linux VM IP from user
$linuxVMIP = Read-Host "Enter Linux VM IP address"
if (-not $linuxVMIP) {
    Write-Host "Error: Please provide Linux VM IP address" -ForegroundColor Red
    exit 1
}

Write-Host "Testing connectivity to Linux VM: $linuxVMIP" -ForegroundColor Green
Write-Host ""

# Test 1: Basic ping
Write-Host "1. Testing basic ping..." -ForegroundColor Yellow
try {
    $ping = Test-Connection -ComputerName $linuxVMIP -Count 3 -Quiet
    if ($ping) {
        Write-Host "   ✓ Ping successful" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Ping failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Ping error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Port 502 (MODBUS)
Write-Host "2. Testing MODBUS port 502..." -ForegroundColor Yellow
try {
    $tcpTest = Test-NetConnection -ComputerName $linuxVMIP -Port 502 -InformationLevel Detailed
    if ($tcpTest.TcpTestSucceeded) {
        Write-Host "   ✓ Port 502 is accessible" -ForegroundColor Green
        Write-Host "   Connection details:" -ForegroundColor White
        Write-Host "     Remote Address: $($tcpTest.RemoteAddress)" -ForegroundColor White
        Write-Host "     Remote Port: $($tcpTest.RemotePort)" -ForegroundColor White
        Write-Host "     Local Address: $($tcpTest.LocalAddress)" -ForegroundColor White
        Write-Host "     Local Port: $($tcpTest.LocalPort)" -ForegroundColor White
    } else {
        Write-Host "   ✗ Port 502 is not accessible" -ForegroundColor Red
        Write-Host "   Error: $($tcpTest.TcpTestSucceeded)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ✗ Port 502 test error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Check Windows firewall
Write-Host "3. Checking Windows firewall..." -ForegroundColor Yellow
try {
    $firewallRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*502*" -or $_.DisplayName -like "*MODBUS*" }
    if ($firewallRules) {
        Write-Host "   Found firewall rules for port 502:" -ForegroundColor Green
        foreach ($rule in $firewallRules) {
            Write-Host "     - $($rule.DisplayName): $($rule.Enabled)" -ForegroundColor White
        }
    } else {
        Write-Host "   No specific firewall rules found for port 502" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ✗ Firewall check error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check network interface
Write-Host "4. Checking network interface..." -ForegroundColor Yellow
try {
    $interfaces = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
    Write-Host "   Active network interfaces:" -ForegroundColor White
    foreach ($interface in $interfaces) {
        Write-Host "     - $($interface.Name): $($interface.InterfaceDescription)" -ForegroundColor White
        $ipConfig = Get-NetIPAddress -InterfaceIndex $interface.InterfaceIndex -AddressFamily IPv4
        foreach ($ip in $ipConfig) {
            Write-Host "       IP: $($ip.IPAddress)/$($ip.PrefixLength)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "   ✗ Network interface check error: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Route to Linux VM
Write-Host "5. Checking route to Linux VM..." -ForegroundColor Yellow
try {
    $route = Test-NetRoute -RemoteIPAddress $linuxVMIP -InformationLevel Detailed
    if ($route) {
        Write-Host "   ✓ Route found to $linuxVMIP" -ForegroundColor Green
        Write-Host "   Route details:" -ForegroundColor White
        Write-Host "     Interface: $($route.InterfaceAlias)" -ForegroundColor White
        Write-Host "     NextHop: $($route.NextHop)" -ForegroundColor White
    } else {
        Write-Host "   ✗ No route found to $linuxVMIP" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Route check error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Troubleshooting Steps" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "If port 502 is not accessible, try these steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. On Linux VM, check if MODBUS server is listening:" -ForegroundColor White
Write-Host "   sudo netstat -tlnp | grep :502" -ForegroundColor Gray
Write-Host ""
Write-Host "2. On Linux VM, check firewall:" -ForegroundColor White
Write-Host "   sudo ufw status" -ForegroundColor Gray
Write-Host "   sudo ufw allow 502/tcp" -ForegroundColor Gray
Write-Host ""
Write-Host "3. On Linux VM, check if server is bound to correct interface:" -ForegroundColor White
Write-Host "   sudo ss -tlnp | grep :502" -ForegroundColor Gray
Write-Host ""
Write-Host "4. On Windows VM, try adding firewall rule:" -ForegroundColor White
Write-Host "   netsh advfirewall firewall add rule name='MODBUS' dir=out action=allow protocol=TCP remoteport=502" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Test with telnet (if available):" -ForegroundColor White
Write-Host "   telnet $linuxVMIP 502" -ForegroundColor Gray
Write-Host ""
Write-Host "6. Check if VMs are on same subnet:" -ForegroundColor White
Write-Host "   ipconfig" -ForegroundColor Gray
Write-Host "   (Compare IP addresses and subnet masks)" -ForegroundColor Gray 