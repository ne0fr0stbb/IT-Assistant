#!/usr/bin/env python3
"""
Test Email Alerts for Live Monitor
This script tests that email alerts are triggered correctly based on thresholds
"""

import time
from email_alert_manager import email_alert_manager
from settings import settings_manager

def test_email_alerts():
    """Test email alert functionality"""
    
    # Print current settings
    alert_settings = settings_manager.settings.alerts
    print("=== Email Alert Settings ===")
    print(f"Email Notifications Enabled: {alert_settings.email_notifications}")
    print(f"Threshold: {alert_settings.email_threshold_ms}ms")
    print(f"Consecutive Failures Required: {alert_settings.email_consecutive_failures}")
    print(f"Cooldown Period: {alert_settings.email_cooldown_minutes} minutes")
    print(f"Recipients: {alert_settings.email_recipient_list}")
    print(f"Alert Types - Device Down: {alert_settings.alert_types.get('device_down', True)}")
    print(f"Alert Types - High Latency: {alert_settings.alert_types.get('high_latency', True)}")
    print("\n")
    
    # Test device info
    device_info = {
        'hostname': 'test-device',
        'manufacturer': 'Test Manufacturer',
        'mac': '00:11:22:33:44:55'
    }
    
    # Test 1: High Latency Alert
    print("=== Test 1: High Latency Alert ===")
    threshold = alert_settings.email_threshold_ms
    high_latency = threshold + 100  # 100ms above threshold
    
    print(f"Testing high latency: {high_latency}ms (threshold: {threshold}ms)")
    for i in range(alert_settings.email_consecutive_failures):
        print(f"  Sending failure {i+1}/{alert_settings.email_consecutive_failures}")
        email_alert_manager.check_and_send_alert('192.168.1.100', high_latency, 'up', device_info)
        time.sleep(1)  # Small delay between failures
    
    print("\n")
    
    # Test 2: Device Down Alert
    print("=== Test 2: Device Down Alert ===")
    print("Testing device down status")
    for i in range(alert_settings.email_consecutive_failures):
        print(f"  Sending failure {i+1}/{alert_settings.email_consecutive_failures}")
        email_alert_manager.check_and_send_alert('192.168.1.101', float('nan'), 'down', device_info)
        time.sleep(1)  # Small delay between failures
    
    print("\n")
    
    # Test 3: Normal Operation (should reset counter)
    print("=== Test 3: Normal Operation (Reset Counter) ===")
    normal_latency = threshold - 50  # 50ms below threshold
    print(f"Testing normal latency: {normal_latency}ms (threshold: {threshold}ms)")
    email_alert_manager.check_and_send_alert('192.168.1.100', normal_latency, 'up', device_info)
    
    print("\n")
    
    # Test 4: Cooldown Period
    print("=== Test 4: Cooldown Period ===")
    print("Testing alert during cooldown (should be skipped)")
    email_alert_manager.check_and_send_alert('192.168.1.100', high_latency, 'up', device_info)
    
    print("\n")
    print("=== Test Complete ===")
    print("Check debug output above and your email inbox for alerts.")
    print("If email notifications are disabled or not configured, no emails will be sent.")

if __name__ == "__main__":
    test_email_alerts()
