#!/usr/bin/env python3
"""
Test script to diagnose scanning issues
"""
import sys
import subprocess
import socket
import ipaddress
import platform

def test_basic_ping():
    """Test basic ping functionality"""
    print("Testing basic ping functionality...")
    try:
        if platform.system().lower() == 'windows':
            result = subprocess.run(['ping', '-n', '1', '-w', '1000', '127.0.0.1'],
                                  capture_output=True, text=True, timeout=2)
        else:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', '127.0.0.1'],
                                  capture_output=True, text=True, timeout=2)

        print(f"Ping result: {result.returncode}")
        if result.returncode == 0:
            print("✓ Basic ping is working")
        else:
            print("✗ Basic ping failed")
            print(f"Error output: {result.stderr}")
    except Exception as e:
        print(f"✗ Ping test error: {e}")

def test_network_detection():
    """Test network auto-detection"""
    print("\nTesting network auto-detection...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            print(f"Local IP: {local_ip}")

            # Convert to network range
            ip_parts = local_ip.split('.')
            network = f"{'.'.join(ip_parts[:3])}.0/24"
            print(f"Network range: {network}")

            # Test network parsing
            test_network = ipaddress.ip_network(network, strict=False)
            hosts = list(test_network.hosts())
            print(f"✓ Network detection working - {len(hosts)} hosts to scan")

    except Exception as e:
        print(f"✗ Network detection error: {e}")

def test_module_imports():
    """Test if required modules are available"""
    print("\nTesting module imports...")

    # Test Scapy
    try:
        from scapy.layers.l2 import ARP, Ether, srp
        print("✓ Scapy is available")
        scapy_available = True
    except ImportError as e:
        print(f"✗ Scapy not available: {e}")
        scapy_available = False

    # Test manuf
    try:
        from manuf import manuf
        print("✓ Manuf is available")
        manuf_available = True
    except ImportError as e:
        print(f"✗ Manuf not available: {e}")
        manuf_available = False

    return scapy_available, manuf_available

def test_simple_scan():
    """Test a simple network scan"""
    print("\nTesting simple network scan...")
    scapy_available, manuf_available = test_module_imports()

    # Get local network
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            ip_parts = local_ip.split('.')

            # Test just the first few IPs
            test_ips = [f"{'.'.join(ip_parts[:3])}.{i}" for i in range(1, 6)]

            print(f"Testing IPs: {test_ips}")

            found_devices = 0
            for ip in test_ips:
                try:
                    if platform.system().lower() == 'windows':
                        result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip],
                                              capture_output=True, text=True, timeout=2,
                                              creationflags=subprocess.CREATE_NO_WINDOW)
                    else:
                        result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                              capture_output=True, text=True, timeout=2)

                    if result.returncode == 0:
                        print(f"✓ Found device at {ip}")
                        found_devices += 1
                except Exception as e:
                    print(f"✗ Error testing {ip}: {e}")

            print(f"Found {found_devices} devices in test scan")

    except Exception as e:
        print(f"✗ Simple scan error: {e}")

if __name__ == "__main__":
    print("Network Monitor Diagnostic Test")
    print("=" * 40)

    test_basic_ping()
    test_network_detection()
    test_module_imports()
    test_simple_scan()

    print("\n" + "=" * 40)
    print("Diagnostic complete")
