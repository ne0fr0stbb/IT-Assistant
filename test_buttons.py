#!/usr/bin/env python3
"""
Test script to verify settings dialog buttons are visible
"""

import customtkinter as ctk
from settings_manager import SettingsDialog
from settings import settings_manager

def test_buttons():
    """Test if buttons are visible in settings dialog"""
    
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    
    # Create root window
    root = ctk.CTk()
    root.title("Settings Button Test")
    root.geometry("200x150")
    
    def show_dialog():
        # Reset settings first to ensure defaults are loaded
        settings_manager.reset_to_defaults()
        
        # Create dialog
        dialog = SettingsDialog(root)
        
        # Print current settings to verify defaults
        print("Current settings after reset:")
        print(f"  Max workers: {settings_manager.settings.scan.max_workers}")
        print(f"  Timeout: {settings_manager.settings.scan.timeout}")
        print(f"  Ping timeout: {settings_manager.settings.scan.ping_timeout}")
        print(f"  Enable scapy: {settings_manager.settings.scan.enable_scapy}")
        print(f"  Enable MAC lookup: {settings_manager.settings.scan.enable_mac_lookup}")
        print(f"  Auto detect network: {settings_manager.settings.scan.auto_detect_network}")
        print(f"  Default network range: {settings_manager.settings.scan.default_network_range}")
        
    # Create button to show dialog
    ctk.CTkButton(root, text="Show Settings Dialog", command=show_dialog).pack(pady=20)
    
    # Start GUI
    root.mainloop()

if __name__ == "__main__":
    test_buttons()
