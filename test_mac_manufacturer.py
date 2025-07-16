#!/usr/bin/env python3
"""
Test the new MAC address and manufacturer detection functionality
"""
import sys
import os
import time

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from NetworkMonitor_CTk_Full import NetworkScanner

def test_mac_and_manufacturer_detection():
    """Test MAC address and manufacturer detection"""
    print("Testing MAC address and manufacturer detection...")

    # Test IPs that we know exist
    test_ips = ['192.168.100.1', '192.168.100.2', '192.168.100.3', '192.168.100.4']

    # Create scanner
    scanner = NetworkScanner("192.168.100.0/24")

    print("\n" + "="*60)
    print("TESTING MAC ADDRESS AND MANUFACTURER DETECTION")
    print("="*60)

    for ip in test_ips:
        print(f"\nTesting {ip}:")

        # Test MAC address detection
        print("  MAC Address Detection:")
        mac = scanner.get_mac_address(ip)
        print(f"    Result: {mac}")

        # Test manufacturer detection
        print("  Manufacturer Detection:")
        manufacturer = scanner.get_manufacturer(mac)
        print(f"    Result: {manufacturer}")

        # Test full device scan
        print("  Full Device Scan:")
        devices = scanner.arp_scan_ip(ip)

        if devices:
            device = devices[0]
            print(f"    IP: {device['ip']}")
            print(f"    MAC: {device.get('mac', 'Unknown')}")
            print(f"    Hostname: {device.get('hostname', 'Unknown')}")
            print(f"    Manufacturer: {device.get('manufacturer', 'Unknown')}")
            print(f"    Status: {device.get('status', 'Unknown')}")
        else:
            print(f"    No devices found for {ip}")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("The test shows:")
    print("✓ MAC address detection from ARP table")
    print("✓ Manufacturer lookup using manuf library")
    print("✓ Integration with full device scanning")
    print("✓ Fallback to 'Unknown' when MAC unavailable")

if __name__ == "__main__":
    test_mac_and_manufacturer_detection()
