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
import subprocess
import socket
import psutil
from datetime import datetime, timedelta
import json
import os
import sys
import csv
import webbrowser
import platform
import re
import ipaddress
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from PIL import Image

# Import settings system
try:
    from settings import settings_manager, get_theme, set_theme, get_window_size, set_window_size
    from settings_manager import show_settings_dialog
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False

# Import nmap monitor module
try:
    from nmap_monitor import NmapMonitor
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False

# Import system tray module
try:
    from system_tray import SystemTrayManager
    SYSTRAY_AVAILABLE = True
except ImportError:
    SYSTRAY_AVAILABLE = False

# Import live monitor module
try:
    from live_monitor import LiveMonitor
    LIVE_MONITOR_AVAILABLE = True
except ImportError:
    LIVE_MONITOR_AVAILABLE = False

# Try to import advanced modules with fallbacks
try:
    from scapy.layers.l2 import ARP, Ether, srp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

try:
    from manuf import manuf
    MANUF_AVAILABLE = True
except ImportError:
    MANUF_AVAILABLE = False

try:
    import speedtest as speedtest_module
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False

# ==================== Utility Classes ====================

class NetworkScanner:
    """Network scanning functionality"""
    
    def __init__(self, ip_range, progress_callback=None, device_callback=None):
        self.ip_range = ip_range
        self.progress_callback = progress_callback
        self.device_callback = device_callback
        self.scanning = True
        
        # Initialize MAC parser if available
        if MANUF_AVAILABLE:
            try:
                self.mac_parser = manuf.MacParser()
            except:
                self.mac_parser = None
        else:
            self.mac_parser = None
    
    def check_web_port(self, ip):
        """Check if device has web services"""
        ports = [(80, 'http'), (443, 'https')]
        for port, scheme in ports:
            try:
                with socket.create_connection((str(ip), port), timeout=0.5):
                    return f"{scheme}://{ip}:{port if port != 80 and port != 443 else ''}"
            except:
                continue
        return None
    
    def get_hostname(self, ip):
        """Get hostname for IP with timeout"""
        try:
            # Set a shorter timeout for hostname resolution
            socket.setdefaulttimeout(2.0)  # 2 second timeout
            hostname = socket.gethostbyaddr(str(ip))[0]
            # Reset timeout
            socket.setdefaulttimeout(None)
            return hostname if hostname else "Unknown"
        except (socket.herror, socket.gaierror, socket.timeout):
            # Reset timeout on error
            socket.setdefaulttimeout(None)
            return "Unknown"
        except Exception:
            # Reset timeout on any other error
            socket.setdefaulttimeout(None)
            return "Unknown"

    def get_manufacturer(self, mac):
        """Get manufacturer from MAC with improved error handling"""
        if not mac or mac == 'Unknown':
            return "Unknown"

        if self.mac_parser:
            try:
                # Clean the MAC address format
                clean_mac = mac.replace('-', ':').replace('.', ':').upper()
                manufacturer = self.mac_parser.get_manuf(clean_mac)
                return manufacturer if manufacturer else "Unknown"
            except Exception:
                return "Unknown"
        return "Unknown"

    def get_mac_address(self, ip):
        """Get MAC address using ARP table lookup as fallback"""
        try:
            # First try to get MAC from system ARP table
            if platform.system().lower() == 'windows':
                result = subprocess.run(['arp', '-a', str(ip)],
                                      capture_output=True, text=True, timeout=5,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    # Parse ARP output to extract MAC
                    for line in result.stdout.split('\n'):
                        if str(ip) in line:
                            # Look for MAC address pattern
                            import re
                            mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
                            if mac_match:
                                return mac_match.group(0).upper()
            else:
                # Linux/Unix systems
                result = subprocess.run(['arp', '-n', str(ip)],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if str(ip) in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                mac = parts[2]
                                if ':' in mac and len(mac) == 17:
                                    return mac.upper()
        except Exception as e:
            pass

        return "Unknown"

    def arp_scan_ip(self, ip):
        """ARP scan single IP"""
        if not self.scanning:
            return []
            
        devices = []
        
        if SCAPY_AVAILABLE:
            try:
                # Use Scapy for ARP scanning
                arp = ARP(pdst=str(ip))
                ether = Ether(dst="ff:ff:ff:ff:ff:ff")
                packet = ether / arp
                
                start_time = time.time()
                result = srp(packet, timeout=0.5, verbose=0)[0]
                end_time = time.time()
                
                for _, received in result:
                    ip_addr = received.psrc
                    mac = received.hwsrc
                    response_time = end_time - start_time
                    
                    web_service = self.check_web_port(ip_addr)
                    hostname = self.get_hostname(ip_addr)
                    manufacturer = self.get_manufacturer(mac)
                    
                    devices.append({
                        'ip': ip_addr,
                        'mac': mac,
                        'response_time': response_time,
                        'web_service': web_service,
                        'hostname': hostname,
                        'manufacturer': manufacturer,
                        'status': 'Online',
                        'profile': '',  # New field for profile
                        'friendly_name': '',  # New field for friendly name
                        'notes': ''  # New field for notes
                    })

                # If ARP scan found no devices, fall back to ping scanning
                if not devices:
                    ping_result = self.ping_host_simple(ip)
                    if ping_result[0]:  # If ping succeeded
                        hostname = self.get_hostname(ip)
                        web_service = self.check_web_port(ip)
                        # Try to get MAC from ARP table
                        mac = self.get_mac_address(ip)
                        manufacturer = self.get_manufacturer(mac)

                        devices.append({
                            'ip': str(ip),
                            'mac': mac,
                            'response_time': ping_result[1],  # Use actual ping time
                            'web_service': web_service,
                            'hostname': hostname,
                            'manufacturer': manufacturer,
                            'status': 'Online',
                            'profile': '',  # New field for profile
                            'friendly_name': '',  # New field for friendly name
                            'notes': ''  # New field for notes
                        })

            except Exception as e:
                print(f"ARP scan error for {ip}: {e}")
                # Fallback to ping scanning if ARP fails
                ping_result = self.ping_host_simple(ip)
                if ping_result[0]:  # If ping succeeded
                    hostname = self.get_hostname(ip)
                    web_service = self.check_web_port(ip)
                    # Try to get MAC from ARP table
                    mac = self.get_mac_address(ip)
                    manufacturer = self.get_manufacturer(mac)

                    devices.append({
                        'ip': str(ip),
                        'mac': mac,
                        'response_time': ping_result[1],  # Use actual ping time
                        'web_service': web_service,
                        'hostname': hostname,
                        'manufacturer': manufacturer,
                        'status': 'Online',
                        'profile': '',  # New field for profile
                        'friendly_name': '',  # New field for friendly name
                        'notes': ''  # New field for notes
                    })
        else:
            # Fallback to ping scanning
            ping_result = self.ping_host_simple(ip)
            if ping_result[0]:  # If ping succeeded
                hostname = self.get_hostname(ip)
                web_service = self.check_web_port(ip)
                # Try to get MAC from ARP table
                mac = self.get_mac_address(ip)
                manufacturer = self.get_manufacturer(mac)

                devices.append({
                    'ip': str(ip),
                    'mac': mac,
                    'response_time': ping_result[1],  # Use actual ping time
                    'web_service': web_service,
                    'hostname': hostname,
                    'manufacturer': manufacturer,
                    'status': 'Online',
                    'profile': '',  # New field for profile
                    'friendly_name': '',  # New field for friendly name
                    'notes': ''  # New field for notes
                })
                
        return devices
    
    def ping_host_simple(self, ip):
        """Simple ping implementation with response time measurement"""
        try:
            if platform.system().lower() == 'windows':
                start_time = time.time()
                result = subprocess.run(['ping', '-n', '1', '-w', '1000', str(ip)],
                                      capture_output=True, text=True, timeout=2, creationflags=subprocess.CREATE_NO_WINDOW)
                end_time = time.time()

                if result.returncode == 0:
                    # Try to extract actual ping time from output
                    output = result.stdout
                    import re
                    time_match = re.search(r'time[<=](\d+(?:\.\d+)?)ms', output)
                    if time_match:
                        actual_time = float(time_match.group(1)) / 1000  # Convert to seconds
                        return True, actual_time
                    elif 'time<1ms' in output.lower():
                        return True, 0.0005  # 0.5ms
                    else:
                        # Fallback to measured time
                        return True, end_time - start_time
                else:
                    return False, None
            else:
                start_time = time.time()
                result = subprocess.run(['ping', '-c', '1', '-W', '1', str(ip)],
                                      capture_output=True, text=True, timeout=2)
                end_time = time.time()

                if result.returncode == 0:
                    # Try to extract actual ping time from output
                    output = result.stdout
                    import re
                    time_match = re.search(r'time=(\d+\.?\d*) ms', output)
                    if time_match:
                        actual_time = float(time_match.group(1)) / 1000  # Convert to seconds
                        return True, actual_time
                    else:
                        # Fallback to measured time
                        return True, end_time - start_time
                else:
                    return False, None
        except:
            return False, None

    def scan(self):
        """Main scanning method"""
        devices = []
        
        try:
            network = ipaddress.ip_network(self.ip_range, strict=False)
        except ValueError:
            return devices
        
        hosts = list(network.hosts())
        total = len(hosts)
        completed = 0
        
        try:
            with ThreadPoolExecutor(max_workers=32) as executor:
                future_to_ip = {executor.submit(self.arp_scan_ip, ip): ip for ip in hosts}
                
                for future in as_completed(future_to_ip):
                    if not self.scanning:
                        break
                        
                    try:
                        result_devices = future.result()
                        for device in result_devices:
                            devices.append(device)
                            if self.device_callback:
                                self.device_callback(device)
                    except Exception as e:
                        print(f"Error in scan thread: {e}")
                    
                    completed += 1
                    if self.progress_callback:
                        percent = int((completed / total) * 100)
                        self.progress_callback(percent)
                        
        except Exception as e:
            print(f"ThreadPoolExecutor error: {e}")
        
        return devices
    
    def stop(self):
        """Stop scanning"""
        self.scanning = False

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

class SpeedTestRunner:
    """Speed test functionality"""
    
    def __init__(self, progress_callback=None, status_callback=None, result_callback=None, error_callback=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.result_callback = result_callback
        self.error_callback = error_callback
        self.cancelled = False
    
    def cancel(self):
        self.cancelled = True
    
    def run_test(self):
        """Run speed test in thread"""
        if not SPEEDTEST_AVAILABLE:
            if self.error_callback:
                self.error_callback("speedtest-cli not available")
            return
        
        try:
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Initializing speed test...")
            if self.progress_callback:
                self.progress_callback(10)
            
            st = speedtest_module.Speedtest()
            
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Finding best server...")
            if self.progress_callback:
                self.progress_callback(20)
            
            st.get_best_server()
            
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Testing download speed...")
            if self.progress_callback:
                self.progress_callback(40)
            
            download_speed = st.download() / 1_000_000
            
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Testing upload speed...")
            if self.progress_callback:
                self.progress_callback(70)
            
            upload_speed = st.upload() / 1_000_000
            
            if self.cancelled:
                return
            
            if self.status_callback:
                self.status_callback("Finalizing results...")
            if self.progress_callback:
                self.progress_callback(90)
            
            ping = st.results.ping
            
            if not self.cancelled:
                if self.progress_callback:
                    self.progress_callback(100)
                if self.result_callback:
                    self.result_callback({
                        'download': download_speed,
                        'upload': upload_speed,
                        'ping': ping,
                        'server': st.results.server
                    })
                    
        except Exception as e:
            if not self.cancelled and self.error_callback:
                self.error_callback(str(e))

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
        if NMAP_AVAILABLE:
            self.nmap_monitor = NmapMonitor(self)
        else:
            self.nmap_monitor = None
        
        # Initialize system tray
        if SYSTRAY_AVAILABLE:
            self.tray_manager = SystemTrayManager(self)
            self.tray_manager.start()
        else:
            self.tray_manager = None

        # Setup UI
        self.setup_ui()
        self.setup_menu()
        
        # Auto-detect network
        self.auto_detect_network()
        
        # Start a thread to get external IP
        threading.Thread(target=self.get_external_ip, daemon=True).start()
    
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
            text="I.T Assistant",
            font=ctk.CTkFont(size=18, weight="bold")  # Reduced font size
        )
        title_label.grid(row=1, column=0, padx=10, pady=(4, 2), sticky="ew")  # Reduced padding

        subtitle_label = ctk.CTkLabel(
            self.sidebar, 
            text="Network Monitor",
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
        tools_frame.grid_rowconfigure(2, weight=1)  # Nmap button
        tools_frame.grid_rowconfigure(3, weight=1)  # Speed test button
        
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
        self.speedtest_btn.grid(row=3, column=0, padx=8, pady=(4, 12), sticky="ew")
        
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
        self.main_frame.grid_rowconfigure(2, weight=1)
        
        # Info label
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text="Enter IP range or leave blank for auto-detect",
            font=ctk.CTkFont(size=14)
        )
        self.info_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Search and progress frame
        search_progress_frame = ctk.CTkFrame(self.main_frame)
        search_progress_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        search_progress_frame.grid_columnconfigure(0, weight=3)  # Search entry weight
        search_progress_frame.grid_columnconfigure(1, weight=1)  # Search button weight
        search_progress_frame.grid_columnconfigure(2, weight=1)  # Progress bar weight

        # Search entry
        self.search_input = ctk.CTkEntry(search_progress_frame, placeholder_text="IP, MAC, or hostname...")
        self.search_input.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="ew")
        # Remove the automatic search on typing and add Enter key binding
        self.search_input.bind("<Return>", lambda event: self.perform_search())

        # Search button
        search_button = ctk.CTkButton(search_progress_frame, text="Search", width=70, height=28, command=self.perform_search)
        search_button.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(search_progress_frame)
        self.progress_bar.grid(row=0, column=2, padx=(0, 10), pady=5, sticky="ew")
        self.progress_bar.set(0)

        self.summary_label = ctk.CTkLabel(
            search_progress_frame,
            text="Devices found: 0 | Problematic (>500ms): 0"
        )
        self.summary_label.grid(row=0, column=3, padx=(0, 10), pady=5, sticky="ew")
        
        
        # Device table frame
        self.table_frame = ctk.CTkScrollableFrame(
            self.main_frame, 
            label_text="Discovered Devices"
        )
        self.table_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        # Configure column weights for equal spacing
        for i in range(11):  # Updated from 8 to 11 for new columns
            self.table_frame.grid_columnconfigure(i, weight=1, minsize=100)
        
        # Table headers - Updated to include new columns
        headers = ["Select", "Profile", "IP Address", "MAC Address", "Hostname", "Friendly Name", "Manufacturer", "Response Time", "Web Service", "Actions", "Notes"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.table_frame, 
                text=header,
                font=ctk.CTkFont(weight="bold")
            )
            if i == 0:  # Left-justify the "Select" header to match checkbox alignment
                label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            else:
                label.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
        
        self.device_rows = []
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        self.status_frame.grid(row=2, column=1, sticky="ew", padx=20, pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
    
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
                
                # Also update the info label to show current status
                self.info_label.configure(text=f"Ready to scan network: {network}")
                
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
        self.info_label.configure(text=f"Scanning {ip_range}...")
        
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
        self.info_label.configure(text="Scan stopped")
        self.update_status("Scan stopped by user")
    
    def scan_network(self, ip_range):
        """Network scanning thread"""
        try:
            self.scanner = NetworkScanner(
                ip_range, 
                progress_callback=self.update_progress,
                device_callback=self.add_device_found
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
        self.info_label.configure(text="Scan complete")
        
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
    
    def add_device_to_table(self, device):
        """Add device to table"""
        if not device:
            return
            
        row_num = len(self.device_rows) + 1
        row_widgets = []
        
        # Select checkbox - left-aligned
        var = tk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            self.table_frame, 
            text="",
            variable=var,
            command=lambda: self.toggle_device_selection(device, var.get())
        )
        checkbox.grid(row=row_num, column=0, padx=5, pady=2, sticky="w")
        row_widgets.append(checkbox)
        
        # Profile (new column)
        profile_label = ctk.CTkLabel(self.table_frame, text=device.get('profile', ''))
        profile_label.grid(row=row_num, column=1, padx=5, pady=2)
        row_widgets.append(profile_label)

        # IP Address
        ip_label = ctk.CTkLabel(self.table_frame, text=device['ip'])
        ip_label.grid(row=row_num, column=2, padx=5, pady=2)
        row_widgets.append(ip_label)

        # MAC Address
        mac_label = ctk.CTkLabel(self.table_frame, text=device.get('mac', 'Unknown'))
        mac_label.grid(row=row_num, column=3, padx=5, pady=2)
        row_widgets.append(mac_label)
        
        # Hostname
        hostname_label = ctk.CTkLabel(self.table_frame, text=device.get('hostname', 'Unknown'))
        hostname_label.grid(row=row_num, column=4, padx=5, pady=2)
        row_widgets.append(hostname_label)
        
        # Friendly Name (new column)
        friendly_name_label = ctk.CTkLabel(self.table_frame, text=device.get('friendly_name', ''))
        friendly_name_label.grid(row=row_num, column=5, padx=5, pady=2)
        row_widgets.append(friendly_name_label)

        # Manufacturer
        manufacturer_label = ctk.CTkLabel(self.table_frame, text=device.get('manufacturer', 'Unknown'))
        manufacturer_label.grid(row=row_num, column=6, padx=5, pady=2)
        row_widgets.append(manufacturer_label)
        
        # Response Time
        response_ms = device.get('response_time', 0) * 1000
        response_color = "#f44336" if response_ms > 500 else None
        response_label = ctk.CTkLabel(
            self.table_frame, 
            text=f"{response_ms:.0f}ms",
            text_color=response_color
        )
        response_label.grid(row=row_num, column=7, padx=5, pady=2)
        row_widgets.append(response_label)
        
        # Web Service (clickable)
        web_service = device.get('web_service')
        if web_service:
            web_btn = ctk.CTkButton(
                self.table_frame,
                text="Open",
                width=60,
                height=24,
                command=lambda: webbrowser.open(web_service)
            )
            web_btn.grid(row=row_num, column=8, padx=5, pady=2)
            row_widgets.append(web_btn)
        else:
            web_label = ctk.CTkLabel(self.table_frame, text="None")
            web_label.grid(row=row_num, column=8, padx=5, pady=2)
            row_widgets.append(web_label)
        
        # Actions buttons (replacing dropdown)
        actions_frame = ctk.CTkFrame(self.table_frame)
        actions_frame.grid(row=row_num, column=9, padx=5, pady=2)

        # Details button
        details_btn = ctk.CTkButton(
            actions_frame,
            text="Details",
            width=60,
            height=20,
            command=lambda dev=device: self.show_device_details(dev)
        )
        details_btn.grid(row=0, column=0, padx=2, pady=1)

        # Nmap Scan button
        nmap_btn = ctk.CTkButton(
            actions_frame,
            text="Nmap",
            width=50,
            height=20,
            command=lambda dev=device: self.show_nmap_dialog(dev.get('ip'))
        )
        nmap_btn.grid(row=0, column=1, padx=2, pady=1)

        row_widgets.append(actions_frame)

        # Notes (new column)
        notes_label = ctk.CTkLabel(self.table_frame, text=device.get('notes', ''))
        notes_label.grid(row=row_num, column=10, padx=5, pady=2)
        row_widgets.append(notes_label)

        self.device_rows.append(row_widgets)

    def toggle_device_selection(self, device, selected):
        """Toggle device selection for monitoring"""
        if selected:
            if device not in self.selected_devices:
                self.selected_devices.append(device)
        else:
            if device in self.selected_devices:
                self.selected_devices.remove(device)
    
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

        # Re-add filtered devices with exact match
        for device in self.all_devices:
            if (query == device['ip'].lower() or
                query == device.get('mac', '').lower() or
                query == device.get('hostname', '').lower()):
                self.add_device_to_table(device)

        self.update_status(f"Search completed. Found {len(self.device_rows)} devices matching '{query}' (exact match)")

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
        result_text = ctk.CTkTextbox(nmap_window, font=ctk.CTkFont(family="Consolas"))
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
    
    def open_live_monitor(self):
        """Open live monitoring dialog using the refactored LiveMonitor class"""
        if not LIVE_MONITOR_AVAILABLE:
            messagebox.showerror("Live Monitor", "Live monitor module is not available.")
            return

        if not self.selected_devices:
            messagebox.showwarning("No Devices", "Please select at least one device to monitor.")
            return
        
        # Initialize live monitor if not already done
        if not hasattr(self, 'live_monitor'):
            self.live_monitor = LiveMonitor(self)

        # Open the live monitor with selected devices
        self.live_monitor.open_live_monitor(self.selected_devices)

    def show_file_menu(self):
        """Show file menu dropdown"""
        # Create dropdown menu
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Open", command=self.open_file)
        menu.add_command(label="Save Report", command=self.save_report)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.root.quit)

        # Position menu below button
        x = self.file_menu_btn.winfo_rootx()
        y = self.file_menu_btn.winfo_rooty() + self.file_menu_btn.winfo_height()
        menu.post(x, y)

    def show_options_menu(self):
        """Show options menu dropdown"""
        # Create dropdown menu
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Toggle Theme", command=self.toggle_theme_via_switch)

        # Add settings option if available
        if SETTINGS_AVAILABLE:
            menu.add_separator()
            menu.add_command(label="Settings...", command=lambda: show_settings_dialog(self.root))

        # Position menu below button
        x = self.options_menu_btn.winfo_rootx()
        y = self.options_menu_btn.winfo_rooty() + self.options_menu_btn.winfo_height()
        menu.post(x, y)

    def show_about_menu(self):
        """Show about menu dropdown"""
        # Create dropdown menu
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="About Network Monitor", command=self.show_about)

        # Position menu below button
        x = self.about_menu_btn.winfo_rootx()
        y = self.about_menu_btn.winfo_rooty() + self.about_menu_btn.winfo_height()
        menu.post(x, y)

    def show_about(self):
        """Show about dialog"""
        about_window = ctk.CTkToplevel(self.root)
        about_window.title("About I.T Assistant")
        about_window.geometry("420x320")
        about_window.transient(self.root)

        about_text = """
I.T Assistant v1.0

A modern network scanner and live device monitor.
Features: device discovery, latency/uptime monitoring, 
speed test, and more.

Author: Jason Burnham
Email: jason.o.burnham@gmail.com
License: MIT
© 2025 Jason Burnham

Built with CustomTkinter, psutil, scapy, speedtest-cli
        """

        about_label = ctk.CTkLabel(
            about_window,
            text=about_text,
            justify="center",
            font=ctk.CTkFont(size=12)
        )
        about_label.pack(padx=20, pady=20, expand=True, fill="both")

        ok_btn = ctk.CTkButton(about_window, text="OK", command=about_window.destroy)
        ok_btn.pack(pady=10)

    def toggle_theme_via_switch(self):
        # Get current theme and toggle it
        current_mode = ctk.get_appearance_mode()
        if current_mode.lower() == "dark":
            new_theme = "light"
        else:
            new_theme = "dark"

        # Apply the new theme
        ctk.set_appearance_mode(new_theme)

        # Save the theme preference to settings
        if SETTINGS_AVAILABLE:
            set_theme(new_theme)

        # Update menubar button colors after theme change
        self.root.after(50, self.update_menubar_colors)

    def update_menubar_colors(self):
        """Update menubar button text colors to match current theme"""
        current_mode = ctk.get_appearance_mode()

        # Set text colors based on theme
        if current_mode.lower() == "dark":
            text_color = "#FFFFFF"  # Explicit white hex
            hover_color = ("gray80", "gray20")
        else:
            text_color = "#000000"  # Explicit black hex
            hover_color = ("gray80", "gray20")

        # Update all menubar button colors
        try:
            self.file_menu_btn.configure(fg_color="transparent", text_color=text_color, hover_color=hover_color)
            self.options_menu_btn.configure(fg_color="transparent", text_color=text_color, hover_color=hover_color)
            self.about_menu_btn.configure(fg_color="transparent", text_color=text_color, hover_color=hover_color)
            print(f"Menubar text colors updated to {text_color} for {current_mode} theme")
        except Exception as e:
            print(f"Error updating menubar button colors: {e}")

    def get_network_interfaces(self):
        """Get available network interfaces with their details"""
        interfaces = []
        active_interface = None

        try:
            import psutil
            net_interfaces = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()

            # Get the current active interface (the one we're using for internet)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    active_ip = s.getsockname()[0]
            except:
                active_ip = None

            for interface_name, addresses in net_interfaces.items():
                # Skip loopback interfaces
                if 'loopback' in interface_name.lower() or interface_name.lower() == 'lo':
                    continue

                # Get interface statistics
                stats = net_stats.get(interface_name)
                if not stats or not stats.isup:
                    continue

                # Find IPv4 address
                ipv4_addr = None
                for addr in addresses:
                    if addr.family == socket.AF_INET:  # IPv4
                        ipv4_addr = addr.address
                        break

                if ipv4_addr and not ipv4_addr.startswith('127.') and not ipv4_addr.startswith('169.254.'):
                    # Create network range for this interface
                    ip_parts = ipv4_addr.split('.')
                    network_range = f"{'.'.join(ip_parts[:3])}.0/24"

                    interface_info = {
                        'name': interface_name,
                        'ip': ipv4_addr,
                        'network': network_range,
                        'display': f"{interface_name} ({ipv4_addr} - {network_range})"
                    }

                    interfaces.append(interface_info)

                    # Check if this is the active interface
                    if active_ip and ipv4_addr == active_ip:
                        active_interface = interface_info

            # If no active interface found, use the first one
            if not active_interface and interfaces:
                active_interface = interfaces[0]

        except Exception as e:
            print(f"Error detecting network interfaces: {e}")
            # Fallback to basic detection
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    ip_parts = local_ip.split('.')
                    network_range = f"{'.'.join(ip_parts[:3])}.0/24"

                    fallback_interface = {
                        'name': 'Auto-detected',
                        'ip': local_ip,
                        'network': network_range,
                        'display': f"Auto-detected ({local_ip} - {network_range})"
                    }
                    interfaces = [fallback_interface]
                    active_interface = fallback_interface
            except:
                pass

        return interfaces, active_interface

    def on_interface_selected(self, selection):
        """Handle interface selection from dropdown"""
        if selection == "Auto-Detect":
            self.auto_detect_network()
            return

        # Find the selected interface
        for interface in self.available_interfaces:
            if interface['display'] == selection:
                # Update the IP input with the network range
                self.ip_input.delete(0, tk.END)
                self.ip_input.insert(0, interface['network'])
                self.update_status(f"Selected interface: {interface['name']} - {interface['network']}")
                self.info_label.configure(text=f"Ready to scan network: {interface['network']}")
                break

    def update_network_information(self):
        """Update the network information display in the sidebar"""
        try:
            # Get active network interface info
            local_ip = None
            subnet_mask = None
            gateway = None
            mac_address = None
            internet_connected = False

            # Try to get local IP and check internet connection
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    internet_connected = True
            except:
                internet_connected = False

            # Get network interface details using psutil
            if local_ip:
                import psutil

                # Get subnet mask and MAC for the interface with our IP
                for interface_name, addresses in psutil.net_if_addrs().items():
                    for addr in addresses:
                        if addr.family == socket.AF_INET and addr.address == local_ip:
                            subnet_mask = addr.netmask
                        elif addr.family == psutil.AF_LINK and hasattr(addr, 'address'):
                            # Store MAC address for this interface
                            if 'loopback' not in interface_name.lower():
                                mac_address = addr.address

                # Get default gateway
                try:
                    gateways = psutil.net_if_stats()
                    # On Windows, use route command to get gateway
                    if platform.system().lower() == 'windows':
                        result = subprocess.run(['route', 'print', '0.0.0.0'],
                                              capture_output=True, text=True,
                                              creationflags=subprocess.CREATE_NO_WINDOW)
                        if result.returncode == 0:
                            lines = result.stdout.split('\n')
                            for line in lines:
                                if '0.0.0.0' in line and local_ip in line:
                                    parts = line.split()
                                    if len(parts) >= 3:
                                        gateway = parts[2]
                                        break
                    else:
                        # Linux/Mac
                        result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
                        if result.returncode == 0:
                            lines = result.stdout.split('\n')
                            for line in lines:
                                if 'default' in line:
                                    parts = line.split()
                                    if 'via' in parts:
                                        idx = parts.index('via')
                                        if idx + 1 < len(parts):
                                            gateway = parts[idx + 1]
                                            break
                except:
                    pass

            # Update labels
            if local_ip:
                self.local_ip_label.configure(text=f"Local IP: {local_ip}")
            else:
                self.local_ip_label.configure(text="Local IP: Not connected")

            if subnet_mask:
                self.subnet_label.configure(text=f"Subnet: {subnet_mask}")
            else:
                self.subnet_label.configure(text="Subnet: Unknown")

            if gateway:
                self.gateway_label.configure(text=f"Gateway: {gateway}")
            else:
                self.gateway_label.configure(text="Gateway: Unknown")

            if mac_address:
                self.mac_label.configure(text=f"MAC: {mac_address}")
            else:
                self.mac_label.configure(text="MAC: Unknown")

            # Internet status with color
            if internet_connected:
                self.internet_status_label.configure(text="Internet: Connected", text_color="#4CAF50")
            else:
                self.internet_status_label.configure(text="Internet: Disconnected", text_color="#F44336")

        except Exception as e:
            print(f"Error updating network information: {e}")
            self.local_ip_label.configure(text="Local IP: Error")
            self.subnet_label.configure(text="Subnet: Error")
            self.gateway_label.configure(text="Gateway: Error")
            self.mac_label.configure(text="MAC: Error")
            self.internet_status_label.configure(text="Internet: Error", text_color="#F44336")

    def get_external_ip(self):
        """Get external IP address in a separate thread"""
        try:
            # Try multiple services for redundancy
            services = [
                'https://api.ipify.org',
                'https://checkip.amazonaws.com',
                'https://ifconfig.me/ip'
            ]

            import urllib.request
            for service in services:
                try:
                    with urllib.request.urlopen(service, timeout=5) as response:
                        external_ip = response.read().decode('utf-8').strip()
                        # Update label on main thread
                        self.root.after(0, lambda: self.external_ip_label.configure(
                            text=f"External IP: {external_ip}"))
                        return
                except:
                    continue

            # If all services fail
            self.root.after(0, lambda: self.external_ip_label.configure(
                text="External IP: Unable to detect"))

        except Exception as e:
            print(f"Error getting external IP: {e}")
            self.root.after(0, lambda: self.external_ip_label.configure(
                text="External IP: Error"))

    def run_speed_test(self):
        """Run internet speed test"""
        if not SPEEDTEST_AVAILABLE:
            messagebox.showerror("Speed Test", "speedtest-cli not available")
            return

        # Create speed test window
        speed_window = ctk.CTkToplevel(self.root)
        speed_window.title("Internet Speed Test")
        speed_window.geometry("450x350")
        speed_window.transient(self.root)
        speed_window.grab_set()  # Make modal

        # Status label
        status_label = ctk.CTkLabel(
            speed_window,
            text="Initializing speed test...",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        status_label.pack(pady=20, padx=20, fill="x")

        # Progress bar
        progress_bar = ctk.CTkProgressBar(speed_window)
        progress_bar.pack(pady=10, padx=20, fill="x")
        progress_bar.set(0)

        # Results label
        results_label = ctk.CTkLabel(speed_window, text="", justify=ctk.LEFT)
        results_label.pack(pady=10, padx=20, fill="x")

        # --- Button Frame ---
        button_frame = ctk.CTkFrame(speed_window)
        button_frame.pack(pady=20, padx=20, fill="x")

        # Center buttons using a nested frame
        center_frame = ctk.CTkFrame(button_frame)
        center_frame.pack(expand=True)

        action_button = ctk.CTkButton(center_frame, text="Cancel")
        action_button.pack(side="left", padx=10)

        close_button = ctk.CTkButton(center_frame, text="Close", command=speed_window.destroy)
        close_button.pack(side="left", padx=10)
        close_button.configure(state="disabled")

        # --- Speed Test Logic ---
        speed_test_runner = None
        test_thread = None
        test_completed = False

        def start_test():
            nonlocal speed_test_runner, test_thread, test_completed
            test_completed = False

            # Reset UI
            status_label.configure(text="Initializing speed test...")
            progress_bar.set(0)
            results_label.configure(text="")
            action_button.configure(text="Cancel", state="normal")
            close_button.configure(state="disabled")

            # Create and start a new test runner
            speed_test_runner = SpeedTestRunner(
                progress_callback=on_progress,
                status_callback=on_status,
                result_callback=on_result,
                error_callback=on_error
            )

            def cancel_test():
                speed_test_runner.cancel()
                action_button.configure(text="Retry", command=start_test)
                close_button.configure(state="normal")
                status_label.configure(text="Speed test cancelled")
                progress_bar.set(0)

            action_button.configure(command=cancel_test)

            test_thread = threading.Thread(target=speed_test_runner.run_test, daemon=True)
            test_thread.start()

        def on_progress(value):
            progress_bar.set(value / 100)

        def on_status(status):
            status_label.configure(text=status)

        def on_result(result):
            nonlocal test_completed
            test_completed = True

            server_info = ""
            if 'server' in result and result['server']:
                server = result['server']
                server_info = f"\nServer: {server.get('sponsor', 'Unknown')} ({server.get('name', 'Unknown')})"

            results_text = (f"Download: {result['download']:.2f} Mbps\n"
                          f"Upload: {result['upload']:.2f} Mbps\n"
                          f"Ping: {result['ping']:.2f} ms{server_info}")

            results_label.configure(text=results_text)
            status_label.configure(text="Speed test completed!")

            action_button.configure(text="Retry", command=start_test)
            close_button.configure(state="normal")

        def on_error(error):
            nonlocal test_completed
            test_completed = True

            results_label.configure(text=f"Error: {error}")
            status_label.configure(text="Speed test failed")

            action_button.configure(text="Retry", command=start_test)
            close_button.configure(state="normal")

        # --- Start the first test ---
        start_test()

    def save_report(self):
        """Save scan results to CSV"""
        if not self.all_devices:
            messagebox.showwarning("No Data", "No devices to save")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)

                    # Headers
                    writer.writerow([
                        "IP Address", "MAC Address", "Hostname",
                        "Manufacturer", "Response Time (ms)", "Web Service", "Status"
                    ])

                    # Data
                    for device in self.all_devices:
                        writer.writerow([
                            device['ip'],
                            device.get('mac', 'Unknown'),
                            device.get('hostname', 'Unknown'),
                            device.get('manufacturer', 'Unknown'),
                            f"{device.get('response_time', 0) * 1000:.1f}",
                            device.get('web_service', 'None'),
                            device.get('status', 'Unknown')
                        ])

                messagebox.showinfo("Success", f"Report saved to {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {e}")

    def open_file(self):
        """Open CSV file"""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                self.clear_device_table()

                with open(filename, 'r') as csvfile:
                    reader = csv.DictReader(csvfile)

                    for row in reader:
                        device = {
                            'ip': row.get('IP Address', ''),
                            'mac': row.get('MAC Address', 'Unknown'),
                            'hostname': row.get('Hostname', 'Unknown'),
                            'manufacturer': row.get('Manufacturer', 'Unknown'),
                            'response_time': float(row.get('Response Time (ms)', '0')) / 1000,
                            'web_service': row.get('Web Service', 'None'),
                            'status': row.get('Status', 'Unknown')
                        }

                        self.all_devices.append(device)
                        self.add_device_to_table(device)

                self.update_status(f"Loaded {len(self.all_devices)} devices from {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def on_window_close(self):
        """Handle window close event - minimize to tray if available"""
        if self.tray_manager:
            # Minimize to system tray
            self.root.withdraw()
            # Show notification (optional)
            try:
                if hasattr(self.tray_manager.icon, 'notify'):
                    self.tray_manager.icon.notify(
                        "I.T Assistant minimized to tray",
                        "Double-click the tray icon to restore"
                    )
            except:
                pass
        else:
            # No tray manager, so close everything and quit
            # Close live monitor window if open
            if hasattr(self, 'current_monitor_window') and self.current_monitor_window:
                try:
                    self.current_monitor_window.destroy()
                except:
                    pass
            # Quit the application
            self.root.quit()

    def run(self):
        """Start application"""
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

