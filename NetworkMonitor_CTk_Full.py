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

# Try to import advanced modules with fallbacks
try:
    from scapy.layers.l2 import ARP, Ether, srp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    # print("Warning: Scapy not available. Using basic ping scanning.")

try:
    from manuf import manuf
    MANUF_AVAILABLE = True
except ImportError:
    MANUF_AVAILABLE = False
    # print("Warning: manuf not available. MAC vendor lookup disabled.")

try:
    import speedtest as speedtest_module
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False
    # print("Warning: speedtest-cli not available. Speed test disabled.")

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
        """Get hostname for IP"""
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return None
    
    def get_manufacturer(self, mac):
        """Get manufacturer from MAC"""
        if self.mac_parser:
            try:
                return self.mac_parser.get_manuf(mac)
            except:
                pass
        return None
    
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
                        'status': 'Online'
                    })
                    
            except Exception as e:
                print(f"ARP scan error for {ip}: {e}")
        else:
            # Fallback to ping scanning
            if self.ping_host_simple(ip):
                hostname = self.get_hostname(ip)
                web_service = self.check_web_port(ip)
                
                devices.append({
                    'ip': str(ip),
                    'mac': 'Unknown',
                    'response_time': 0.1,  # Estimated
                    'web_service': web_service,
                    'hostname': hostname,
                    'manufacturer': 'Unknown',
                    'status': 'Online'
                })
                
        return devices
    
    def ping_host_simple(self, ip):
        """Simple ping implementation"""
        try:
            if platform.system().lower() == 'windows':
                result = subprocess.run(['ping', '-n', '1', '-w', '1000', str(ip)], 
                                      capture_output=True, text=True, timeout=2, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', str(ip)], 
                                      capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except:
            return False
    
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
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("I.T Assistant - Network Monitor")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
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
        
        # Setup UI
        self.setup_ui()
        self.setup_menu()
        
        # Auto-detect network
        self.auto_detect_network()
    
    def setup_ui(self):
        """Setup main UI"""
        # Configure grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create sidebar
        self.create_sidebar()
        
        # Create main content
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
    
    def setup_menu(self):
        """Setup custom themed menubar using CustomTkinter"""
        # Create custom menubar frame
        self.menubar = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        self.menubar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        self.menubar.grid_columnconfigure(0, weight=1)
        
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
        
        # Adjust main content grid to account for menubar
        self.root.grid_rowconfigure(1, weight=1)
    
    def create_sidebar(self):
        """Create sidebar with controls"""
        self.sidebar = ctk.CTkFrame(self.root, width=280, corner_radius=0)
        self.sidebar.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)  # Flexible space after tools

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
                size=(80, 80)
            )
            logo_label = ctk.CTkLabel(
                self.sidebar,
                image=logo_image,
                text=""
            )
            logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        except Exception as e:
            print(f"Could not load logo: {e}")
            # Fallback - create empty space
            logo_label = ctk.CTkLabel(self.sidebar, text="", height=80)
            logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Title
        title_label = ctk.CTkLabel(
            self.sidebar, 
            text="I.T Assistant",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=1, column=0, padx=20, pady=(10, 5))

        subtitle_label = ctk.CTkLabel(
            self.sidebar, 
            text="Network Monitor",
            font=ctk.CTkFont(size=16)
        )
        subtitle_label.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Network settings frame
        network_frame = ctk.CTkFrame(self.sidebar)
        network_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        network_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(network_frame, text="Network Range:", 
                    font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5))
        
        self.ip_input = ctk.CTkEntry(network_frame, placeholder_text="192.168.1.0/24")
        self.ip_input.pack(padx=10, pady=5, fill="x")
        
        self.auto_detect_btn = ctk.CTkButton(
            network_frame,
            text="Auto-Detect",
            command=self.auto_detect_network,
            height=32
        )
        self.auto_detect_btn.pack(padx=10, pady=(5, 10), fill="x")
        
        # Search frame
        search_frame = ctk.CTkFrame(self.sidebar)
        search_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(search_frame, text="Search Devices:", 
                    font=ctk.CTkFont(weight="bold")).pack(padx=10, pady=(10, 5))
        
        self.search_input = ctk.CTkEntry(search_frame, placeholder_text="IP, MAC, or hostname...")
        self.search_input.pack(padx=10, pady=(5, 10), fill="x")
        self.search_input.bind("<KeyRelease>", self.filter_devices)
        
        # Expanded Network Tools frame
        tools_frame = ctk.CTkFrame(self.sidebar)
        tools_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        tools_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(tools_frame, text="Network Tools", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(padx=10, pady=(10, 5))
        
        # Standard button styling for all tools
        button_height = 36
        button_font = ctk.CTkFont(size=13, weight="bold")
        
        # Start Network Scan button
        self.scan_btn = ctk.CTkButton(
            tools_frame,
            text="Start Network Scan",
            command=self.toggle_scan,
            height=button_height,
            font=button_font
        )
        self.scan_btn.pack(padx=10, pady=5, fill="x")
        
        # Live Monitor Selected button
        self.live_monitor_btn = ctk.CTkButton(
            tools_frame,
            text="Live Monitor Selected",
            command=self.open_live_monitor,
            height=button_height,
            font=button_font
        )
        self.live_monitor_btn.pack(padx=10, pady=5, fill="x")
        
        # Internet Speed Test button
        self.speedtest_btn = ctk.CTkButton(
            tools_frame,
            text="Internet Speed Test",
            command=self.run_speed_test,
            height=button_height,
            font=button_font
        )
        self.speedtest_btn.pack(padx=10, pady=(5, 15), fill="x")
        
        # Theme switch
        self.theme_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Dark Mode",
            command=self.change_theme
        )
        self.theme_switch.grid(row=6, column=0, padx=20, pady=10)
        self.theme_switch.select()
    
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
        
        # Progress and summary frame
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(padx=10, pady=(10, 5), fill="x")
        self.progress_bar.set(0)
        
        self.summary_label = ctk.CTkLabel(
            progress_frame,
            text="Devices found: 0 | Problematic (>500ms): 0"
        )
        self.summary_label.pack(padx=10, pady=(5, 10))
        
        # Device table frame
        self.table_frame = ctk.CTkScrollableFrame(
            self.main_frame, 
            label_text="Discovered Devices"
        )
        self.table_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.table_frame.grid_columnconfigure(1, weight=1)
        
        # Table headers
        headers = ["Select", "IP Address", "MAC Address", "Hostname", "Manufacturer", "Response Time", "Web Service", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.table_frame, 
                text=header,
                font=ctk.CTkFont(weight="bold")
            )
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
            # Get local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            
            # Convert to network range
            ip_parts = local_ip.split('.')
            network = f"{'.'.join(ip_parts[:3])}.0/24"
            
            self.ip_input.delete(0, tk.END)
            self.ip_input.insert(0, network)
            self.update_status(f"Auto-detected network: {network}")
            
        except Exception as e:
            self.update_status(f"Auto-detect failed: {e}")
    
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
        
        self.scanning = True
        self.scan_btn.configure(text="Stop Scan", fg_color="#d32f2f")
        self.progress_bar.set(0)
        self.info_label.configure(text="Scanning...")
        
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
        self.scan_btn.configure(text="Start Network Scan", fg_color="#1f538d")
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
        self.scan_btn.configure(text="Start Network Scan", fg_color="#1f538d")
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
    
    def add_device_to_table(self, device):
        """Add device to table"""
        if not device:
            return
            
        row_num = len(self.device_rows) + 1
        row_widgets = []
        
        # Select checkbox
        var = tk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            self.table_frame, 
            text="",
            variable=var,
            command=lambda: self.toggle_device_selection(device, var.get())
        )
        checkbox.grid(row=row_num, column=0, padx=5, pady=2)
        row_widgets.append(checkbox)
        
        # IP Address (clickable for nmap)
        ip_btn = ctk.CTkButton(
            self.table_frame,
            text=device['ip'],
            width=120,
            height=24,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray80", "gray20"),
            command=lambda: self.show_nmap_dialog(device['ip'])
        )
        ip_btn.grid(row=row_num, column=1, padx=5, pady=2, sticky="ew")
        row_widgets.append(ip_btn)
        
        # MAC Address
        mac_label = ctk.CTkLabel(self.table_frame, text=device.get('mac', 'Unknown'))
        mac_label.grid(row=row_num, column=2, padx=5, pady=2)
        row_widgets.append(mac_label)
        
        # Hostname
        hostname_label = ctk.CTkLabel(self.table_frame, text=device.get('hostname', 'Unknown'))
        hostname_label.grid(row=row_num, column=3, padx=5, pady=2)
        row_widgets.append(hostname_label)
        
        # Manufacturer
        manufacturer_label = ctk.CTkLabel(self.table_frame, text=device.get('manufacturer', 'Unknown'))
        manufacturer_label.grid(row=row_num, column=4, padx=5, pady=2)
        row_widgets.append(manufacturer_label)
        
        # Response Time
        response_ms = device.get('response_time', 0) * 1000
        response_color = "#f44336" if response_ms > 500 else None
        response_label = ctk.CTkLabel(
            self.table_frame, 
            text=f"{response_ms:.0f}ms",
            text_color=response_color
        )
        response_label.grid(row=row_num, column=5, padx=5, pady=2)
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
            web_btn.grid(row=row_num, column=6, padx=5, pady=2)
            row_widgets.append(web_btn)
        else:
            web_label = ctk.CTkLabel(self.table_frame, text="None")
            web_label.grid(row=row_num, column=6, padx=5, pady=2)
            row_widgets.append(web_label)
        
        # Actions button
        actions_btn = ctk.CTkButton(
            self.table_frame,
            text="Details",
            width=60,
            height=24,
            command=lambda: self.show_device_details(device)
        )
        actions_btn.grid(row=row_num, column=7, padx=5, pady=2)
        row_widgets.append(actions_btn)
        
        self.device_rows.append(row_widgets)
        
        # Configure column weights
        for i in range(8):
            self.table_frame.grid_columnconfigure(i, weight=1 if i == 1 else 0)
    
    def toggle_device_selection(self, device, selected):
        """Toggle device selection for monitoring"""
        if selected:
            if device not in self.selected_devices:
                self.selected_devices.append(device)
        else:
            if device in self.selected_devices:
                self.selected_devices.remove(device)
    
    def filter_devices(self, event=None):
        """Filter devices based on search"""
        query = self.search_input.get().lower()
        
        # Clear current table
        for row in self.device_rows:
            for widget in row:
                widget.destroy()
        self.device_rows.clear()
        
        # Re-add filtered devices
        for device in self.all_devices:
            if (query in device['ip'].lower() or 
                query in device.get('mac', '').lower() or 
                query in device.get('hostname', '').lower()):
                self.add_device_to_table(device)
    
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
        """Open live monitoring dialog with graphs"""
        if not self.selected_devices:
            messagebox.showwarning("No Devices", "Please select at least one device to monitor.")
            return
        
        monitor_window = ctk.CTk()
        monitor_window.title("Live Device Monitoring - Real-time Graphs")
        
        device_count = len(self.selected_devices)
        screen_width = monitor_window.winfo_screenwidth()
        screen_height = monitor_window.winfo_screenheight()
        
        max_height = int(screen_height * 0.9)
        available_height = max_height - 150
        optimal_height_per_device = min(350, available_height // device_count)
        min_height_per_device = 200
        if optimal_height_per_device < min_height_per_device:
            height_per_device = min_height_per_device
            window_height = max_height
        else:
            height_per_device = optimal_height_per_device
            window_height = (device_count * height_per_device) + 150
        
        if screen_width >= 1920:
            window_width = 1400
        elif screen_width >= 1600:
            window_width = 1200
        elif screen_width >= 1366:
            window_width = 1000
        else:
            window_width = min(screen_width - 100, 900)
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        monitor_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        monitor_window.state('normal')
        plt.style.use('dark_background')
        
        if screen_width >= 1920:
            max_cols = min(3, device_count)
        elif screen_width >= 1400:
            max_cols = min(2, device_count)
        elif screen_width >= 1024:
            max_cols = min(2, device_count)
        else:
            max_cols = 1
        cols = min(max_cols, device_count)
        rows = (device_count + cols - 1) // cols
        min_graph_width = 600 if cols == 1 else 500
        window_width = min(screen_width - 50, cols * min_graph_width + 60)
        available_height_for_graphs = max_height - 180
        if device_count <= 4:
            min_graph_height = 350
        elif device_count <= 6:
            min_graph_height = 240
        elif device_count <= 8:
            min_graph_height = 200
        elif device_count <= 12:
            min_graph_height = 180
        else:
            min_graph_height = 160
        required_height = rows * min_graph_height + 150
        if required_height > max_height:
            min_graph_height = max(160, (available_height_for_graphs // rows))
            window_height = max_height
        else:
            window_height = required_height
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        monitor_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        control_frame = ctk.CTkFrame(monitor_window, height=80)
        control_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        control_frame.pack_propagate(False)

        main_frame = ctk.CTkFrame(monitor_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        main_frame.pack_propagate(False)

        column_frames = []
        if cols > 1:
            columns_container = ctk.CTkFrame(main_frame)
            columns_container.pack(fill="both", expand=True, padx=5, pady=5)
            columns_container.pack_propagate(False)
            for col in range(cols):
                col_frame = ctk.CTkFrame(columns_container)
                col_frame.pack(side="left", fill="both", expand=True, padx=5)
                col_frame.pack_propagate(False)
                column_frames.append(col_frame)
        else:
            column_frames.append(main_frame)
        
        self.current_monitor_window = monitor_window
        self.monitor_graphs = {}
        
        for i, device in enumerate(self.selected_devices):
            row = i // cols
            col = i % cols
            ip = device['ip']
            target_frame = column_frames[col % len(column_frames)]
            device_frame = ctk.CTkFrame(target_frame)
            padding_y = 5 if device_count > 6 else 8 if device_count > 4 else 10
            padding_x = 5 if device_count > 6 else 8 if device_count > 4 else 10
            device_frame.pack(pady=padding_y, padx=padding_x, fill="both", expand=True)
            device_frame.pack_propagate(False)
            info_label = ctk.CTkLabel(
                device_frame,
                text=f"Monitoring: {ip} ({device.get('hostname', 'Unknown')}) - {device.get('manufacturer', 'Unknown')}",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            info_label.pack(pady=5)
            available_width = window_width - (cols * 40)
            graph_width_pixels = available_width // cols
            graph_width = max(4, min(10, graph_width_pixels / 100))
            graph_height = max(2.0, min(6, (min_graph_height - 80) / 80))
            fig = Figure(figsize=(graph_width, graph_height), facecolor='#2b2b2b')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#1e1e1e')
            ax.grid(True, alpha=0.3, color='#444444')
            ax.set_xlabel('Time', color='white')
            ax.set_ylabel('Latency (ms)', color='white')
            ax.set_title(f'Real-time Latency for {ip}', color='white', fontsize=14, fontweight='bold')
            ax.tick_params(colors='white')
            line, = ax.plot([], [], 'g-', linewidth=2, label='Latency')
            ax.legend()
            canvas = FigureCanvasTkAgg(fig, device_frame)
            canvas_padding_y = 5 if device_count > 6 else 8 if device_count > 4 else 10
            canvas_padding_x = 5 if device_count > 6 else 8 if device_count > 4 else 10
            canvas.get_tk_widget().pack(pady=canvas_padding_y, padx=canvas_padding_x, fill="both", expand=True)
            self.monitor_graphs[ip] = {
                'figure': fig,
                'axis': ax,
                'line': line,
                'canvas': canvas,
                'times': [],
                'latencies': [],
                'status_line': None
            }
            status_frame = ctk.CTkFrame(device_frame)
            status_frame.pack(pady=(0, 10), padx=10, fill="x")
            status_label = ctk.CTkLabel(
                status_frame,
                text="Status: Initializing...",
                font=ctk.CTkFont(size=12)
            )
            status_label.pack(side="left", padx=10, pady=5)
            stats_label = ctk.CTkLabel(
                status_frame,
                text="Avg: --ms | Min: --ms | Max: --ms | Loss: --%",
                font=ctk.CTkFont(size=12)
            )
            stats_label.pack(side="right", padx=10, pady=5)
            self.monitor_graphs[ip]['status_label'] = status_label
            self.monitor_graphs[ip]['stats_label'] = stats_label
            if ip not in self.device_monitors:
                monitor = DeviceMonitor(ip, interval=1)
                monitor.start(
                    update_callback=self.update_graph_status,
                    graph_callback=self.update_monitor_graph
                )
                self.device_monitors[ip] = monitor
        self.monitor_paused = False
        pause_btn = ctk.CTkButton(
            control_frame,
            text="Pause Monitoring",
            command=lambda: self.toggle_monitoring_pause(pause_btn)
        )
        pause_btn.pack(side="left", padx=10)
        export_btn = ctk.CTkButton(
            control_frame,
            text="Export Data",
            command=self.export_monitoring_data
        )
        export_btn.pack(side="left", padx=10)
        self.is_maximized = False
        maximize_btn = ctk.CTkButton(
            control_frame,
            text="Maximize",
            command=lambda: self.toggle_maximize(monitor_window, maximize_btn)
        )
        maximize_btn.pack(side="right", padx=10)
        def on_close():
            for monitor in self.device_monitors.values():
                monitor.stop()
            self.device_monitors.clear()
            self.monitor_graphs.clear()
            if hasattr(self, 'current_monitor_window'):
                self.current_monitor_window = None
            plt.close('all')
            monitor_window.destroy()
        monitor_window.protocol("WM_DELETE_WINDOW", on_close)

    def toggle_maximize(self, window, button):
        """Toggle maximize/restore window state and ensure uniform fill"""
        try:
            if not self.is_maximized:
                window.state('zoomed')
                button.configure(text="Restore")
                self.is_maximized = True
            else:
                window.state('normal')
                button.configure(text="Maximize")
                self.is_maximized = False
            window.update_idletasks()
            # Ensure all frames fill available space
            if hasattr(self, 'current_monitor_window') and self.current_monitor_window:
                for child in self.current_monitor_window.winfo_children():
                    try:
                        child.pack_configure(fill="both", expand=True)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error toggling maximize: {e}")
            try:
                if not self.is_maximized:
                    window.attributes('-zoomed', True)
                    button.configure(text="Restore")
                    self.is_maximized = True
                else:
                    window.attributes('-zoomed', False)
                    button.configure(text="Maximize")
                    self.is_maximized = False
                window.update_idletasks()
                if hasattr(self, 'current_monitor_window') and self.current_monitor_window:
                    for child in self.current_monitor_window.winfo_children():
                        try:
                            child.pack_configure(fill="both", expand=True)
                        except Exception:
                            pass
            except:
                if not self.is_maximized:
                    screen_width = window.winfo_screenwidth()
                    screen_height = window.winfo_screenheight()
                    window.geometry(f"{screen_width}x{screen_height}+0+0")
                    button.configure(text="Restore")
                    self.is_maximized = True
                else:
                    window.geometry("1200x800+100+100")
                    button.configure(text="Maximize")
                    self.is_maximized = False
    
    def export_monitoring_data(self):
        """Export monitoring data to CSV"""
        if not self.device_monitors:
            messagebox.showwarning("No Data", "No monitoring data to export")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialname=f"monitoring_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Headers
                    writer.writerow(["Timestamp", "IP Address", "Latency (ms)", "Status"])
                    
                    # Data from all monitors
                    for ip, monitor in self.device_monitors.items():
                        for timestamp, latency, status in monitor.buffer:
                            writer.writerow([
                                datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                                ip,
                                f"{latency:.2f}" if not math.isnan(latency) else "N/A",
                                status
                            ])
                
                messagebox.showinfo("Success", f"Monitoring data exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")
    
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
    
    
    def toggle_theme_via_switch(self):
        """Toggle theme by programmatically triggering the theme switch"""
        # Toggle the switch state, which will automatically call change_theme()
        if self.theme_switch.get():
            self.theme_switch.deselect()
        else:
            self.theme_switch.select()
        
        # Manually trigger the change_theme method since deselect/select might not always trigger it
        self.change_theme()
    
    def change_theme(self):
        """Change theme based on switch"""
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        
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
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.configure(text=message)
    
    def update_graph_status(self, ip, latency, status, timestamp):
        """Update graph status labels"""
        def _update_on_main_thread():
            if ip not in self.monitor_graphs:
                return

            graph_data = self.monitor_graphs[ip]

            # Update status
            if status == 'up':
                status_text = f"Status: Online ({latency:.1f}ms)"
                graph_data['status_label'].configure(text=status_text, text_color="#4CAF50")
            else:
                status_text = "Status: Offline"
                graph_data['status_label'].configure(text=status_text, text_color="#F44336")

            # Calculate statistics
            if ip in self.device_monitors:
                monitor = self.device_monitors[ip]
                valid_latencies = [lat for _, lat, stat in monitor.buffer if stat == 'up' and not math.isnan(lat)]

                total_pings = len(monitor.buffer)
                successful_pings = len(valid_latencies)
                failed_pings = total_pings - successful_pings

                if valid_latencies:
                    avg_latency = sum(valid_latencies) / len(valid_latencies)
                    min_latency = min(valid_latencies)
                    max_latency = max(valid_latencies)

                    loss_percent = (failed_pings / total_pings * 100) if total_pings > 0 else 0

                    stats_text = f"Avg: {avg_latency:.1f}ms | Min: {min_latency:.1f}ms | Max: {max_latency:.1f}ms | Loss: {loss_percent:.1f}%"
                else:
                    stats_text = "Avg: --ms | Min: --ms | Max: --ms | Loss: 100%"

                graph_data['stats_label'].configure(text=stats_text)

        # Schedule GUI update on main thread
        if hasattr(self, 'root'):
            self.root.after(0, _update_on_main_thread)

    def update_monitor_graph(self, ip, buffer_data):
        """Update monitoring graph with new data"""
        def _update_graph_on_main_thread():
            if ip not in self.monitor_graphs or self.monitor_paused:
                return

            graph_data = self.monitor_graphs[ip]

            # Extract times and latencies
            times = []
            latencies = []

            for timestamp, latency, status in buffer_data:
                times.append(datetime.fromtimestamp(timestamp))
                if status == 'up' and not math.isnan(latency):
                    latencies.append(latency)
                else:
                    latencies.append(None)  # None for disconnected points

            # Update graph
            if times and latencies:
                # Clear previous data
                graph_data['line'].set_data([], [])

                # Plot connected segments
                connected_times = []
                connected_latencies = []

                for i, (time, latency) in enumerate(zip(times, latencies)):
                    if latency is not None:
                        connected_times.append(time)
                        connected_latencies.append(latency)
                    else:
                        # Plot accumulated connected data
                        if connected_times:
                            graph_data['axis'].plot(connected_times, connected_latencies, 'g-', linewidth=2)
                            connected_times = []
                            connected_latencies = []

                # Plot remaining connected data
                if connected_times:
                    graph_data['line'].set_data(connected_times, connected_latencies)

                # Set axis limits
                if times:
                    graph_data['axis'].set_xlim(min(times), max(times))

                valid_latencies = [lat for lat in latencies if lat is not None]
                if valid_latencies:
                    min_lat = min(valid_latencies)
                    max_lat = max(valid_latencies)
                    margin = (max_lat - min_lat) * 0.1 if max_lat > min_lat else 1
                    graph_data['axis'].set_ylim(max(0, min_lat - margin), max_lat + margin)

                # Format time axis
                graph_data['axis'].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                graph_data['axis'].tick_params(axis='x', rotation=45)

                # Refresh canvas
                graph_data['canvas'].draw()

        # Schedule GUI update on main thread
        if hasattr(self, 'root'):
            self.root.after(0, _update_graph_on_main_thread)

    def toggle_monitoring_pause(self, button):
        """Toggle monitoring pause state"""
        self.monitor_paused = not self.monitor_paused

        if self.monitor_paused:
            button.configure(text="Resume Monitoring")
        else:
            button.configure(text="Pause Monitoring")

    def run(self):
        """Start application"""
        self.update_status("Ready to scan network")
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = NetworkMonitorApp()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Application Error", f"Failed to start application: {e}")

if __name__ == "__main__":
    main()
