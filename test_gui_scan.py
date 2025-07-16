#!/usr/bin/env python3
"""
Test the GUI scanning integration to verify fallback mechanism works
"""
import sys
import os
import time
import threading

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from NetworkMonitor_CTk_Full import NetworkScanner

def test_gui_scanning():
    """Test GUI scanning with callbacks"""
    print("Testing GUI scanning with callbacks...")

    devices_found = []
    progress_updates = []

    def device_callback(device):
        devices_found.append(device)
        print(f"Device found: {device['ip']} - MAC: {device.get('mac', 'Unknown')}")

    def progress_callback(percent):
        progress_updates.append(percent)
        print(f"Progress: {percent}%")

    # Create scanner with callbacks (like the GUI does)
    scanner = NetworkScanner(
        "192.168.100.0/29",  # Small range for testing
        progress_callback=progress_callback,
        device_callback=device_callback
    )

    print("\nStarting scan...")
    start_time = time.time()

    # Run scan
    devices = scanner.scan()

    end_time = time.time()

    print(f"\nScan completed in {end_time - start_time:.2f} seconds")
    print(f"Final devices list: {len(devices)} devices")
    print(f"Callback devices: {len(devices_found)} devices")
    print(f"Progress updates: {len(progress_updates)} updates")

    # Compare results
    if len(devices) == len(devices_found):
        print("✓ GUI callback system working correctly")
    else:
        print("✗ GUI callback system has issues")

    # Show device details
    for i, device in enumerate(devices_found):
        print(f"  Device {i+1}: {device['ip']} - MAC: {device.get('mac', 'Unknown')} - Status: {device.get('status', 'Unknown')}")

if __name__ == "__main__":
    test_gui_scanning()
