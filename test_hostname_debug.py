#!/usr/bin/env python3
"""
Test hostname resolution specifically to identify the issue
"""
import sys
import os
import time
import socket

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from NetworkMonitor_CTk_Full import NetworkScanner

def test_hostname_resolution():
    """Test hostname resolution for known IPs"""
    print("Testing hostname resolution...")

    # Test IPs that we know exist
    test_ips = ['192.168.100.1', '192.168.100.2', '192.168.100.3', '192.168.100.4']

    # Create scanner
    scanner = NetworkScanner("192.168.100.0/24")

    for ip in test_ips:
        print(f"\nTesting hostname resolution for {ip}:")

        # Test direct socket hostname resolution
        print("  Direct socket.gethostbyaddr()...")
        try:
            start_time = time.time()
            hostname = socket.gethostbyaddr(ip)[0]
            end_time = time.time()
            print(f"    Result: {hostname} (took {end_time - start_time:.2f}s)")
        except Exception as e:
            print(f"    Failed: {e}")

        # Test scanner's get_hostname method
        print("  Scanner get_hostname()...")
        try:
            start_time = time.time()
            hostname = scanner.get_hostname(ip)
            end_time = time.time()
            print(f"    Result: {hostname} (took {end_time - start_time:.2f}s)")
        except Exception as e:
            print(f"    Failed: {e}")

def test_full_device_scan():
    """Test full device scan to see hostname results"""
    print("\n" + "="*50)
    print("Testing full device scan with hostname resolution...")

    # Create scanner
    scanner = NetworkScanner("192.168.100.0/29")  # Small range

    # Test individual IP scanning
    test_ips = ['192.168.100.1', '192.168.100.2', '192.168.100.3', '192.168.100.4']

    for ip in test_ips:
        print(f"\nScanning {ip}:")
        devices = scanner.arp_scan_ip(ip)

        if devices:
            for device in devices:
                print(f"  IP: {device['ip']}")
                print(f"  MAC: {device.get('mac', 'Unknown')}")
                print(f"  Hostname: {device.get('hostname', 'Unknown')}")
                print(f"  Status: {device.get('status', 'Unknown')}")
        else:
            print(f"  No devices found for {ip}")

if __name__ == "__main__":
    test_hostname_resolution()
    test_full_device_scan()
