#!/usr/bin/env python3
"""
Test the ARP scanning logic to identify the exact issue
"""
import sys
import os
import time
import platform
import subprocess

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from NetworkMonitor_CTk_Full import NetworkScanner

def test_arp_scanning():
    """Test individual ARP scanning logic"""
    print("Testing ARP scanning logic...")

    # Test IPs that we know exist from the basic test
    test_ips = ['192.168.100.1', '192.168.100.2', '192.168.100.3', '192.168.100.4']

    # Create scanner
    scanner = NetworkScanner("192.168.100.0/24")

    print("Testing individual IP scanning...")
    for ip in test_ips:
        print(f"\nTesting IP: {ip}")

        # Test basic ping first
        print("  Testing basic ping...")
        ping_result = scanner.ping_host_simple(ip)
        print(f"  Basic ping result: {ping_result}")

        # Test ARP scan
        print("  Testing ARP scan...")
        try:
            devices = scanner.arp_scan_ip(ip)
            print(f"  ARP scan result: {len(devices)} devices found")

            if devices:
                for device in devices:
                    print(f"    Device: {device['ip']} - {device.get('mac', 'Unknown')}")
            else:
                print("    No devices found by ARP scan")

        except Exception as e:
            print(f"  ARP scan error: {e}")
            import traceback
            traceback.print_exc()

def test_scapy_directly():
    """Test Scapy ARP scanning directly"""
    print("\nTesting Scapy directly...")

    try:
        from scapy.layers.l2 import ARP, Ether, srp

        # Test a single IP that we know exists
        test_ip = '192.168.100.1'

        print(f"Testing direct Scapy ARP scan on {test_ip}...")

        # Create ARP request
        arp = ARP(pdst=test_ip)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp

        # Send and receive
        result = srp(packet, timeout=2, verbose=0)[0]

        print(f"Scapy result: {len(result)} responses")

        for sent, received in result:
            print(f"  Response from {received.psrc} at {received.hwsrc}")

    except Exception as e:
        print(f"Direct Scapy test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("ARP Scanning Debug Test")
    print("=" * 40)

    test_arp_scanning()
    test_scapy_directly()

    print("\n" + "=" * 40)
    print("Debug test complete")
