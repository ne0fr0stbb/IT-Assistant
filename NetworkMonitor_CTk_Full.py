#!/usr/bin/env python3
"""
NetworkMonitor - Complete CustomTkinter Version 
A comprehensive network monitoring tool with Material UI themes
Features: Network scanning, live monitoring, speed test, nmap integration, and more
"""

import sys
import os

# --- Patch sys.stdout/sys.stderr for frozen GUI apps ---
if getattr(sys, 'frozen', False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')


import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import sys
import csv
import webbrowser
import platform
from typing import Dict, List, Optional
import numpy as np
from PIL import Image
import urllib.request
import subprocess
import socket
import psutil  # For interface detection
from datetime import datetime, timedelta
from collections import deque
import ipaddress
import math
import re

# Import custom modules
from network_scanner import NetworkScanner
from database_setup import setup_database

# Import SSH functionality
try:
    from ssh_client import SSHClient
    ssh_client_module = SSHClient()
    SSH_AVAILABLE = ssh_client_module.is_available()
except ImportError:
    SSH_AVAILABLE = False
    ssh_client_module = None

# Import Nmap functionality
try:
    from nmap_runner import NmapRunner
    nmap_runner = NmapRunner()
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    nmap_runner = None

# Import speed test functionality
try:
    from speed_test_runner import SpeedTestRunner
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False

# Import tracemap functionality
try:
    from tracemap import TraceMap
    TRACEMAP_AVAILABLE = True
except ImportError:
    TRACEMAP_AVAILABLE = False

# Import settings system
try:
    from settings import settings_manager, get_theme, set_theme, get_window_size, set_window_size
    from settings_manager import show_settings_dialog
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False

# Try to import system tray module
try:
    from system_tray import SystemTrayManager
    SYSTRAY_AVAILABLE = True
except ImportError:
    SYSTRAY_AVAILABLE = False

# Try to import live monitor module
try:
    from live_monitor import LiveMonitor
    LIVE_MONITOR_AVAILABLE = True
except ImportError:
    LIVE_MONITOR_AVAILABLE = False

# ==================== UI Elements ====================

class DeviceMonitor:
    """Live device monitoring"""
    
    def __init__(self, ip, interval=2, buffer_size=100):
        self.ip = ip
        self.interval = interval
        self.buffer = deque(maxlen=buffer_size)
        self.running = False
        self.thread = None
        self.update_callback = None
        self.graph_callback = None
    
    def start(self, update_callback=None, graph_callback=None):
        if not self.running:
            self.update_callback = update_callback
            self.graph_callback = graph_callback
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _monitor_loop(self):
        while self.running:
            latency, status = self.ping_device()
            ts = time.time()
            self.buffer.append((ts, latency, status))
            
            if self.update_callback:
                self.update_callback(self.ip, latency, status, ts)
            
            if self.graph_callback:
                self.graph_callback(self.ip, list(self.buffer))
            
            time.sleep(self.interval)
    
    def ping_device(self):
        """Ping device and return latency and status"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        try:
            if platform.system().lower() == 'windows':
                output = subprocess.check_output([
                    'ping', param, '1', '-w', '1000', self.ip
                ], stderr=subprocess.STDOUT, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                output = subprocess.check_output([
                    'ping', param, '1', '-w', '1000', self.ip
                ], stderr=subprocess.STDOUT, universal_newlines=True)

            if 'unreachable' in output.lower() or 'timed out' in output.lower():
                return float('nan'), 'down'
            
            # Parse latency from ping output
            if platform.system().lower() == 'windows':
                match = re.search(r'time[<=](\d+(?:\.\d+)?)ms', output)
                if match:
                    latency = float(match.group(1))
                    return latency, 'up'
                if 'time<1ms' in output.lower():
                    return 0.5, 'up'
            else:
                match = re.search(r'time=(\d+\.?\d*) ms', output)
                if match:
                    latency = float(match.group(1))
                    return latency, 'up'
            
            return float('nan'), 'down'
        except:
            return float('nan'), 'down'

# ==================== Icon Helper Function ====================

def set_dialog_icon(dialog_window):
    """Set the application icon for dialog windows"""
    try:
        # Handle frozen application (cx_Freeze)
        if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
            # PyInstaller frozen app
            icon_path = os.path.join(sys._MEIPASS, "I.T-Assistant.ico")
        elif hasattr(sys, 'frozen'):
            # cx_Freeze frozen app
            icon_path = os.path.join(os.path.dirname(sys.executable), "I.T-Assistant.ico")
        else:
            # Regular Python script
            icon_path = os.path.join(os.path.dirname(__file__), "I.T-Assistant.ico")
        
        if os.path.exists(icon_path):
            dialog_window.iconbitmap(icon_path)
    except Exception as e:
        # Silently fail - icon is not critical
        pass

# ==================== Main Application ====================

class NetworkMonitorApp:
    def __init__(self):
        # Load saved settings first
        if SETTINGS_AVAILABLE:
            saved_theme = get_theme()
            saved_width, saved_height = get_window_size()
        else:
            saved_theme = "dark"
            saved_width, saved_height = 1200, 800

        # Set appearance based on saved settings
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("I.T Assistant - Network Monitor")
        self.root.geometry(f"{saved_width}x{saved_height}")
        self.root.minsize(1000, 720)  # Reduced minimum size for 720p displays
        
        # Set window icon
        try:
            # Handle frozen application (cx_Freeze)
            if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
                # PyInstaller frozen app
                icon_path = os.path.join(sys._MEIPASS, "I.T-Assistant.ico")
            elif hasattr(sys, 'frozen'):
                # cx_Freeze frozen app
                icon_path = os.path.join(os.path.dirname(sys.executable), "I.T-Assistant.ico")
            else:
                # Regular Python script
                icon_path = os.path.join(os.path.dirname(__file__), "I.T-Assistant.ico")
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                print(f"Icon file not found at: {icon_path}")
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        # Bind window resize event to save size
        self.root.bind("<Configure>", self.on_window_resize)
        
        # Override window close behavior to minimize to tray if available
        if SYSTRAY_AVAILABLE:
            self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Initialize variables
        self.scanning = False
        self.monitoring = False
        self.all_devices = []
        self.selected_devices = []
        self.scan_thread = None
        self.scanner = None
        self.device_monitors = {}
        self.monitor_graphs = {}
        self.monitor_paused = False
        self.is_maximized = False
        self.current_monitor_window = None
        self.last_window_size = (saved_width, saved_height)

        # Initialize modules
        self.nmap_runner = nmap_runner
        self.ssh_client = ssh_client_module
        
        # Initialize tracemap
        if TRACEMAP_AVAILABLE:
            self.tracemap = TraceMap(self.root)
        else:
            self.tracemap = None
        
        # Initialize system tray
        if SYSTRAY_AVAILABLE:
            self.tray_manager = SystemTrayManager(self)
            self.tray_manager.start()
        else:
            self.tray_manager = None

# Setup UI
        self.setup_ui()
        self.setup_menu()
        
        # Setup profile buttons
        self.setup_profile_buttons()
        
        # Auto-detect network
        self.auto_detect_network()
        
# Start a thread to get external IP
        threading.Thread(target=self.get_external_ip, daemon=True).start()
        
    def setup_profile_buttons(self):
        """Setup profile buttons"""
        from profile_manager import setup_profile_buttons
        self.profile_manager = setup_profile_buttons(self)
    
    def on_window_resize(self, event):
        """Handle window resize event to save size"""
        # Only save size for the root window, not child windows
        if event.widget == self.root:
            if SETTINGS_AVAILABLE:
                # Debounce resize events to avoid too many saves
                self.root.after(500, self.save_window_size)

    def update_status(self, message):
        """Update status bar"""
        self.status_label.configure(text=message)

    def save_window_size(self):
        """Save current window size to settings"""
        if SETTINGS_AVAILABLE:
            current_size = (self.root.winfo_width(), self.root.winfo_height())
            if current_size != self.last_window_size:
                set_window_size(current_size[0], current_size[1])
                self.last_window_size = current_size
    
    def on_window_close(self):
        """Handle window close event - minimize to tray if available, otherwise quit"""
        if self.tray_manager:
            # Use iconify for faster minimize to tray
            self.minimize_to_tray()
        else:
            # No tray manager available, quit the application
            self.quit_application()
    
    def minimize_to_tray(self):
        """Minimize window to system tray with optimized performance"""
        try:
            # Store current window state for faster restoration
            self.window_state = {
                'geometry': self.root.geometry(),
                'state': self.root.state(),
                'focus_widget': self.root.focus_get()
            }
            
            # Use iconify instead of withdraw for faster operation
            self.root.iconify()
            
            # Hide from taskbar
            self.root.withdraw()
            
            # Show tray notification
            if hasattr(self.tray_manager, 'icon') and self.tray_manager.icon:
                self.tray_manager.icon.notify(
                    "I.T Assistant minimized to tray",
                    "Double-click to restore or right-click for options"
                )
        except Exception as e:
            print(f"Error minimizing to tray: {e}")
            # Fallback to simple withdraw
            self.root.withdraw()
    
    def restore_from_tray(self):
        """Restore window from system tray with optimized performance"""
        try:
            # Restore window state first
            self.root.deiconify()
            
            # Apply saved window state if available
            if hasattr(self, 'window_state') and self.window_state:
                try:
                    # Restore geometry if it was saved
                    if 'geometry' in self.window_state:
                        self.root.geometry(self.window_state['geometry'])
                    
                    # Restore window state
                    if 'state' in self.window_state and self.window_state['state'] == 'zoomed':
                        self.root.state('zoomed')
                except Exception:
                    pass  # Ignore geometry errors
            
            # Bring window to front
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.attributes('-topmost', False)
            
            # Force focus and update
            self.root.focus_force()
            self.root.update_idletasks()
            
            # Restore focus to previously focused widget if available
            if hasattr(self, 'window_state') and self.window_state and 'focus_widget' in self.window_state:
                try:
                    if self.window_state['focus_widget']:
                        self.window_state['focus_widget'].focus_set()
                except Exception:
                    pass  # Widget might not exist anymore
                    
        except Exception as e:
            print(f"Error restoring from tray: {e}")
            # Fallback restoration
            self.root.deiconify()
            self.root.lift()
    
    def quit_application(self):
        """Properly quit the application"""
        try:
            # Stop any running monitors
            if hasattr(self, 'device_monitors'):
                for monitor in self.device_monitors.values():
                    try:
                        monitor.stop()
                    except Exception:
                        pass
                self.device_monitors.clear()
            
            # Close any monitor windows
            if hasattr(self, 'current_monitor_window') and self.current_monitor_window:
                try:
                    self.current_monitor_window.destroy()
                except Exception:
                    pass
            
            # Stop tray manager
            if self.tray_manager:
                self.tray_manager.stop()
            
            # Close matplotlib plots
            try:
                import matplotlib.pyplot as plt
                plt.close('all')
            except Exception:
                pass
            
            # Quit the main window
            self.root.quit()
            
        except Exception as e:
            print(f"Error during application shutdown: {e}")
            # Force quit if graceful shutdown fails
            sys.exit(0)
    
    def get_external_ip(self):
        """Get external IP address"""
        def _get_external_ip():
            try:
                import urllib.request
                with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                    external_ip = response.read().decode('utf-8')
                    self.root.after(0, lambda: self.external_ip_label.configure(text=f"External IP: {external_ip}"))
            except Exception:
                self.root.after(0, lambda: self.external_ip_label.configure(text="External IP: Unable to detect"))
        
        # Run in thread to avoid blocking UI
        threading.Thread(target=_get_external_ip, daemon=True).start()
    
    def update_network_information(self):
        """Update network information labels"""
        def _update_info():
            try:
                # Get local IP
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                
                # Calculate subnet
                ip_parts = local_ip.split('.')
                subnet = f"{'.'.join(ip_parts[:3])}.0/24"
                
                # Get gateway (default route)
                try:
                    import psutil
                    gateways = psutil.net_if_stats()
                    # Simple gateway detection - usually .1 in the subnet
                    gateway = f"{'.'.join(ip_parts[:3])}.1"
                except Exception:
                    gateway = "Unknown"
                
                # Get MAC address of active interface
                try:
                    import psutil
                    interfaces = psutil.net_if_addrs()
                    mac_addr = "Unknown"
                    for interface_name, addresses in interfaces.items():
                        for addr in addresses:
                            if addr.family == socket.AF_INET and addr.address == local_ip:
                                # Find MAC address for this interface
                                for addr2 in addresses:
                                    if hasattr(addr2, 'address') and ':' in str(addr2.address) and len(str(addr2.address)) == 17:
                                        mac_addr = str(addr2.address).upper()
                                        break
                                break
                        if mac_addr != "Unknown":
                            break
                except Exception:
                    mac_addr = "Unknown"
                
                # Enhanced MAC address detection if the above method fails
                if mac_addr == "Unknown":
                    mac_addr = self.get_mac_address_enhanced(local_ip)
                
                # Update labels on main thread
                self.root.after(0, lambda: self.local_ip_label.configure(text=f"Local IP: {local_ip}"))
                self.root.after(0, lambda: self.subnet_label.configure(text=f"Subnet: {subnet}"))
                self.root.after(0, lambda: self.gateway_label.configure(text=f"Gateway: {gateway}"))
                self.root.after(0, lambda: self.mac_label.configure(text=f"MAC: {mac_addr}"))
                
                # Test internet connectivity
                try:
                    with urllib.request.urlopen('https://www.google.com', timeout=5) as response:
                        self.root.after(0, lambda: self.internet_status_label.configure(
                            text="Internet: Connected", text_color="#4CAF50"))
                except Exception:
                    self.root.after(0, lambda: self.internet_status_label.configure(
                        text="Internet: Disconnected", text_color="#F44336"))
                        
            except Exception as e:
                self.root.after(0, lambda: self.local_ip_label.configure(text="Local IP: Detection failed"))
                self.root.after(0, lambda: self.internet_status_label.configure(
                    text="Internet: Check failed", text_color="#FF9800"))
        
        # Run in thread to avoid blocking UI
        threading.Thread(target=_update_info, daemon=True).start()
    
    def get_mac_address_enhanced(self, local_ip):
        """Enhanced MAC address detection with multiple fallback methods"""
        try:
            import psutil
            interfaces = psutil.net_if_addrs()
            
            for interface_name, addresses in interfaces.items():
                has_ip = False
                mac = None
                
                for addr in addresses:
                    # Check if this interface has the local IP
                    if addr.family == socket.AF_INET and addr.address == local_ip:
                        has_ip = True
                    
                    # Look for MAC address using different methods
                    if hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:
                        mac = addr.address
                    elif hasattr(addr.family, 'name') and addr.family.name == 'AF_LINK':
                        mac = addr.address
                    elif addr.family == 17:  # AF_PACKET on Linux
                        mac = addr.address
                    elif addr.family == -1:  # Sometimes MAC addresses have family -1
                        if ':' in str(addr.address) and len(str(addr.address)) == 17:
                            mac = addr.address
                
                # If we found both the IP and MAC for this interface, return it
                if has_ip and mac:
                    return mac.upper()
            
            # Fallback: try to get MAC using uuid.getnode()
            import uuid
            mac_int = uuid.getnode()
            mac_hex = ':'.join([
                f"{(mac_int >> i) & 0xff:02x}" 
                for i in range(0, 48, 8)
            ][::-1])
            return mac_hex.upper()
            
        except Exception as e:
            print(f"Enhanced MAC detection failed: {e}")
            return "Unknown"
    
    def close_existing_menu(self):
        """Close the existing menu window if it's open."""
        if hasattr(self, 'active_menu_window') and self.active_menu_window:
            self.active_menu_window.destroy()
            self.active_menu_window = None

    def show_file_menu(self):
        """Show file menu options"""
        self.close_existing_menu()  # Ensure any existing menu is closed
        
        # Create a simple popup menu
        self.active_menu_window = ctk.CTkToplevel(self.root)
        self.active_menu_window.title("File Menu")
        self.active_menu_window.geometry("200x150")
        self.active_menu_window.transient(self.root)
        self.active_menu_window.resizable(False, False)
        
        # Position near the button
        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() + 80
        self.active_menu_window.geometry(f"+{x}+{y}")
        
        ctk.CTkButton(self.active_menu_window, text="Export Device List", 
                     command=lambda: [self.export_device_list(), self.active_menu_window.destroy()]).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.active_menu_window, text="Import Device List", 
                     command=lambda: [self.import_device_list(), self.active_menu_window.destroy()]).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.active_menu_window, text="Exit", 
                     command=lambda: [self.active_menu_window.destroy(), self.quit_application()]).pack(pady=5, padx=10, fill="x")
    
    def show_options_menu(self):
        """Show options menu"""
        self.close_existing_menu()  # Ensure any existing menu is closed
        
        self.active_menu_window = ctk.CTkToplevel(self.root)
        self.active_menu_window.title("Options Menu")
        self.active_menu_window.geometry("200x120")
        self.active_menu_window.transient(self.root)
        self.active_menu_window.resizable(False, False)
        
        # Position near the button
        x = self.root.winfo_x() + 120
        y = self.root.winfo_y() + 80
        self.active_menu_window.geometry(f"+{x}+{y}")
        
        ctk.CTkButton(self.active_menu_window, text="Settings", 
                     command=lambda: [self.show_settings(), self.active_menu_window.destroy()]).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.active_menu_window, text="Preferences", 
                     command=lambda: [self.show_preferences(), self.active_menu_window.destroy()]).pack(pady=5, padx=10, fill="x")
    
    def show_about_menu(self):
        """Show about menu"""
        self.close_existing_menu()  # Ensure any existing menu is closed
        self.show_about()
    
    def show_about(self):
        """Show about dialog"""
        about_window = ctk.CTkToplevel(self.root)
        about_window.title("About I.T Assistant")
        about_window.geometry("400x300")
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Center the window
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (about_window.winfo_width() // 2)
        y = (about_window.winfo_screenheight() // 2) - (about_window.winfo_height() // 2)
        about_window.geometry(f"+{x}+{y}")
        
        about_text = """I.T Assistant - Network Monitor

Version: 2.0
        
A comprehensive network monitoring and management tool.

Features:
• Network device discovery
• Live monitoring with graphs
• SSH connectivity
• Speed testing
• Device notes and profiles
• System tray integration

Developed with Python and CustomTkinter

© 2024 I.T Assistant"""
        
        text_label = ctk.CTkLabel(
            about_window,
            text=about_text,
            justify="left",
            font=ctk.CTkFont(size=12)
        )
        text_label.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkButton(about_window, text="Close", command=about_window.destroy).pack(pady=10)
    
    def export_device_list(self):
        """Export device list to CSV"""
        if not self.all_devices:
            messagebox.showwarning("No Data", "No devices to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname=f"device_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["IP Address", "MAC Address", "Hostname", "Manufacturer", "Response Time (ms)", "Web Service", "Notes"])
                    
                    for device in self.all_devices:
                        writer.writerow([
                            device['ip'],
                            device.get('mac', 'Unknown'),
                            device.get('hostname', 'Unknown'),
                            device.get('manufacturer', 'Unknown'),
                            f"{device.get('response_time', 0) * 1000:.1f}",
                            device.get('web_service', 'None'),
                            device.get('notes', '')
                        ])
                
                messagebox.showinfo("Success", f"Device list exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export device list: {e}")
    
    def import_device_list(self):
        """Import device list from CSV"""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    imported_devices = []
                    
                    for row in reader:
                        device = {
                            'ip': row.get('IP Address', ''),
                            'mac': row.get('MAC Address', 'Unknown'),
                            'hostname': row.get('Hostname', 'Unknown'),
                            'manufacturer': row.get('Manufacturer', 'Unknown'),
                            'response_time': float(row.get('Response Time (ms)', 0)) / 1000,
                            'web_service': row.get('Web Service', 'None'),
                            'notes': row.get('Notes', ''),
                            'status': 'Imported',
                            'profile': '',
                            'friendly_name': ''
                        }
                        imported_devices.append(device)
                
                self.all_devices.extend(imported_devices)
                self.batch_add_devices(imported_devices)
                
                messagebox.showinfo("Success", f"Imported {len(imported_devices)} devices")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import device list: {e}")
    
    def show_settings(self):
        """Show settings dialog"""
        if SETTINGS_AVAILABLE:
            show_settings_dialog(self.root)
        else:
            messagebox.showinfo("Settings", "Settings system not available")
    
    def show_preferences(self):
        """Show preferences dialog"""
        messagebox.showinfo("Preferences", "Preferences dialog not yet implemented")

    def setup_ui(self):
        """Setup main UI"""
        # Configure grid with fixed sidebar and flexible main content
        self.root.grid_columnconfigure(0, weight=0, minsize=260)  # Sidebar: fixed width 260px
        self.root.grid_columnconfigure(1, weight=1)  # Main content: takes remaining space
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()

    # Remove the complex window configure handler since we're using proportional sizing

    def setup_menu(self):
        """Setup custom themed menubar using CustomTkinter"""
        # Create custom menubar frame with proper padding configuration
        self.menubar = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        self.menubar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        self.menubar.grid_columnconfigure(0, weight=1)
        self.menubar.grid_propagate(False)  # Prevent the frame from shrinking/expanding

        # Create menu button frame
        menu_button_frame = ctk.CTkFrame(self.menubar, fg_color="transparent")
        menu_button_frame.pack(side="left", padx=5, pady=2)
        
        # Get initial colors for current theme
        current_mode = ctk.get_appearance_mode()
        
        if current_mode.lower() == "dark":
            text_color = "#FFFFFF"  # White text for dark theme
            hover_color = ("gray80", "gray20")
        else:
            text_color = "#000000"  # Black text for light theme
            hover_color = ("gray80", "gray20")
        
        # File menu button
        self.file_menu_btn = ctk.CTkButton(
            menu_button_frame,
            text="File",
            width=60,
            height=26,
            fg_color="transparent",
            text_color=text_color,
            hover_color=hover_color,
            command=self.show_file_menu
        )
        self.file_menu_btn.pack(side="left", padx=2)
        
        # Options menu button
        self.options_menu_btn = ctk.CTkButton(
            menu_button_frame,
            text="Options",
            width=70,
            height=26,
            fg_color="transparent",
            text_color=text_color,
            hover_color=hover_color,
            command=self.show_options_menu
        )
        self.options_menu_btn.pack(side="left", padx=2)
        
        # About menu button
        self.about_menu_btn = ctk.CTkButton(
            menu_button_frame,
            text="About",
            width=60,
            height=26,
            fg_color="transparent",
            text_color=text_color,
            hover_color=hover_color,
            command=self.show_about_menu
        )
        self.about_menu_btn.pack(side="left", padx=2)
        
        # Configure grid properly to prevent menu bar from affecting other elements
        self.root.grid_rowconfigure(0, weight=0)  # Menu bar row - no expansion
        self.root.grid_rowconfigure(1, weight=1)  # Main content row - expandable

    def create_sidebar(self):
        """Create sidebar with controls"""
        # Create sidebar container with fixed width
        self.sidebar_container = ctk.CTkFrame(self.root, width=260, corner_radius=0)
        self.sidebar_container.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.sidebar_container.grid_propagate(False)  # Maintain fixed width

        # Configure sidebar to allow vertical expansion
        self.sidebar_container.grid_rowconfigure(0, weight=1)

        # Create sidebar frame inside container
        self.sidebar = ctk.CTkFrame(self.sidebar_container, corner_radius=0)
        self.sidebar.pack(fill="both", expand=True)
        
        # Configure sidebar grid to allow vertical resizing
        # Row 0-2: Logo and titles (fixed minimal space)
        self.sidebar.grid_rowconfigure(0, weight=0)  # Logo
        self.sidebar.grid_rowconfigure(1, weight=0)  # Title
        self.sidebar.grid_rowconfigure(2, weight=0)  # Subtitle
        
        # Row 3-6: Main content sections (expandable)
        self.sidebar.grid_rowconfigure(3, weight=1)  # Network frame
        self.sidebar.grid_rowconfigure(4, weight=1)  # Search frame
        self.sidebar.grid_rowconfigure(5, weight=1)  # Tools frame
        self.sidebar.grid_rowconfigure(6, weight=1)  # Info frame
        
        # Configure column
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Logo
        try:
            # Handle frozen application (cx_Freeze)
            if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
                # PyInstaller frozen app
                logo_path = os.path.join(sys._MEIPASS, "I.T-Assistant.png")
            elif hasattr(sys, 'frozen'):
                # cx_Freeze frozen app
                logo_path = os.path.join(os.path.dirname(sys.executable), "I.T-Assistant.png")
            else:
                # Regular Python script
                logo_path = os.path.join(os.path.dirname(__file__), "I.T-Assistant.png")
            logo_image = ctk.CTkImage(
                light_image=Image.open(logo_path),
                dark_image=Image.open(logo_path),
                size=(60, 60)  # Reduced from 80x80
            )
            logo_label = ctk.CTkLabel(
                self.sidebar,
                image=logo_image,
                text=""
            )
            logo_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")  # Reduced padding
        except Exception as e:
            print(f"Could not load logo: {e}")
            # Fallback - create empty space
            logo_label = ctk.CTkLabel(self.sidebar, text="", height=60)  # Reduced height
            logo_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")  # Reduced padding

        # Title
        title_label = ctk.CTkLabel(
            self.sidebar, 
            text="Tech Assistant",
            font=ctk.CTkFont(size=18, weight="bold")  # Reduced font size
        )
        title_label.grid(row=1, column=0, padx=10, pady=(4, 2), sticky="ew")  # Reduced padding

        subtitle_label = ctk.CTkLabel(
            self.sidebar, 
            text="Network Management Tool",
            font=ctk.CTkFont(size=13)  # Reduced font size
        )
        subtitle_label.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")  # Reduced padding

        # Network settings frame
        network_frame = ctk.CTkFrame(self.sidebar)
        network_frame.grid(row=3, column=0, padx=8, pady=8, sticky="nsew")
        network_frame.grid_columnconfigure(0, weight=1)
        
        # Configure rows for network frame
        network_frame.grid_rowconfigure(0, weight=0)  # Title
        network_frame.grid_rowconfigure(1, weight=0)  # Interface label
        network_frame.grid_rowconfigure(2, weight=1)  # Interface dropdown
        network_frame.grid_rowconfigure(3, weight=0)  # Network range label
        network_frame.grid_rowconfigure(4, weight=1)  # IP input
        network_frame.grid_rowconfigure(5, weight=1)  # Auto-detect button
        network_frame.grid_rowconfigure(6, weight=1)  # Scan button
        
        # Network title
        ctk.CTkLabel(network_frame, text="Network:",
                    font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")
        
        # Network Interface dropdown
        ctk.CTkLabel(network_frame, text="Interface:",
                    font=ctk.CTkFont(size=12)).grid(row=1, column=0, padx=10, pady=(5, 2), sticky="w")

        # Get available interfaces
        self.available_interfaces, active_interface = self.get_network_interfaces()

        # Create dropdown options
        interface_options = ["Auto-Detect"]
        if self.available_interfaces:
            interface_options.extend([interface['display'] for interface in self.available_interfaces])

        # Set default selection (active interface or auto-detect)
        default_selection = "Auto-Detect"
        if active_interface:
            default_selection = active_interface['display']

        self.interface_dropdown = ctk.CTkComboBox(
            network_frame,
            values=interface_options,
            command=self.on_interface_selected,
            state="readonly"
        )
        self.interface_dropdown.set(default_selection)
        self.interface_dropdown.grid(row=2, column=0, padx=10, pady=(2, 10), sticky="ew")

        # Network Range entry
        ctk.CTkLabel(network_frame, text="Network Range:",
                    font=ctk.CTkFont(size=12)).grid(row=3, column=0, padx=10, pady=(5, 2), sticky="w")

        self.ip_input = ctk.CTkEntry(network_frame, placeholder_text="192.168.1.0/24")
        self.ip_input.grid(row=4, column=0, padx=10, pady=(2, 10), sticky="ew")

        self.auto_detect_btn = ctk.CTkButton(
            network_frame,
            text="Auto-Detect",
            command=self.auto_detect_network,
            height=28
        )
        self.auto_detect_btn.grid(row=5, column=0, padx=8, pady=(4, 4), sticky="ew")
        
        # Network Scan button (moved from tools frame)
        self.scan_btn = ctk.CTkButton(
            network_frame,
            text="Network Scan",
            command=self.toggle_scan,
            height=28
        )
        self.scan_btn.grid(row=6, column=0, padx=8, pady=(4, 8), sticky="ew")
        
        tools_frame = ctk.CTkFrame(self.sidebar)
        tools_frame.grid(row=5, column=0, padx=8, pady=8, sticky="nsew")
        tools_frame.grid_columnconfigure(0, weight=1)
        
        # Configure rows for tools frame
        tools_frame.grid_rowconfigure(0, weight=0)  # Title
        tools_frame.grid_rowconfigure(1, weight=1)  # Live Monitor button
        tools_frame.grid_rowconfigure(2, weight=1)  # SSH button
        tools_frame.grid_rowconfigure(3, weight=1)  # TraceMap button
        tools_frame.grid_rowconfigure(4, weight=1)  # Nmap button
        tools_frame.grid_rowconfigure(5, weight=1)  # Speed test button

        # Tools title
        ctk.CTkLabel(tools_frame, text="Network Tools:",
                    font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")
        
        # Standard button styling for all tools
        button_height = 32  # Reduced height
        button_font = ctk.CTkFont(size=12)  # Smaller font
        
        # Live Monitor Selected button
        self.live_monitor_btn = ctk.CTkButton(
            tools_frame,
            text="Live Monitor",
            command=self.open_live_monitor,
            height=button_height,
            font=button_font
        )
        self.live_monitor_btn.grid(row=1, column=0, padx=8, pady=4, sticky="ew")

        # SSH Selected button
        self.ssh_btn = ctk.CTkButton(
            tools_frame,
            text="SSH",
            command=self.open_ssh_dialog,
            height=button_height,
            font=button_font
        )
        self.ssh_btn.grid(row=2, column=0, padx=8, pady=4, sticky="ew")

        # Traceroute button
        self.traceroute_btn = ctk.CTkButton(
            tools_frame,
            text="Traceroute",
            command=self.open_traceroute_choice_dialog,
            height=button_height,
            font=button_font
        )
        self.traceroute_btn.grid(row=3, column=0, padx=8, pady=4, sticky="ew")

        '''
        # Nmap Scan Selected button
        self.nmap_scan_btn = ctk.CTkButton(
            tools_frame,
            text="Nmap Scan",
            command=self.nmap_scan_selected,
            height=button_height,
            font=button_font
        )
        self.nmap_scan_btn.grid(row=2, column=0, padx=8, pady=4, sticky="ew")
        '''
        # Internet Speed Test button
        self.speedtest_btn = ctk.CTkButton(
            tools_frame,
            text="Internet Speed Test",
            command=self.run_speed_test,
            height=button_height,
            font=button_font
        )
        self.speedtest_btn.grid(row=5, column=0, padx=8, pady=(4, 12), sticky="ew")

        # Network Information frame
        info_frame = ctk.CTkFrame(self.sidebar)
        info_frame.grid(row=6, column=0, padx=8, pady=8, sticky="nsew")
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Configure rows for info frame
        info_frame.grid_rowconfigure(0, weight=0)  # Title
        info_frame.grid_rowconfigure(1, weight=1)  # Local IP
        info_frame.grid_rowconfigure(2, weight=1)  # Subnet
        info_frame.grid_rowconfigure(3, weight=1)  # Gateway
        info_frame.grid_rowconfigure(4, weight=1)  # MAC
        info_frame.grid_rowconfigure(5, weight=1)  # External IP
        info_frame.grid_rowconfigure(6, weight=1)  # Internet status
        
        # Info title
        ctk.CTkLabel(info_frame, text="Network Information:",
                    font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, padx=8, pady=(6, 3), sticky="w")
        
        # Create labels for network info with reduced padding
        self.local_ip_label = ctk.CTkLabel(info_frame, text="Local IP: Detecting...", 
                                          font=ctk.CTkFont(size=12), anchor="w")
        self.local_ip_label.grid(row=1, column=0, padx=8, pady=1, sticky="ew")
        
        self.subnet_label = ctk.CTkLabel(info_frame, text="Subnet: Detecting...", 
                                        font=ctk.CTkFont(size=12), anchor="w")
        self.subnet_label.grid(row=2, column=0, padx=8, pady=1, sticky="ew")
        
        self.gateway_label = ctk.CTkLabel(info_frame, text="Gateway: Detecting...", 
                                         font=ctk.CTkFont(size=12), anchor="w")
        self.gateway_label.grid(row=3, column=0, padx=8, pady=1, sticky="ew")
        
        self.mac_label = ctk.CTkLabel(info_frame, text="MAC: Detecting...", 
                                     font=ctk.CTkFont(size=12), anchor="w")
        self.mac_label.grid(row=4, column=0, padx=8, pady=1, sticky="ew")
        
        self.external_ip_label = ctk.CTkLabel(info_frame, text="External IP: Detecting...", 
                                             font=ctk.CTkFont(size=12), anchor="w")
        self.external_ip_label.grid(row=5, column=0, padx=8, pady=1, sticky="ew")
        
        self.internet_status_label = ctk.CTkLabel(info_frame, text="Internet: Checking...", 
                                                 font=ctk.CTkFont(size=13), anchor="w")
        self.internet_status_label.grid(row=6, column=0, padx=8, pady=(1, 6), sticky="ew")
        
        # Update network information
        self.update_network_information()
    
    def create_main_content(self):
        """Create main content area"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)  # Device table should expand
        
        # Profile buttons will be added at row=0 by profile_manager
        
        # Search frame (without progress bar)
        search_frame = ctk.CTkFrame(self.main_frame)
        search_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)  # Search entry weight (reduced)
        search_frame.grid_columnconfigure(1, weight=0)  # Search button weight
        search_frame.grid_columnconfigure(2, weight=0)  # Clear button weight
        search_frame.grid_columnconfigure(3, weight=2)  # Summary label weight

        # Search entry (half size)
        self.search_input = ctk.CTkEntry(search_frame, placeholder_text="Search devices, I.P, Hostname, Manufacturer...")
        self.search_input.grid(row=0, column=0, padx=(10, 5), pady=0, sticky="ew")
        # Remove the automatic search on typing and add Enter key binding
        self.search_input.bind("<Return>", lambda event: self.perform_search())

        # Search button
        search_button = ctk.CTkButton(search_frame, text="Search", width=70, height=28, command=self.perform_search)
        search_button.grid(row=0, column=1, padx=(0, 5), pady=5)

        # Clear Search button
        clear_search_button = ctk.CTkButton(search_frame, text="Clear Search", width=90, height=28, command=self.clear_search)
        clear_search_button.grid(row=0, column=2, padx=(0, 20), pady=5)

        self.summary_label = ctk.CTkLabel(
            search_frame,
            text="Devices found: 0 | Problematic (>500ms): 0"
        )
        self.summary_label.grid(row=0, column=3, padx=(0, 10), pady=5, sticky="ew")
        
        # Device table frame
        self.table_frame = ctk.CTkScrollableFrame(
            self.main_frame, 
            label_text="Discovered Devices"
        )
        self.table_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        # Create selection controls frame at the top of the scrollable frame
        selection_controls_frame = ctk.CTkFrame(self.table_frame)
        selection_controls_frame.grid(row=0, column=0, columnspan=11, padx=0, pady=(0, 10), sticky="ew")
        
        # Selection buttons on the right
        deselect_all_btn = ctk.CTkButton(
            selection_controls_frame,
            text="Deselect All",
            command=self.deselect_all_devices,
            width=90,
            height=26
        )
        deselect_all_btn.pack(side="right", padx=(5, 10))
        
        select_all_btn = ctk.CTkButton(
            selection_controls_frame,
            text="Select All",
            command=self.select_all_devices,
            width=90,
            height=26
        )
        select_all_btn.pack(side="right", padx=5)
        
        # Configure column weights for spacing - removed profile column
        column_weights = [1, 1, 1, 1, 1, 2, 1, 1, 1, 1]  # Manufacturer column (index 5) gets weight 2
        for i, weight in enumerate(column_weights):
            minsize = 150 if i == 5 else 100  # Manufacturer column gets larger minsize
            self.table_frame.grid_columnconfigure(i, weight=weight, minsize=minsize)
        
        # Table headers - Removed Profile column
        headers = ["Select", "IP Address", "MAC Address", "Hostname", "Friendly Name", "Manufacturer", "Response Time", "Web Service", "Actions", "Notes"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.table_frame, 
                text=header,
                font=ctk.CTkFont(weight="bold")
            )
            if i == 0:  # Left-justify the "Select" header to match checkbox alignment
                label.grid(row=1, column=i, padx=5, pady=5, sticky="w")
            else:
                label.grid(row=1, column=i, padx=5, pady=5, sticky="ew")
        
        self.device_rows = []
    
    def create_status_bar(self):
        """Create status bar with progress bar"""
        # Status and progress container
        bottom_frame = ctk.CTkFrame(self.root, corner_radius=0)
        bottom_frame.grid(row=2, column=1, sticky="ew", padx=20, pady=(0, 20))
        bottom_frame.grid_columnconfigure(0, weight=1)
        
        # Status frame
        self.status_frame = ctk.CTkFrame(bottom_frame, height=30, corner_radius=0)
        self.status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Progress bar frame
        progress_frame = ctk.CTkFrame(bottom_frame, corner_radius=0)
        progress_frame.grid(row=1, column=0, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.set(0)
    
    def get_network_interfaces(self):
        """Get available network interfaces"""
        interfaces = []
        active_interface = None
        
        try:
            import psutil
            # Get network interfaces
            net_interfaces = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()
            
            for interface_name, addresses in net_interfaces.items():
                # Skip loopback interfaces
                if 'loopback' in interface_name.lower() or interface_name.lower() == 'lo':
                    continue
                
                # Get IPv4 address
                ipv4_addr = None
                for addr in addresses:
                    if addr.family == socket.AF_INET:
                        ipv4_addr = addr.address
                        break
                
                if ipv4_addr and not ipv4_addr.startswith('127.') and not ipv4_addr.startswith('169.254.'):
                    # Check if interface is up
                    stats = net_stats.get(interface_name)
                    is_up = stats and stats.isup if stats else False
                    
                    interface_info = {
                        'name': interface_name,
                        'ip': ipv4_addr,
                        'display': f"{interface_name} ({ipv4_addr})",
                        'is_up': is_up
                    }
                    
                    interfaces.append(interface_info)
                    
                    # Set as active if it's up and we don't have one yet
                    if is_up and active_interface is None:
                        active_interface = interface_info
            
            # If no active interface found, try to detect using socket method
            if not active_interface:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                        s.connect(("8.8.8.8", 80))
                        active_ip = s.getsockname()[0]
                        
                        # Find interface with this IP
                        for interface in interfaces:
                            if interface['ip'] == active_ip:
                                active_interface = interface
                                break
                except Exception:
                    pass
            
        except ImportError:
            # Fallback if psutil is not available
            try:
                # Try to get local IP using socket method
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    
                    interface_info = {
                        'name': 'Default',
                        'ip': local_ip,
                        'display': f"Default ({local_ip})",
                        'is_up': True
                    }
                    interfaces.append(interface_info)
                    active_interface = interface_info
            except Exception:
                pass
        except Exception as e:
            print(f"Error getting network interfaces: {e}")
        
        return interfaces, active_interface
    
    def on_interface_selected(self, selection):
        """Handle network interface selection"""
        if selection == "Auto-Detect":
            self.auto_detect_network()
        else:
            # Find the selected interface
            for interface in self.available_interfaces:
                if interface['display'] == selection:
                    # Update IP input with network range for this interface
                    ip_parts = interface['ip'].split('.')
                    network = f"{'.'.join(ip_parts[:3])}.0/24"
                    
                    self.ip_input.delete(0, tk.END)
                    self.ip_input.insert(0, network)
                    
                    self.update_status(f"Selected interface {interface['name']}: {network}")
                    break
    
    def auto_detect_network(self):
        """Auto-detect network range"""
        try:
            # Method 1: Try to get the active network interface
            local_ip = None
            network = None
            
            # First try the socket method (most reliable for active internet connection)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    
                # Convert to network range
                ip_parts = local_ip.split('.')
                network = f"{'.'.join(ip_parts[:3])}.0/24"
                
                self.update_status(f"Auto-detected network via internet connection: {network} (Local IP: {local_ip})")
                
            except Exception as e:
                self.update_status(f"Internet connection method failed: {e}")
                
            # Method 2: If socket method fails, try using psutil to get network interfaces
            if not local_ip:
                try:
                    import psutil
                    interfaces = psutil.net_if_addrs()
                    
                    # Look for active network interfaces (excluding loopback)
                    for interface_name, addresses in interfaces.items():
                        if 'loopback' in interface_name.lower() or 'lo' == interface_name.lower():
                            continue
                            
                        for addr in addresses:
                            if addr.family == socket.AF_INET:  # IPv4
                                ip = addr.address
                                if not ip.startswith('127.') and not ip.startswith('169.254.'):
                                    # Check if this interface is actually active
                                    stats = psutil.net_if_stats().get(interface_name)
                                    if stats and stats.isup:
                                        local_ip = ip
                                        ip_parts = local_ip.split('.')
                                        network = f"{'.'.join(ip_parts[:3])}.0/24"
                                        
                                        self.update_status(f"Auto-detected network via interface {interface_name}: {network} (Local IP: {local_ip})")
                                        break
                        
                        if local_ip:
                            break
                            
                except Exception as e:
                    self.update_status(f"Interface detection method failed: {e}")
            
            # Method 3: If all else fails, try hostname method
            if not local_ip:
                try:
                    local_ip = socket.gethostbyname(socket.gethostname())
                    if not local_ip.startswith('127.'):
                        ip_parts = local_ip.split('.')
                        network = f"{'.'.join(ip_parts[:3])}.0/24"
                        
                        self.update_status(f"Auto-detected network via hostname: {network} (Local IP: {local_ip})")
                    else:
                        local_ip = None
                        
                except Exception as e:
                    self.update_status(f"Hostname method failed: {e}")
            
            # Update UI with detected network
            if network:
                self.ip_input.delete(0, tk.END)
                self.ip_input.insert(0, network)
                
                # Update status to show current network
                self.update_status(f"Ready to scan network: {network}")
                
                # Clear any previous scan results since we're on a new network
                if hasattr(self, 'all_devices') and self.all_devices:
                    self.clear_device_table()
                    self.update_status(f"Cleared previous results - ready to scan new network: {network}")
                
                return network
            else:
                self.update_status("Failed to auto-detect network. Please enter manually.")
                return None
                
        except Exception as e:
            self.update_status(f"Auto-detect failed: {e}")
            return None
    
    def detect_network_change(self):
        """Detect if the network has changed and update accordingly"""
        current_network = self.ip_input.get().strip()
        detected_network = self.auto_detect_network()
        
        if detected_network and current_network != detected_network:
            # Network has changed
            if messagebox.askyesno(
                "Network Change Detected", 
                f"Network change detected!\n\nPrevious: {current_network}\nCurrent: {detected_network}\n\nWould you like to clear the previous scan results and scan the new network?",
                icon="question"
            ):
                self.clear_device_table()
                self.update_status(f"Network changed from {current_network} to {detected_network}")
                return True
            else:
                # User chose to keep the old network, restore it
                self.ip_input.delete(0, tk.END)
                self.ip_input.insert(0, current_network)
                self.update_status(f"Keeping previous network: {current_network}")
                return False
        
        return detected_network is not None
    
    def toggle_scan(self):
        """Toggle network scanning"""
        if not self.scanning:
            self.start_scan()
        else:
            self.stop_scan()
    
    def start_scan(self):
        """Start network scan"""
        ip_range = self.ip_input.get().strip()
        if not ip_range:
            messagebox.showerror("Error", "Please enter an IP range")
            return
        
        # Validate IP range format
        try:
            test_network = ipaddress.ip_network(ip_range, strict=False)
            self.update_status(f"Starting scan of {ip_range} ({len(list(test_network.hosts()))} hosts)")
        except ValueError as e:
            messagebox.showerror("Invalid IP Range", f"The IP range '{ip_range}' is not valid.\n\nError: {e}\n\nExample formats:\n- 192.168.1.0/24\n- 10.0.0.0/24\n- 172.16.0.0/24")
            return
        
        self.scanning = True
        self.scan_btn.configure(text="Stop Scan", fg_color="#d32f2f")
        self.progress_bar.set(0)
        self.update_status(f"Scanning {ip_range}...")
        
        # Clear previous results
        self.clear_device_table()
        
        # Start scan thread
        self.scan_thread = threading.Thread(target=self.scan_network, args=(ip_range,))
        self.scan_thread.daemon = True
        self.scan_thread.start()
    
    def stop_scan(self):
        """Stop network scan"""
        self.scanning = False
        if self.scanner:
            self.scanner.stop()
        self.scan_btn.configure(text="Network Scan", fg_color="#1f538d")
        self.update_status("Scan stopped by user")
    
    def scan_network(self, ip_range):
        """Network scanning thread"""
        try:
            # Disable real-time device updates for better performance
            self.scanner = NetworkScanner(
                ip_range, 
                progress_callback=self.update_progress,
                device_callback=None  # Don't update UI for each device
            )
            
            devices = self.scanner.scan()
            
            if self.scanning:
                self.root.after(0, lambda: self.scan_completed(devices))
                
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"Scan error: {e}"))
    
    def update_progress(self, value):
        """Update progress bar"""
        self.root.after(0, lambda: self.progress_bar.set(value / 100))
    
    def add_device_found(self, device):
        """Add device to table when found"""
        self.root.after(0, lambda: self.add_device_to_table(device))
    
    def scan_completed(self, devices):
        """Handle scan completion"""
        self.all_devices = devices
        self.scanning = False
        self.scan_btn.configure(text="Network Scan", fg_color="#1f538d")
        self.progress_bar.set(1.0)
        
        # Sort devices by IP address for consistent display
        devices.sort(key=lambda d: tuple(map(int, d['ip'].split('.'))))
        
        # Batch add all devices at once for better performance
        self.batch_add_devices(devices)
        
        # Update summary
        problematic = sum(1 for d in devices if d.get('response_time', 0) * 1000 > 500)
        self.summary_label.configure(text=f"Devices found: {len(devices)} | Problematic (>500ms): {problematic}")
        
        self.update_status(f"Scan completed. Found {len(devices)} devices.")
    
    def clear_device_table(self):
        """Clear device table"""
        for row in self.device_rows:
            for widget in row:
                widget.destroy()
        self.device_rows.clear()
        self.all_devices.clear()
        self.selected_devices.clear()
        
        # Reset summary
        self.summary_label.configure(text="Devices found: 0 | Problematic (>500ms): 0")
        
        # Update loaded profile label if profile manager exists
        if hasattr(self, 'profile_manager') and hasattr(self.profile_manager, 'loaded_profile_label'):
            self.profile_manager.loaded_profile_label.configure(text="No profile loaded")
    
    def refresh_device_table(self):
        """Refresh the device table by clearing and re-adding all devices"""
        # Clear only the widgets, not the device data
        for row in self.device_rows:
            for widget in row:
                widget.destroy()
        self.device_rows.clear()
        
        # Re-add all devices to the table
        for device in self.all_devices:
            self.add_device_to_table(device)
            
        # Update summary
        problematic = sum(1 for d in self.all_devices if d.get('response_time', 0) * 1000 > 500)
        self.summary_label.configure(text=f"Devices found: {len(self.all_devices)} | Problematic (>500ms): {problematic}")
    
    def batch_add_devices(self, devices):
        """Batch add multiple devices to table for better performance"""
        # Freeze UI updates
        self.table_frame.configure(label_text="Discovered Devices - Loading...")
        
        # Add all devices
        for device in devices:
            self.add_device_to_table(device, batch_mode=True)
        
        # Restore label and force single UI update
        self.table_frame.configure(label_text="Discovered Devices")
        self.table_frame.update_idletasks()
        
        # Load notes for all devices in background
        self.load_notes_for_devices_background(devices)
    
    def add_device_to_table(self, device, batch_mode=False):
        """Add device to table"""
        if not device:
            return
            
        # Debug: Print device structure
        print(f"DEBUG: Adding device to table: {device}")
        print(f"DEBUG: Device keys: {list(device.keys())}")
            
        row_num = len(self.device_rows) + 2  # +2 because row 0 is controls, row 1 is headers
        row_widgets = []
        
        # Ensure device has all required fields with defaults
        device_data = {
            'ip': device.get('ip', 'Unknown'),
            'mac': device.get('mac', 'Unknown'),
            'hostname': device.get('hostname', 'Unknown'),
            'friendly_name': device.get('friendly_name', ''),
            'manufacturer': device.get('manufacturer', 'Unknown'),
            'response_time': device.get('response_time', 0),
            'web_service': device.get('web_service', None),
            'notes': device.get('notes', '')
        }
        
        print(f"DEBUG: Processed device_data: {device_data}")
        
        # Select checkbox - Column 0
        var = tk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            self.table_frame, 
            text="",
            variable=var,
            command=lambda: self.toggle_device_selection(device, var.get())
        )
        checkbox.grid(row=row_num, column=0, padx=5, pady=2, sticky="w")
        row_widgets.append(checkbox)
        
        # IP Address - Column 1
        ip_label = ctk.CTkLabel(self.table_frame, text=device_data['ip'])
        ip_label.grid(row=row_num, column=1, padx=5, pady=2)
        row_widgets.append(ip_label)

        # MAC Address - Column 2
        mac_label = ctk.CTkLabel(self.table_frame, text=device_data['mac'])
        mac_label.grid(row=row_num, column=2, padx=5, pady=2)
        row_widgets.append(mac_label)
        
        # Hostname - Column 3
        hostname_label = ctk.CTkLabel(self.table_frame, text=device_data['hostname'])
        hostname_label.grid(row=row_num, column=3, padx=5, pady=2)
        row_widgets.append(hostname_label)
        
        # Friendly Name - Column 4
        friendly_name_text = device_data['friendly_name'] if device_data['friendly_name'] else '-'
        friendly_name_label = ctk.CTkLabel(self.table_frame, text=friendly_name_text)
        friendly_name_label.grid(row=row_num, column=4, padx=5, pady=2)
        row_widgets.append(friendly_name_label)

        # Manufacturer - Column 5
        manufacturer_label = ctk.CTkLabel(self.table_frame, text=device_data['manufacturer'])
        manufacturer_label.grid(row=row_num, column=5, padx=5, pady=2)
        row_widgets.append(manufacturer_label)
        
        # Response Time (moved from column 7 to column 6)
        response_ms = device.get('response_time', 0) * 1000
        response_color = "#f44336" if response_ms > 500 else None
        response_label = ctk.CTkLabel(
            self.table_frame, 
            text=f"{response_ms:.0f}ms",
            text_color=response_color
        )
        response_label.grid(row=row_num, column=6, padx=5, pady=2)
        row_widgets.append(response_label)
        
        # Web Service (moved from column 8 to column 7)
        web_service = device.get('web_service')
        if web_service:
            web_label = ctk.CTkLabel(
                self.table_frame,
                text="Open",
                text_color="#1f538d",  # Blue color to indicate clickability
                cursor="hand2"
            )
            web_label.grid(row=row_num, column=7, padx=5, pady=2)
            
            # Add click event and hover effects
            web_label.bind("<Button-1>", lambda e: webbrowser.open(web_service))
            web_label.bind("<Enter>", lambda e: web_label.configure(text_color="#0d47a1"))  # Darker blue on hover
            web_label.bind("<Leave>", lambda e: web_label.configure(text_color="#1f538d"))  # Original blue
            
            row_widgets.append(web_label)
        else:
            web_label = ctk.CTkLabel(self.table_frame, text="None")
            web_label.grid(row=row_num, column=7, padx=5, pady=2)
            row_widgets.append(web_label)
        
        # Actions clickable labels (moved from column 9 to column 8)
        actions_frame = ctk.CTkFrame(self.table_frame)
        actions_frame.grid(row=row_num, column=8, padx=5, pady=2)

        # Details clickable label
        details_label = ctk.CTkLabel(
            actions_frame,
            text="Details",
            text_color="#1f538d",  # Blue color to indicate clickability
            cursor="hand2"
        )
        details_label.grid(row=0, column=0, padx=2, pady=1)
        
        # Add click event and hover effects for Details
        details_label.bind("<Button-1>", lambda e, dev=device: self.show_device_details(dev))
        details_label.bind("<Enter>", lambda e: details_label.configure(text_color="#0d47a1"))  # Darker blue on hover
        details_label.bind("<Leave>", lambda e: details_label.configure(text_color="#1f538d"))  # Original blue

        # Nmap clickable label
        nmap_label = ctk.CTkLabel(
            actions_frame,
            text="Nmap",
            text_color="#1f538d",  # Blue color to indicate clickability
            cursor="hand2"
        )
        nmap_label.grid(row=0, column=1, padx=2, pady=1)
        
        # Add click event and hover effects for Nmap
        nmap_label.bind("<Button-1>", lambda e, dev=device: self.show_nmap_dialog(dev.get('ip')))
        nmap_label.bind("<Enter>", lambda e: nmap_label.configure(text_color="#0d47a1"))  # Darker blue on hover
        nmap_label.bind("<Leave>", lambda e: nmap_label.configure(text_color="#1f538d"))  # Original blue

        row_widgets.append(actions_frame)

        # Notes clickable label (new column)
        notes_text = device.get('notes', '').strip()
        has_notes = bool(notes_text)
        
        notes_label = ctk.CTkLabel(
            self.table_frame,
            text="View Notes" if has_notes else "Add Notes",
            text_color="#4CAF50" if has_notes else "#1f538d",  # Green if has notes, blue otherwise
            cursor="hand2"
        )
        notes_label.grid(row=row_num, column=9, padx=5, pady=2)
        
        # Add click event and hover effects for Notes
        notes_label.bind("<Button-1>", lambda e, dev=device: self.show_notes_dialog(dev))
        if has_notes:
            notes_label.bind("<Enter>", lambda e: notes_label.configure(text_color="#2E7D32"))  # Darker green on hover
            notes_label.bind("<Leave>", lambda e: notes_label.configure(text_color="#4CAF50"))  # Original green
        else:
            notes_label.bind("<Enter>", lambda e: notes_label.configure(text_color="#0d47a1"))  # Darker blue on hover
            notes_label.bind("<Leave>", lambda e: notes_label.configure(text_color="#1f538d"))  # Original blue
        
        row_widgets.append(notes_label)

        self.device_rows.append(row_widgets)
        
        # Only update the UI if not in batch mode
        if not batch_mode:
            self.table_frame.update_idletasks()

    def toggle_device_selection(self, device, selected):
        """Toggle device selection for monitoring"""
        if selected:
            if device not in self.selected_devices:
                self.selected_devices.append(device)
        else:
            if device in self.selected_devices:
                self.selected_devices.remove(device)
    
    def select_all_devices(self):
        """Select all devices in the table"""
        # Clear existing selections
        self.selected_devices.clear()
        
        # Select all devices and update checkboxes
        for i, device in enumerate(self.all_devices):
            self.selected_devices.append(device)
            # Update checkbox widget (first widget in each row)
            if i < len(self.device_rows):
                checkbox = self.device_rows[i][0]
                if hasattr(checkbox, 'select'):
                    checkbox.select()
        
        self.update_status(f"Selected all {len(self.all_devices)} devices")
    
    def deselect_all_devices(self):
        """Deselect all devices in the table"""
        # Clear selections
        self.selected_devices.clear()
        
        # Update all checkboxes to unchecked
        for i in range(len(self.device_rows)):
            checkbox = self.device_rows[i][0]
            if hasattr(checkbox, 'deselect'):
                checkbox.deselect()
        
        self.update_status("Deselected all devices")
    
    def perform_search(self):
        """Perform device search"""
        query = self.search_input.get().lower().strip()

        # Clear current table
        for row in self.device_rows:
            for widget in row:
                widget.destroy()
        self.device_rows.clear()
        
        if not query:
            # If query is empty, re-add all devices
            for device in self.all_devices:
                self.add_device_to_table(device)
            self.update_status("Showing all devices")
            return

        # Re-add filtered devices with exact match on IP, MAC, Hostname or Manufacturer
        matched_count = 0
        for device in self.all_devices:
            if (query == device['ip'].lower() or
                query == device.get('mac', '').lower() or
                query == device.get('hostname', '').lower() or
                query == device.get('manufacturer', '').lower()):
                self.add_device_to_table(device)
                matched_count += 1

        self.update_status(f"Search completed. Found {matched_count} devices matching '{query}' (exact match)")

    def clear_search(self):
        """Clear search input and show all devices"""
        # Clear the search input
        self.search_input.delete(0, tk.END)
        
        # Clear current table
        for row in self.device_rows:
            for widget in row:
                widget.destroy()
        self.device_rows.clear()
        
        # Re-add all devices to the table
        for device in self.all_devices:
            self.add_device_to_table(device)
        
        # Update summary
        problematic = sum(1 for d in self.all_devices if d.get('response_time', 0) * 1000 > 500)
        self.summary_label.configure(text=f"Devices found: {len(self.all_devices)} | Problematic (>500ms): {problematic}")
        
        self.update_status("Search cleared - showing all devices")

    def nmap_scan_selected(self):
        """Handle Nmap scan for selected devices"""
        if not NMAP_AVAILABLE:
            messagebox.showerror("Nmap Not Available", "Nmap monitor module is not available.")
            return

        if not self.selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device to scan.")
            return

        # Check if more than one device is selected
        if len(self.selected_devices) > 1:
            messagebox.showwarning(
                "Multiple Devices Selected",
                f"You have selected {len(self.selected_devices)} devices. Nmap can only scan one device at a time.\n\nPlease select only one device and try again."
            )
            return

        # Get the selected device
        selected_device = self.selected_devices[0]
        ip = selected_device['ip']

        # Use the existing nmap_monitor to show the dialog
        if self.nmap_monitor:
            self.nmap_monitor.show_nmap_dialog(ip)
        else:
            # Fallback to the built-in nmap functionality
            self.show_nmap_dialog(ip)

    def show_nmap_dialog(self, ip):
        """Show nmap options dialog"""
        nmap_window = ctk.CTkToplevel(self.root)
        nmap_window.title(f"Nmap Options for {ip}")
        nmap_window.geometry("800x600")
        nmap_window.transient(self.root)
        set_dialog_icon(nmap_window)
        
        # Info label
        info_label = ctk.CTkLabel(
            nmap_window,
            text=f"Select an Nmap scan to run on {ip}:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        info_label.pack(pady=20)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(nmap_window)
        buttons_frame.pack(pady=10, padx=20, fill="x")
        
        # Nmap scan buttons
        scans = [
            ("Quick Scan", ["-F"]),
            ("OS Detection", ["-O"]),
            ("Port Scan", ["-p", "1-10000"]),
            ("Service Version", ["-sV"]),
            ("Top 100 Ports", ["--top-ports", "100"]),
            ("Firewall Evasion", ["-f"]),
            ("Traceroute", ["--traceroute"])
        ]
        
        for i, (name, args) in enumerate(scans):
            btn = ctk.CTkButton(
                buttons_frame,
                text=name,
                command=lambda a=args: self.run_nmap(ip, a, result_text)
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="ew")
            buttons_frame.grid_columnconfigure(i%3, weight=1)
        
        # Results text area
        result_text = ctk.CTkTextbox(nmap_window, font=ctk.CTkFont(family="Consolas", size=13))
        result_text.pack(pady=20, padx=20, fill="both", expand=True)
    
    def run_nmap(self, ip, args, result_widget):
        """Run nmap scan"""
        result_widget.delete("1.0", "end")
        result_widget.insert("1.0", "Scanning...")
        
        def nmap_thread():
            try:
                if platform.system().lower() == 'windows':
                    result = subprocess.run(
                        ['nmap'] + args + [ip],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    result = subprocess.run(
                        ['nmap'] + args + [ip],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                output = result.stdout or result.stderr
            except subprocess.TimeoutExpired:
                output = "Nmap scan timed out"
            except FileNotFoundError:
                output = self.get_nmap_installation_message()
            except Exception as e:
                output = f"Error running nmap: {e}"
            
            self.root.after(0, lambda: self.update_nmap_result(result_widget, output))
        
        threading.Thread(target=nmap_thread, daemon=True).start()
    
    def get_nmap_installation_message(self):
        """Get detailed nmap installation instructions"""
        os_name = platform.system().lower()
        
        if os_name == "windows":
            return """NMAP NOT FOUND - Installation Required

Nmap is not installed on your system. To use network scanning features, please install Nmap:

📋 INSTALLATION INSTRUCTIONS FOR WINDOWS:

1. Visit the official Nmap website:
   https://nmap.org/download.html

2. Download the Windows installer:
   - Look for "Latest stable release self-installer"
   - Download the .exe file (usually named nmap-X.XX-setup.exe)

3. Install Nmap:
   - Run the downloaded .exe file as Administrator
   - Follow the installation wizard
   - Make sure to check "Add Nmap to PATH" during installation

4. Restart the application:
   - Close this Network Monitor application
   - Restart it after Nmap installation completes

💡 ALTERNATIVE INSTALLATION METHODS:

• Using Chocolatey (if installed):
  choco install nmap

• Using Windows Package Manager:
  winget install Insecure.Nmap

⚠️  IMPORTANT NOTES:
- Nmap requires administrator privileges for some scan types
- Windows Defender or antivirus may flag Nmap (this is normal)
- Add Nmap to your antivirus whitelist if needed

🔄 After installation, try the scan again."""
        
        elif os_name == "darwin":  # macOS
            return """NMAP NOT FOUND - Installation Required

Nmap is not installed on your system. To use network scanning features, please install Nmap:

📋 INSTALLATION INSTRUCTIONS FOR macOS:

1. Using Homebrew (Recommended):
   brew install nmap

2. Using MacPorts:
   sudo port install nmap

3. Manual Installation:
   - Visit: https://nmap.org/download.html
   - Download the macOS installer (.dmg file)
   - Run the installer and follow instructions

4. Restart the application after installation.

🔄 After installation, try the scan again."""
        
        else:  # Linux and others
            return """NMAP NOT FOUND - Installation Required

Nmap is not installed on your system. To use network scanning features, please install Nmap:

📋 INSTALLATION INSTRUCTIONS FOR LINUX:

• Ubuntu/Debian:
  sudo apt update
  sudo apt install nmap

• CentOS/RHEL/Fedora:
  sudo yum install nmap     (or: sudo dnf install nmap)

• Arch Linux:
  sudo pacman -S nmap

• From source:
  Visit https://nmap.org/download.html

🔄 After installation, try the scan again."""
    
    
    def update_nmap_result(self, widget, result):
        """Update nmap result display"""
        widget.delete("1.0", "end")
        widget.insert("1.0", result)
    
    def show_device_details(self, device):
        """Show device details dialog"""
        details_window = ctk.CTkToplevel(self.root)
        details_window.title(f"Device Details - {device['ip']}")
        details_window.geometry("400x300")
        details_window.transient(self.root)
        set_dialog_icon(details_window)
        
        details_text = f"""
Device Information:
IP Address: {device['ip']}
MAC Address: {device.get('mac', 'Unknown')}
Hostname: {device.get('hostname', 'Unknown')}
Manufacturer: {device.get('manufacturer', 'Unknown')}
Response Time: {device.get('response_time', 0) * 1000:.1f}ms
Web Service: {device.get('web_service', 'None')}
Status: {device.get('status', 'Unknown')}
        """
        
        details_label = ctk.CTkLabel(
            details_window,
            text=details_text,
            justify="left",
            font=ctk.CTkFont(family="Consolas")
        )
        details_label.pack(padx=20, pady=20, fill="both", expand=True)
    
    def show_notes_dialog(self, device):
        """Show notes dialog for viewing/editing device notes"""
        import sqlite3
        
        notes_window = ctk.CTkToplevel(self.root)
        notes_window.title(f"Device Notes - {device['ip']}")
        notes_window.geometry("500x400")
        notes_window.transient(self.root)
        set_dialog_icon(notes_window)
        notes_window.grab_set()  # Make modal
        
        # Center the window
        notes_window.update_idletasks()
        x = (notes_window.winfo_screenwidth() // 2) - (notes_window.winfo_width() // 2)
        y = (notes_window.winfo_screenheight() // 2) - (notes_window.winfo_height() // 2)
        notes_window.geometry(f"+{x}+{y}")
        
        # Device info frame
        info_frame = ctk.CTkFrame(notes_window)
        info_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Display device info
        device_info = f"IP: {device['ip']} | MAC: {device.get('mac', 'Unknown')} | Hostname: {device.get('hostname', 'Unknown')}"
        ctk.CTkLabel(
            info_frame,
            text=device_info,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)

        # Notes text area
        notes_label = ctk.CTkLabel(
            notes_window,
            text="Notes:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        notes_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        notes_textbox = ctk.CTkTextbox(
            notes_window,
            height=200,
            font=ctk.CTkFont(size=12)
        )
        notes_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Load existing notes from dedicated notes table
        existing_notes = self.load_device_notes(device.get('mac', ''))
        notes_textbox.insert("1.0", existing_notes)
        
        # Button frame
        button_frame = ctk.CTkFrame(notes_window)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def save_notes():
            """Save notes to database and update device"""
            new_notes = notes_textbox.get("1.0", "end-1c").strip()
            
            # Update device object
            device['notes'] = new_notes
            
            # Save notes to dedicated notes table (MAC-based, not profile-based)
            mac_address = device.get('mac', '')
            if mac_address and mac_address.upper() != 'UNKNOWN':
                try:
                    success = self.save_device_notes(mac_address, new_notes)
                    if success:
                        messagebox.showinfo("Success", "Notes saved successfully!")
                        # Also update in Profile table if device has a profile
                        if device.get('profile'):
                            self.update_profile_notes(device.get('profile'), mac_address, new_notes)
                    else:
                        messagebox.showerror("Error", "Failed to save notes to database.")
                        return  # Don't close dialog if there was an error
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save notes: {str(e)}")
                    return  # Don't close dialog if there was an error
            else:
                # No valid MAC address, just update in memory
                messagebox.showinfo("Note", "Notes saved for this session only (no MAC address).")
            
            # Update all devices in memory with the same MAC address
            self.update_all_device_notes(mac_address, new_notes)
            
            # Refresh the device table to update the notes button
            self.refresh_device_table()
            notes_window.destroy()  # Close dialog after successful save
        
        def clear_notes():
            """Clear the notes text area"""
            notes_textbox.delete("1.0", "end")
            notes_textbox.focus()
        
        # Create a centered container frame for buttons
        button_container = ctk.CTkFrame(button_frame)
        button_container.pack(expand=True)  # Center the container
        
        # Buttons - now centered
        save_btn = ctk.CTkButton(
            button_container,
            text="Save",
            command=save_notes,
            width=100
        )
        save_btn.pack(side="left", padx=5)
        
        clear_btn = ctk.CTkButton(
            button_container,
            text="Clear",
            command=clear_notes,
            width=100
        )
        clear_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_container,
            text="Cancel",
            command=notes_window.destroy,
            width=100
        )
        cancel_btn.pack(side="left", padx=5)
        
        # Focus on text area
        notes_textbox.focus()
    
    def open_ssh_dialog(self):
        """Open SSH connection dialog for selected devices"""
        if not self.selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device to SSH into.")
            return

        # If multiple devices selected, let user choose one
        if len(self.selected_devices) > 1:
            # Create device selection dialog
            selection_window = ctk.CTkToplevel(self.root)
            selection_window.title("Select Device for SSH")
            selection_window.geometry("400x300")
            selection_window.transient(self.root)
            set_dialog_icon(selection_window)
            selection_window.grab_set()

            # Center the window
            selection_window.update_idletasks()
            x = (selection_window.winfo_screenwidth() // 2) - (selection_window.winfo_width() // 2)
            y = (selection_window.winfo_screenheight() // 2) - (selection_window.winfo_height() // 2)
            selection_window.geometry(f"+{x}+{y}")

            ctk.CTkLabel(
                selection_window,
                text="Multiple devices selected. Choose one for SSH:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=20)

            # Device list frame
            list_frame = ctk.CTkScrollableFrame(selection_window)
            list_frame.pack(fill="both", expand=True, padx=20, pady=10)

            selected_device = None

            def select_device(device):
                nonlocal selected_device
                selected_device = device
                selection_window.destroy()
                self.show_ssh_connection_dialog(device)

            # Add device buttons
            for device in self.selected_devices:
                device_info = f"{device['ip']} - {device.get('hostname', 'Unknown')}"
                btn = ctk.CTkButton(
                    list_frame,
                    text=device_info,
                    command=lambda d=device: select_device(d)
                )
                btn.pack(fill="x", pady=5)

            # Cancel button
            cancel_btn = ctk.CTkButton(
                selection_window,
                text="Cancel",
                command=selection_window.destroy
            )
            cancel_btn.pack(pady=10)

        else:
            # Single device selected
            self.show_ssh_connection_dialog(self.selected_devices[0])

    def show_ssh_connection_dialog(self, device):
        """Show SSH connection dialog for a specific device"""
        if not SSH_AVAILABLE:
            self.show_ssh_installation_dialog(device)
            return

        ssh_window = ctk.CTkToplevel(self.root)
        ssh_window.title(f"SSH Connection - {device['ip']}")
        ssh_window.geometry("500x400")
        ssh_window.transient(self.root)
        ssh_window.grab_set()

        # Center the window
        ssh_window.update_idletasks()
        x = (ssh_window.winfo_screenwidth() // 2) - (ssh_window.winfo_width() // 2)
        y = (ssh_window.winfo_screenheight() // 2) - (ssh_window.winfo_height() // 2)
        ssh_window.geometry(f"+{x}+{y}")

        # Device info
        info_frame = ctk.CTkFrame(ssh_window)
        info_frame.pack(fill="x", padx=20, pady=20)

        device_info = f"Connecting to: {device['ip']} ({device.get('hostname', 'Unknown')})"
        ctk.CTkLabel(
            info_frame,
            text=device_info,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)

        # Connection form
        form_frame = ctk.CTkFrame(ssh_window)
        form_frame.pack(fill="x", padx=20, pady=10)

        # Username
        ctk.CTkLabel(form_frame, text="Username:").pack(anchor="w", padx=10, pady=(10, 5))
        username_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter username")
        username_entry.pack(fill="x", padx=10, pady=(0, 10))
        username_entry.focus()

        # Password
        ctk.CTkLabel(form_frame, text="Password:").pack(anchor="w", padx=10, pady=(0, 5))
        password_entry = ctk.CTkEntry(form_frame, placeholder_text="Enter password", show="*")
        password_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Port
        ctk.CTkLabel(form_frame, text="Port:").pack(anchor="w", padx=10, pady=(0, 5))
        port_entry = ctk.CTkEntry(form_frame, placeholder_text="22")
        port_entry.insert(0, "22")
        port_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Status label
        status_label = ctk.CTkLabel(ssh_window, text="")
        status_label.pack(pady=10)

        # Button frame
        button_frame = ctk.CTkFrame(ssh_window)
        button_frame.pack(fill="x", padx=20, pady=20)

        def connect_ssh():
            """Attempt SSH connection"""
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            port = port_entry.get().strip() or "22"

            if not username:
                status_label.configure(text="Please enter a username", text_color="#f44336")
                return

            if not password:
                status_label.configure(text="Please enter a password", text_color="#f44336")
                return

            try:
                port_num = int(port)
            except ValueError:
                status_label.configure(text="Invalid port number", text_color="#f44336")
                return

            # Disable buttons during connection
            connect_btn.configure(state="disabled", text="Connecting...")
            status_label.configure(text="Connecting...", text_color="#2196f3")
            ssh_window.update()

            # Attempt connection in a thread
            def ssh_connect_thread():
                try:
                    # Create SSH client
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    # Connect
                    ssh_client.connect(
                        hostname=device['ip'],
                        port=port_num,
                        username=username,
                        password=password,
                        timeout=10
                    )

                    # Connection successful
                    ssh_window.after(0, lambda: connection_successful(ssh_client))

                except paramiko.AuthenticationException:
                    ssh_window.after(0, lambda: connection_failed("Authentication failed - check username/password"))
                except paramiko.SSHException as e:
                    ssh_window.after(0, lambda: connection_failed(f"SSH connection error: {str(e)}"))
                except socket.timeout:
                    ssh_window.after(0, lambda: connection_failed("Connection timeout - device may not be reachable"))
                except Exception as e:
                    ssh_window.after(0, lambda: connection_failed(f"Connection error: {str(e)}"))

            threading.Thread(target=ssh_connect_thread, daemon=True).start()

        def connection_successful(ssh_client):
            """Handle successful SSH connection"""
            status_label.configure(text="Connected successfully!", text_color="#4caf50")
            connect_btn.configure(state="normal", text="Connect")

            # Close the connection dialog and open SSH terminal
            ssh_window.destroy()
            self.open_ssh_terminal(device, ssh_client)

        def connection_failed(error_msg):
            """Handle failed SSH connection"""
            status_label.configure(text=error_msg, text_color="#f44336")
            connect_btn.configure(state="normal", text="Connect")

        # Connect button
        connect_btn = ctk.CTkButton(
            button_frame,
            text="Connect",
            command=connect_ssh
        )
        connect_btn.pack(side="left", padx=5)

        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=ssh_window.destroy
        )
        cancel_btn.pack(side="left", padx=5)

        # Bind Enter key to connect
        def on_enter(event):
            connect_ssh()

        username_entry.bind("<Return>", on_enter)
        password_entry.bind("<Return>", on_enter)
        port_entry.bind("<Return>", on_enter)

    def open_ssh_terminal(self, device, ssh_client):
        """Open SSH terminal window"""
        terminal_window = ctk.CTkToplevel(self.root)
        terminal_window.title(f"SSH Terminal - {device['ip']}")
        terminal_window.geometry("800x600")
        terminal_window.transient(self.root)

        # Terminal frame
        terminal_frame = ctk.CTkFrame(terminal_window)
        terminal_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Output text area
        output_text = ctk.CTkTextbox(
            terminal_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word"
        )
        output_text.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # Command input
        input_frame = ctk.CTkFrame(terminal_frame)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(input_frame, text="$", font=ctk.CTkFont(family="Consolas", size=12)).pack(side="left", padx=(5, 2))

        command_entry = ctk.CTkEntry(
            input_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            placeholder_text="Enter command..."
        )
        command_entry.pack(fill="x", side="left", padx=(0, 5))
        command_entry.focus()

        send_btn = ctk.CTkButton(
            input_frame,
            text="Send",
            width=60
        )
        send_btn.pack(side="right", padx=5)

        # Add welcome message
        output_text.insert("end", f"Connected to {device['ip']}\n")
        output_text.insert("end", f"Hostname: {device.get('hostname', 'Unknown')}\n")
        output_text.insert("end", "Type 'exit' to close connection.\n\n")

        def execute_command():
            """Execute SSH command"""
            command = command_entry.get().strip()
            if not command:
                return

            # Add command to output
            output_text.insert("end", f"$ {command}\n")
            command_entry.delete(0, "end")

            if command.lower() in ['exit', 'quit', 'logout']:
                # Close connection
                ssh_client.close()
                output_text.insert("end", "Connection closed.\n")
                terminal_window.after(2000, terminal_window.destroy)
                return

            # Execute command in thread
            def command_thread():
                try:
                    stdin, stdout, stderr = ssh_client.exec_command(command, timeout=30)

                    # Read output
                    output = stdout.read().decode('utf-8', errors='replace')
                    error = stderr.read().decode('utf-8', errors='replace')

                    # Update UI in main thread
                    terminal_window.after(0, lambda: display_output(output, error))

                except Exception as e:
                    terminal_window.after(0, lambda: display_output("", f"Command error: {str(e)}"))

            threading.Thread(target=command_thread, daemon=True).start()

        def display_output(stdout_text, stderr_text):
            """Display command output"""
            if stdout_text:
                output_text.insert("end", stdout_text)
            if stderr_text:
                output_text.insert("end", f"Error: {stderr_text}")
            output_text.insert("end", "\n")
            output_text.see("end")

        # Bind Enter key and button
        command_entry.bind("<Return>", lambda event: execute_command())
        send_btn.configure(command=execute_command)

        # Handle window close
        def on_close():
            try:
                ssh_client.close()
            except:
                pass
            terminal_window.destroy()

        terminal_window.protocol("WM_DELETE_WINDOW", on_close)

    def show_ssh_installation_dialog(self, device):
        """Show SSH installation instructions when paramiko is not available"""
        install_window = ctk.CTkToplevel(self.root)
        install_window.title("SSH Support Required")
        install_window.geometry("600x500")
        install_window.transient(self.root)
        install_window.grab_set()

        # Center the window
        install_window.update_idletasks()
        x = (install_window.winfo_screenwidth() // 2) - (install_window.winfo_width() // 2)
        y = (install_window.winfo_screenheight() // 2) - (install_window.winfo_height() // 2)
        install_window.geometry(f"+{x}+{y}")

        # Instructions text
        instructions = """SSH SUPPORT NOT AVAILABLE

To use SSH functionality, you need to install the 'paramiko' library.

INSTALLATION INSTRUCTIONS:

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)

2. Install paramiko using pip:
   pip install paramiko

3. Alternative installation methods:
   • Using conda: conda install paramiko
   • Using pip3: pip3 install paramiko

4. Restart the application after installation

ALTERNATIVE SSH OPTIONS:

• Use built-in SSH client:
  - Windows: ssh username@{ip}
  - Mac/Linux: ssh username@{ip}

• Use dedicated SSH clients:
  - PuTTY (Windows)
  - Terminal (Mac/Linux)
  - MobaXterm (Windows)

After installing paramiko, you'll be able to SSH directly from this application.""".format(ip=device['ip'])

        text_widget = ctk.CTkTextbox(
            install_window,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        text_widget.pack(fill="both", expand=True, padx=20, pady=20)
        text_widget.insert("1.0", instructions)
        text_widget.configure(state="disabled")

        # Buttons
        button_frame = ctk.CTkFrame(install_window)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def open_external_ssh():
            """Try to open external SSH client"""
            ip = device['ip']
            try:
                if platform.system().lower() == 'windows':
                    # Try to use Windows SSH client
                    subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', f'ssh root@{ip}'],
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    # Mac/Linux
                    subprocess.Popen(['ssh', f'root@{ip}'])

                install_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not launch external SSH client: {e}")

        external_btn = ctk.CTkButton(
            button_frame,
            text=f"Open External SSH to {device['ip']}",
            command=open_external_ssh
        )
        external_btn.pack(side="left", padx=5)

        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=install_window.destroy
        )
        close_btn.pack(side="right", padx=5)

    def open_live_monitor(self):
        """Open live monitoring window for selected devices"""
        if not self.selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device to monitor.")
            return
        
        if LIVE_MONITOR_AVAILABLE:
            # Use external live monitor module
            try:
                from live_monitor import LiveMonitor
                live_monitor = LiveMonitor(self)
                live_monitor.open_live_monitor(self.selected_devices)
            except Exception as e:
                messagebox.showerror("Live Monitor Error", f"Failed to open live monitor: {e}")
                print(f"Live monitor error: {e}")  # Debug output
                # Fall back to built-in monitor
                self.show_builtin_live_monitor()
        else:
            # Use built-in live monitor
            self.show_builtin_live_monitor()
    
    def show_builtin_live_monitor(self):
        """Show built-in live monitoring window"""
        if self.current_monitor_window:
            self.current_monitor_window.lift()
            return
        
        # Create monitor window
        self.current_monitor_window = ctk.CTkToplevel(self.root)
        self.current_monitor_window.title("Live Device Monitor")
        self.current_monitor_window.geometry("1000x700")
        self.current_monitor_window.minsize(1280, 720)  # Set minimum size
        self.current_monitor_window.transient(self.root)
        
        # Handle window close
        self.current_monitor_window.protocol("WM_DELETE_WINDOW", self.close_monitor_window)
        
        # Main frame
        main_frame = ctk.CTkFrame(self.current_monitor_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Control frame
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Start/Stop monitoring button
        self.monitor_btn = ctk.CTkButton(
            control_frame,
            text="Start Monitoring",
            command=self.toggle_monitoring
        )
        self.monitor_btn.pack(side="left", padx=5)
        
        # Pause/Resume button
        self.pause_btn = ctk.CTkButton(
            control_frame,
            text="Pause",
            command=self.toggle_pause_monitoring,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=5)
        
        # Clear data button
        clear_btn = ctk.CTkButton(
            control_frame,
            text="Clear Data",
            command=self.clear_monitor_data
        )
        clear_btn.pack(side="left", padx=5)
        
        # Status label
        self.monitor_status_label = ctk.CTkLabel(
            control_frame,
            text=f"Monitoring {len(self.selected_devices)} devices"
        )
        self.monitor_status_label.pack(side="right", padx=10)
        
        # Create scrollable frame for device monitors
        self.monitor_scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            label_text="Device Status"
        )
        self.monitor_scroll_frame.pack(fill="both", expand=True)
        
        # Create individual device monitor widgets
        self.create_device_monitor_widgets()
    
    def create_device_monitor_widgets(self):
        """Create monitoring widgets for each selected device"""
        self.device_monitor_widgets = {}
        
        for i, device in enumerate(self.selected_devices):
            # Device frame
            device_frame = ctk.CTkFrame(self.monitor_scroll_frame)
            device_frame.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")
            
            # Configure grid
            self.monitor_scroll_frame.grid_columnconfigure(i%2, weight=1)
            
            # Device info
            info_label = ctk.CTkLabel(
                device_frame,
                text=f"{device['ip']} - {device.get('hostname', 'Unknown')}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            info_label.pack(pady=5)
            
            # Status label
            status_label = ctk.CTkLabel(device_frame, text="Status: Not monitoring")
            status_label.pack()
            
            # Latency label  
            latency_label = ctk.CTkLabel(device_frame, text="Latency: --")
            latency_label.pack()
            
            # Last update label
            update_label = ctk.CTkLabel(device_frame, text="Last update: Never")
            update_label.pack()
            
            # Simple graph placeholder (text-based)
            graph_label = ctk.CTkLabel(
                device_frame,
                text="Latency Graph: Start monitoring to see data",
                width=400,
                height=100
            )
            graph_label.pack(pady=5)
            
            # Store widgets
            self.device_monitor_widgets[device['ip']] = {
                'frame': device_frame,
                'status': status_label,
                'latency': latency_label,
                'update': update_label,
                'graph': graph_label
            }
    
    def toggle_monitoring(self):
        """Toggle device monitoring"""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start monitoring selected devices"""
        self.monitoring = True
        self.monitor_paused = False
        
        # Update UI
        self.monitor_btn.configure(text="Stop Monitoring", fg_color="#d32f2f")
        self.pause_btn.configure(state="normal")
        
        # Start monitors for each device
        for device in self.selected_devices:
            if device['ip'] not in self.device_monitors:
                monitor = DeviceMonitor(device['ip'], interval=2)
                monitor.start(
                    update_callback=self.update_device_monitor,
                    graph_callback=self.update_device_graph
                )
                self.device_monitors[device['ip']] = monitor
        
        self.update_status(f"Started monitoring {len(self.selected_devices)} devices")
    
    def stop_monitoring(self):
        """Stop monitoring all devices"""
        self.monitoring = False
        self.monitor_paused = False
        
        # Update UI
        self.monitor_btn.configure(text="Start Monitoring", fg_color="#1f538d")
        self.pause_btn.configure(state="disabled", text="Pause")
        
        # Stop all monitors
        for monitor in self.device_monitors.values():
            monitor.stop()
        self.device_monitors.clear()
        
        # Reset widget states
        for ip, widgets in self.device_monitor_widgets.items():
            widgets['status'].configure(text="Status: Not monitoring")
            widgets['latency'].configure(text="Latency: --")
            widgets['update'].configure(text="Last update: Never")
        
        self.update_status("Stopped monitoring all devices")
    
    def toggle_pause_monitoring(self):
        """Toggle pause/resume monitoring"""
        if not self.monitor_paused:
            self.monitor_paused = True
            self.pause_btn.configure(text="Resume")
            self.update_status("Monitoring paused")
        else:
            self.monitor_paused = False
            self.pause_btn.configure(text="Pause")
            self.update_status("Monitoring resumed")
    
    def clear_monitor_data(self):
        """Clear monitoring data"""
        for monitor in self.device_monitors.values():
            monitor.buffer.clear()
        
        # Reset graphs
        for widgets in self.device_monitor_widgets.values():
            widgets['graph'].configure(text="Latency Graph: Data cleared")
        
        self.update_status("Monitoring data cleared")
    
    def update_device_monitor(self, ip, latency, status, timestamp):
        """Update device monitor display"""
        if self.monitor_paused:
            return
        
        if ip in self.device_monitor_widgets:
            widgets = self.device_monitor_widgets[ip]
            
            # Update status
            status_text = "Online" if status == 'up' else "Offline"
            status_color = "#4CAF50" if status == 'up' else "#f44336"
            widgets['status'].configure(
                text=f"Status: {status_text}",
                text_color=status_color
            )
            
            # Update latency
            if status == 'up' and not math.isnan(latency):
                latency_color = "#4CAF50" if latency < 100 else "#FF9800" if latency < 500 else "#f44336"
                widgets['latency'].configure(
                    text=f"Latency: {latency:.1f}ms",
                    text_color=latency_color
                )
            else:
                widgets['latency'].configure(
                    text="Latency: Timeout",
                    text_color="#f44336"
                )
            
            # Update timestamp
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
            widgets['update'].configure(text=f"Last update: {time_str}")
    
    def update_device_graph(self, ip, data_buffer):
        """Update device graph (simplified text version)"""
        if self.monitor_paused or ip not in self.device_monitor_widgets:
            return
        
        widgets = self.device_monitor_widgets[ip]
        
        if len(data_buffer) < 2:
            widgets['graph'].configure(text="Latency Graph: Collecting data...")
            return
        
        # Simple text-based graph representation
        recent_data = data_buffer[-10:]  # Last 10 readings
        latencies = [d[1] for d in recent_data if not math.isnan(d[1])]
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            graph_text = f"Latency (last 10): Avg {avg_latency:.1f}ms | Min {min_latency:.1f}ms | Max {max_latency:.1f}ms"
        else:
            graph_text = "Latency Graph: No valid data"
        
        widgets['graph'].configure(text=graph_text)
    
    def close_monitor_window(self):
        """Close monitoring window"""
        if self.monitoring:
            self.stop_monitoring()
        
        if self.current_monitor_window:
            self.current_monitor_window.destroy()
            self.current_monitor_window = None
    
    def run_speed_test(self):
        """Run internet speed test"""
        if not SPEEDTEST_AVAILABLE:
            self.show_speedtest_installation_dialog()
            return
        
        # Create speed test window
        speedtest_window = ctk.CTkToplevel(self.root)
        speedtest_window.title("Internet Speed Test")
        speedtest_window.geometry("500x400")
        speedtest_window.transient(self.root)
        speedtest_window.grab_set()
        
        # Center the window
        speedtest_window.update_idletasks()
        x = (speedtest_window.winfo_screenwidth() // 2) - (speedtest_window.winfo_width() // 2)
        y = (speedtest_window.winfo_screenheight() // 2) - (speedtest_window.winfo_height() // 2)
        speedtest_window.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(speedtest_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Internet Speed Test",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Status label
        status_label = ctk.CTkLabel(main_frame, text="Ready to start speed test")
        status_label.pack(pady=5)
        
        # Progress bar
        progress_bar = ctk.CTkProgressBar(main_frame)
        progress_bar.pack(fill="x", pady=10)
        progress_bar.set(0)
        
        # Results frame
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, pady=10)
        
        # Results labels
        download_label = ctk.CTkLabel(results_frame, text="Download Speed: --", font=ctk.CTkFont(size=14))
        download_label.pack(pady=5)
        
        upload_label = ctk.CTkLabel(results_frame, text="Upload Speed: --", font=ctk.CTkFont(size=14))
        upload_label.pack(pady=5)
        
        ping_label = ctk.CTkLabel(results_frame, text="Ping: --", font=ctk.CTkFont(size=14))
        ping_label.pack(pady=5)
        
        server_label = ctk.CTkLabel(results_frame, text="Server: --", font=ctk.CTkFont(size=12))
        server_label.pack(pady=5)
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Speed test runner
        speed_runner = None
        
        def start_test():
            nonlocal speed_runner
            
            # Reset UI
            status_label.configure(text="Initializing...")
            progress_bar.set(0)
            download_label.configure(text="Download Speed: --")
            upload_label.configure(text="Upload Speed: --")
            ping_label.configure(text="Ping: --")
            server_label.configure(text="Server: --")
            
            start_btn.configure(state="disabled")
            cancel_btn.configure(state="normal")
            
            # Create and start speed test
            speed_runner = SpeedTestRunner(
                progress_callback=lambda p: progress_bar.set(p/100),
                status_callback=lambda s: status_label.configure(text=s),
                result_callback=show_results,
                error_callback=show_error
            )
            
            # Run in thread
            threading.Thread(target=speed_runner.run_test, daemon=True).start()
        
        def cancel_test():
            nonlocal speed_runner
            if speed_runner:
                speed_runner.cancel()
            status_label.configure(text="Test cancelled")
            start_btn.configure(state="normal")
            cancel_btn.configure(state="disabled")
        
        def show_results(results):
            status_label.configure(text="Test completed!")
            download_label.configure(text=f"Download Speed: {results['download']:.2f} Mbps")
            upload_label.configure(text=f"Upload Speed: {results['upload']:.2f} Mbps")
            ping_label.configure(text=f"Ping: {results['ping']:.1f} ms")
            server_label.configure(text=f"Server: {results['server']['name']} ({results['server']['country']})")
            start_btn.configure(state="normal")
            cancel_btn.configure(state="disabled")
        
        def show_error(error):
            status_label.configure(text=f"Error: {error}")
            start_btn.configure(state="normal")
            cancel_btn.configure(state="disabled")
        
        # Buttons
        start_btn = ctk.CTkButton(
            button_frame,
            text="Start Test",
            command=start_test
        )
        start_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=cancel_test,
            state="disabled"
        )
        cancel_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=speedtest_window.destroy
        )
        close_btn.pack(side="right", padx=5)
    
    def open_traceroute_choice_dialog(self):
        """Open choice dialog to select Traceroute or PathPing"""
        if not TRACEMAP_AVAILABLE:
            messagebox.showerror("Traceroute Not Available", "Traceroute module is not available.")
            return

        if not self.selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device.")
            return

        choice_window = ctk.CTkToplevel(self.root)
        choice_window.title("Select Traceroute or PathPing")
        choice_window.geometry("350x200")
        choice_window.transient(self.root)
        set_dialog_icon(choice_window)
        choice_window.grab_set()

        # Center the window
        choice_window.update_idletasks()
        x = (choice_window.winfo_screenwidth() // 2) - (choice_window.winfo_width() // 2)
        y = (choice_window.winfo_screenheight() // 2) - (choice_window.winfo_height() // 2)
        choice_window.geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(choice_window, text="Choose tracing method:", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(pady=(20, 10))

        def start_traceroute():
            choice_window.destroy()
            self.open_traceroute_dialog()

        def start_pathping():
            choice_window.destroy()
            self.open_pathping_dialog()

        btn_frame = ctk.CTkFrame(choice_window)
        btn_frame.pack(pady=10, padx=20, fill="x")

        traceroute_btn = ctk.CTkButton(btn_frame, text="Traceroute", command=start_traceroute)
        traceroute_btn.pack(side="left", expand=True, padx=5)

        pathping_btn = ctk.CTkButton(btn_frame, text="PathPing", command=start_pathping)
        pathping_btn.pack(side="left", expand=True, padx=5)

        # Options button
        options_button = ctk.CTkButton(btn_frame, text="Options", command=self.show_options_dialog)
        options_button.pack(side="left", expand=True, padx=5)

    def open_traceroute_dialog(self):
        if len(self.selected_devices) > 1:
            self._select_device_then_run(self.tracemap.show_tracemap_dialog, "Traceroute")
        else:
            self.tracemap.show_tracemap_dialog(self.selected_devices[0]['ip'])

    def open_pathping_dialog(self):
        if len(self.selected_devices) > 1:
            self._select_device_then_run(self.show_pathping_dialog, "PathPing")
        else:
            self.show_pathping_dialog(self.selected_devices[0]['ip'])

    def _select_device_then_run(self, func, title):
        selection_window = ctk.CTkToplevel(self.root)
        selection_window.title(f"Select Device for {title}")
        selection_window.geometry("400x300")
        selection_window.transient(self.root)
        set_dialog_icon(selection_window)
        selection_window.grab_set()

        # Center the window
        selection_window.update_idletasks()
        x = (selection_window.winfo_screenwidth() // 2) - (selection_window.winfo_width() // 2)
        y = (selection_window.winfo_screenheight() // 2) - (selection_window.winfo_height() // 2)
        selection_window.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            selection_window,
            text=f"Multiple devices selected. Choose one for {title}:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=20)

        list_frame = ctk.CTkScrollableFrame(selection_window)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        def select_device(device):
            selection_window.destroy()
            func(device['ip'])

        for device in self.selected_devices:
            device_info = f"{device['ip']} - {device.get('hostname', 'Unknown')}"
            btn = ctk.CTkButton(
                list_frame,
                text=device_info,
                command=lambda d=device: select_device(d)
            )
            btn.pack(fill="x", pady=5)

        cancel_btn = ctk.CTkButton(selection_window, text="Cancel", command=selection_window.destroy)
        cancel_btn.pack(pady=10)

    def show_options_dialog(self):
        """Show options for traceroute or pathping commands"""
        options_window = ctk.CTkToplevel(self.root)
        options_window.title("Command Options")
        options_window.geometry("400x300")
        options_window.transient(self.root)
        set_dialog_icon(options_window)
        options_window.grab_set()

        # Center the window
        options_window.update_idletasks()
        x = (options_window.winfo_screenwidth() // 2) - (options_window.winfo_width() // 2)
        y = (options_window.winfo_screenheight() // 2) - (options_window.winfo_height() // 2)
        options_window.geometry(f"+{x}+{y}")

        # Arguments
        options = {
            'max_hops': tk.StringVar(value='30'),
            'wait_time': tk.StringVar(value='3'),
            'queries_per_hop': tk.StringVar(value='3'),
            'ping_interval': tk.StringVar(value='250')
        }

        ctk.CTkLabel(options_window, text="Max Hops:").pack(anchor="w", padx=20)
        ctk.CTkEntry(options_window, textvariable=options['max_hops']).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(options_window, text="Wait Time (secs):").pack(anchor="w", padx=20)
        ctk.CTkEntry(options_window, textvariable=options['wait_time']).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(options_window, text="Queries per Hop:").pack(anchor="w", padx=20)
        ctk.CTkEntry(options_window, textvariable=options['queries_per_hop']).pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(options_window, text="Ping Interval (ms):").pack(anchor="w", padx=20)
        ctk.CTkEntry(options_window, textvariable=options['ping_interval']).pack(fill="x", padx=20, pady=(0, 10))

        def save_options():
            self.traceroute_options = options['max_hops'].get(), options['wait_time'].get()
            self.pathping_options = options['queries_per_hop'].get(), options['ping_interval'].get()
            options_window.destroy()

        ctk.CTkButton(options_window, text="Save", command=save_options).pack(pady=10)

    def show_pathping_dialog(self, ip):
        import subprocess
        import threading

        if hasattr(self, '_pathping_window') and self._pathping_window:
            try:
                self._pathping_window.destroy()
            except:
                pass
            self._pathping_window = None

        self._pathping_window = ctk.CTkToplevel(self.root)
        self._pathping_window.title(f"PathPing - {ip}")
        self._pathping_window.geometry("700x500")
        self._pathping_window.transient(self.root)
        self._pathping_window.grab_set()
        set_dialog_icon(self._pathping_window)

        # Center the window
        self._pathping_window.update_idletasks()
        x = (self._pathping_window.winfo_screenwidth() // 2) - (self._pathping_window.winfo_width() // 2)
        y = (self._pathping_window.winfo_screenheight() // 2) - (self._pathping_window.winfo_height() // 2)
        self._pathping_window.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(self._pathping_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        label = ctk.CTkLabel(frame, text=f"PathPing results for {ip}", font=ctk.CTkFont(size=16, weight="bold"))
        label.pack(pady=10)

        result_text = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=13))
        result_text.pack(fill="both", expand=True, pady=10)

        progress_bar = ctk.CTkProgressBar(frame)
        progress_bar.pack(fill="x", pady=(0, 10))
        progress_bar.set(0)

        stop_flag = {'running': True}

        def run_pathping():
            try:
                # Run pathping using TraceMap
                if hasattr(self, 'pathping_options'):
                    queries, interval = self.pathping_options
                else:
                    queries, interval = 3, 250
                
                proc = self.tracemap.run_pathping(ip, queries, interval)
                if proc is None:
                    self.safe_window_update(lambda: label.configure(text=f"Error: Failed to start PathPing"))
                    self.safe_window_update(lambda: result_text.insert("end", "Failed to start PathPing process\n"))
                    return

                def output_callback(line):
                    safe_window_update(lambda l=line: result_text.insert("end", l))
                    safe_window_update(lambda: result_text.see("end"))

                output_lines, return_code = self.tracemap.collect_pathping_output(proc, output_callback, stop_flag)
                if return_code == 0:
                    safe_window_update(lambda: label.configure(text=f"PathPing completed for {ip}"))
                else:
                    safe_window_update(lambda: label.configure(text=f"PathPing finished with errors"))
            except Exception as e:
                safe_window_update(lambda: label.configure(text=f"Error: {str(e)}"))
                safe_window_update(lambda: result_text.insert("end", f"\n\nError: {str(e)}\n"))
        
        def safe_window_update(callback):
            """Safely update window widgets, handling destroyed windows"""
            try:
                if hasattr(self, '_pathping_window') and self._pathping_window and self._pathping_window.winfo_exists():
                    self._pathping_window.after(0, callback)
            except (tk.TclError, AttributeError):
                # Window has been destroyed or is not accessible
                pass

        def start_pathping():
            stop_flag['running'] = True
            start_button.configure(state="disabled")
            stop_button.configure(state="normal")
            progress_bar.set(0)
            result_text.delete("1.0", "end")
            threading.Thread(target=run_pathping, daemon=True).start()

        def stop_pathping():
            stop_flag['running'] = False
            stop_button.configure(state="disabled")
            start_button.configure(state="normal")

        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(fill="x", pady=10)

        start_button = ctk.CTkButton(button_frame, text="Start PathPing", command=start_pathping)
        start_button.pack(side="left", padx=10)

        stop_button = ctk.CTkButton(button_frame, text="Stop PathPing", command=stop_pathping, state="disabled")
        stop_button.pack(side="left", padx=10)

        close_button = ctk.CTkButton(button_frame, text="Close", command=self._pathping_window.destroy)
        close_button.pack(side="right", padx=10)

    def open_tracemap_dialog(self):
        """Open TraceMap dialog for selected devices"""
        if not TRACEMAP_AVAILABLE:
            messagebox.showerror("Trace Route Not Available", "Trace Route module is not available.")
            return

        if not self.selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device to trace route.")
            return

        # If multiple devices selected, let user choose one
        if len(self.selected_devices) > 1:
            # Create device selection dialog
            selection_window = ctk.CTkToplevel(self.root)
            selection_window.title("Select Device for TraceMap")
            selection_window.geometry("400x300")
            selection_window.transient(self.root)
            set_dialog_icon(selection_window)
            selection_window.grab_set()

            # Center the window
            selection_window.update_idletasks()
            x = (selection_window.winfo_screenwidth() // 2) - (selection_window.winfo_width() // 2)
            y = (selection_window.winfo_screenheight() // 2) - (selection_window.winfo_height() // 2)
            selection_window.geometry(f"+{x}+{y}")

            ctk.CTkLabel(
                selection_window,
                text="Multiple devices selected. Choose one for TraceMap:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=20)

            # Device list frame
            list_frame = ctk.CTkScrollableFrame(selection_window)
            list_frame.pack(fill="both", expand=True, padx=20, pady=10)

            def select_device(device):
                selection_window.destroy()
                self.tracemap.show_tracemap_dialog(device['ip'])

            # Add device buttons
            for device in self.selected_devices:
                device_info = f"{device['ip']} - {device.get('hostname', 'Unknown')}"
                btn = ctk.CTkButton(
                    list_frame,
                    text=device_info,
                    command=lambda d=device: select_device(d)
                )
                btn.pack(fill="x", pady=5)

            # Cancel button
            cancel_btn = ctk.CTkButton(
                selection_window,
                text="Cancel",
                command=selection_window.destroy
            )
            cancel_btn.pack(pady=10)

        else:
            # Single device selected
            self.tracemap.show_tracemap_dialog(self.selected_devices[0]['ip'])

    def show_speedtest_installation_dialog(self):
        """Show speedtest installation instructions"""
        install_window = ctk.CTkToplevel(self.root)
        install_window.title("Speed Test Not Available")
        install_window.geometry("600x400")
        install_window.transient(self.root)
        install_window.grab_set()
        
        # Center the window
        install_window.update_idletasks()
        x = (install_window.winfo_screenwidth() // 2) - (install_window.winfo_width() // 2)
        y = (install_window.winfo_screenheight() // 2) - (install_window.winfo_height() // 2)
        install_window.geometry(f"+{x}+{y}")
        
        instructions = """SPEED TEST NOT AVAILABLE

To use the internet speed test feature, you need to install the 'speedtest-cli' library.

INSTALLATION INSTRUCTIONS:

1. Open Command Prompt (Windows) or Terminal (Mac/Linux)

2. Install speedtest-cli using pip:
   pip install speedtest-cli

3. Alternative installation methods:
   • Using conda: conda install speedtest-cli
   • Using pip3: pip3 install speedtest-cli

4. Restart the application after installation

ALTERNATIVE SPEED TEST OPTIONS:

• Visit speedtest.net in your web browser
• Use fast.com by Netflix
• Run 'speedtest-cli' directly from command line after installation

After installing speedtest-cli, you'll be able to run speed tests directly from this application."""
        
        text_widget = ctk.CTkTextbox(
            install_window,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        text_widget.pack(fill="both", expand=True, padx=20, pady=20)
        text_widget.insert("1.0", instructions)
        text_widget.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(
            install_window,
            text="Close",
            command=install_window.destroy
        )
        close_btn.pack(pady=(0, 20))
    
    # Database methods for notes persistence
    def init_device_notes_table(self):
        """Initialize the device notes database table"""
        try:
            import sqlite3
            
            # Create data directory if it doesn't exist
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # Database path
            db_path = os.path.join(data_dir, 'device_notes.db')
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_notes (
                        mac_address TEXT PRIMARY KEY,
                        notes TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                
        except Exception as e:
            print(f"Error initializing device notes database: {e}")
    
    def save_device_notes(self, mac_address, notes):
        """Save device notes to database"""
        try:
            import sqlite3
            
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            db_path = os.path.join(data_dir, 'device_notes.db')
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO device_notes (mac_address, notes, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (mac_address.upper(), notes))
                conn.commit()
                
            return True
            
        except Exception as e:
            print(f"Error saving device notes: {e}")
            return False
    
    def load_device_notes(self, mac_address):
        """Load device notes from database"""
        try:
            import sqlite3
            
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            db_path = os.path.join(data_dir, 'device_notes.db')
            
            if not os.path.exists(db_path):
                return ""
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT notes FROM device_notes WHERE mac_address = ?', (mac_address.upper(),))
                result = cursor.fetchone()
                
                return result[0] if result else ""
                
        except Exception as e:
            print(f"Error loading device notes: {e}")
            return ""
    
    def update_all_device_notes(self, mac_address, notes):
        """Update notes for all devices with the same MAC address"""
        if not mac_address or mac_address.upper() == 'UNKNOWN':
            return
        
        # Update all devices in memory with the same MAC address
        for device in self.all_devices:
            if device.get('mac', '').upper() == mac_address.upper():
                device['notes'] = notes
    
    def load_notes_for_devices_background(self, devices):
        """Load notes for devices in background thread"""
        def load_notes():
            for device in devices:
                mac = device.get('mac', '')
                if mac and mac.upper() != 'UNKNOWN':
                    notes = self.load_device_notes(mac)
                    device['notes'] = notes
        
        threading.Thread(target=load_notes, daemon=True).start()
    
    def update_profile_notes(self, profile_name, mac_address, notes):
        """Update notes in profile if device belongs to a profile"""
        # This would integrate with the profile manager if available
        try:
            if hasattr(self, 'profile_manager'):
                # The profile manager would handle this
                pass
        except Exception:
            pass

    def run(self):
        """Start application"""
        # Initialize database schema if it doesn't exist
        setup_database()
        
        # Initialize the device notes table on startup
        self.init_device_notes_table()
        
        self.update_status("Ready to scan network")
        self.root.mainloop()

        # Clean up system tray on exit
        if self.tray_manager:
            self.tray_manager.stop()

def main():
    """Main entry point for the NetworkMonitor application"""
    try:
        # Set the appearance mode and theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create and run the application
        app = NetworkMonitorApp()
        app.run()

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting NetworkMonitor: {e}")
        messagebox.showerror("Error", f"Failed to start NetworkMonitor:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

