#!/usr/bin/env python3
"""
Test script to verify settings dialog functionality
"""

import customtkinter as ctk
from settings_manager import SettingsDialog
from settings import settings_manager

def test_settings_dialog():
    """Test the settings dialog"""
    
    # Create root window
    root = ctk.CTk()
    root.title("Settings Test")
    root.geometry("400x300")
    
    def show_dialog():
        dialog = SettingsDialog(root)
        
    def test_settings():
        print("Current settings:")
        print(f"  Email notifications: {settings_manager.settings.alerts.email_notifications}")
        print(f"  Email threshold: {settings_manager.settings.alerts.email_threshold_ms}")
        print(f"  Email consecutive failures: {settings_manager.settings.alerts.email_consecutive_failures}")
        print(f"  Email cooldown: {settings_manager.settings.alerts.email_cooldown_minutes}")
        print(f"  Email batch alerts: {settings_manager.settings.alerts.email_batch_alerts}")
        print(f"  Email batch interval: {settings_manager.settings.alerts.email_batch_interval_minutes}")
        print(f"  Email send reports: {settings_manager.settings.alerts.email_send_reports}")
        print(f"  Email report interval: {settings_manager.settings.alerts.email_report_interval_hours}")
        print(f"  Email subject template: {settings_manager.settings.alerts.email_subject_template}")
        print(f"  SMTP server: {settings_manager.settings.alerts.smtp_server}")
        print(f"  SMTP port: {settings_manager.settings.alerts.smtp_port}")
        print(f"  SMTP username: {settings_manager.settings.alerts.smtp_username}")
        print(f"  SMTP TLS: {settings_manager.settings.alerts.smtp_tls}")
        print(f"  From address: {settings_manager.settings.alerts.from_address}")
        print(f"  Email recipients: {settings_manager.settings.alerts.email_recipient_list}")
        
    def reset_settings():
        settings_manager.reset_to_defaults()
        print("Settings reset to defaults!")
        test_settings()
    
    # Create buttons
    ctk.CTkButton(root, text="Show Settings Dialog", command=show_dialog).pack(pady=10)
    ctk.CTkButton(root, text="Test Current Settings", command=test_settings).pack(pady=10)
    ctk.CTkButton(root, text="Reset to Defaults", command=reset_settings).pack(pady=10)
    
    # Test initial settings
    print("=== INITIAL SETTINGS TEST ===")
    test_settings()
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    test_settings_dialog()
