#!/usr/bin/env python3
"""
Live Monitor Module for Network Monitor
Handles real-time device monitoring with graphical display
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from settings import settings_manager
from email_alert_manager import email_alert_manager
import threading
import time
import subprocess
import platform
import re
import math
import csv
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    import speedtest as speedtest_module
    SPEEDTEST_AVAILABLE = True
except ImportError:
    SPEEDTEST_AVAILABLE = False


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


class LiveMonitor:
    """Live monitoring interface"""

    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.device_monitors = {}
        self.monitor_graphs = {}
        self.monitor_tooltips = {}
        self.device_info = {}
        self.monitor_paused = False
        self.is_maximized = False
        self.current_monitor_window = None
        self.minimized_monitor_window = None

    def open_live_monitor(self, selected_devices):
        """Open live monitoring dialog with graphs - Grid layout with 4x2 max visible"""
        if not selected_devices:
            messagebox.showwarning("No Devices", "Please select at least one device to monitor.")
            return
        
        # Close existing monitor window if open
        if hasattr(self, 'current_monitor_window') and self.current_monitor_window:
            self.current_monitor_window.destroy()
        
        monitor_window = ctk.CTk()
        monitor_window.title("Live Device Monitoring - Real-time Graphs")
        
        device_count = len(selected_devices)
        screen_width = monitor_window.winfo_screenwidth()
        screen_height = monitor_window.winfo_screenheight()
        
        # Dynamic grid layout based on device count
        MAX_COLS = 4  # Maximum columns per row
        
        # Determine optimal grid configuration
        if device_count <= 2:
            GRID_COLS = device_count  # 1 or 2 devices in single row
        elif device_count <= 4:
            GRID_COLS = min(device_count, MAX_COLS)  # Up to 4 in single row
        else:
            GRID_COLS = MAX_COLS  # Use max columns for more than 4 devices
        
        # Calculate window dimensions
        # Each device graph should be at least 300px wide and 250px tall
        MIN_DEVICE_WIDTH = 300
        MIN_DEVICE_HEIGHT = 250
        
        # Calculate window size based on actual grid columns needed
        window_width = min(screen_width - 100, (GRID_COLS * MIN_DEVICE_WIDTH) + 60)
        
        # Determine rows needed
        total_rows = math.ceil(device_count / GRID_COLS)
        
        # Only show second row if more than 4 devices
        if device_count <= 4:
            visible_rows = 1  # Always single row for 4 or fewer devices
        else:
            MAX_VISIBLE_ROWS = 2  # Show up to 2 rows for more than 4 devices
            visible_rows = min(MAX_VISIBLE_ROWS, total_rows)
        
        window_height = min(screen_height - 100, (visible_rows * MIN_DEVICE_HEIGHT) + 180)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        monitor_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        monitor_window.minsize(1280, 720)  # Set minimum size
        monitor_window.state('normal')
        
        # Set matplotlib style for dark theme
        plt.style.use('dark_background')
        
        # Control frame at bottom (fixed height)
        control_frame = ctk.CTkFrame(monitor_window, height=80)
        control_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        control_frame.pack_propagate(False)
        
        # Main scrollable frame for device graphs
        main_container = ctk.CTkFrame(monitor_window)
        main_container.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # Create scrollable frame for devices
        scrollable_frame = ctk.CTkScrollableFrame(
            main_container,
            label_text="Device Monitors",
            label_font=ctk.CTkFont(size=16, weight="bold")
        )
        scrollable_frame.pack(fill="both", expand=True)
        
        # Configure grid for scrollable frame
        for col in range(GRID_COLS):
            scrollable_frame.grid_columnconfigure(col, weight=1, uniform="column")
        
        # Calculate total rows needed
        total_rows = math.ceil(device_count / GRID_COLS)
        for row in range(total_rows):
            scrollable_frame.grid_rowconfigure(row, weight=1, uniform="row")
        
        # Special handling for last row if it has fewer items
        last_row_items = device_count % GRID_COLS
        if last_row_items > 0 and total_rows > 1:
            # We'll handle column spanning for last row items to fill space
            pass
        
        self.current_monitor_window = monitor_window
        self.monitor_graphs = {}
        self.monitor_tooltips = {}  # Store tooltip labels for hover functionality
        
        # Create device monitoring widgets in grid layout
        for i, device in enumerate(selected_devices):
            row = i // GRID_COLS
            col = i % GRID_COLS
            ip = device['ip']
            
            # Calculate column span for last row items to fill space
            columnspan = 1
            if row == total_rows - 1 and last_row_items > 0:
                # For the last row, distribute columns evenly
                if last_row_items == 1:
                    columnspan = GRID_COLS  # Single item spans all columns
                    col = 0  # Center it
                elif last_row_items == 2:
                    columnspan = GRID_COLS // 2  # Each item spans half
                    col = col * columnspan
                elif last_row_items == 3:
                    # For 3 items, distribute across 4 columns
                    if GRID_COLS == 4:
                        if i % GRID_COLS == 0:
                            columnspan = 2  # First item spans 2 columns
                            col = 0
                        elif i % GRID_COLS == 1:
                            columnspan = 1  # Second item spans 1 column
                            col = 2
                        else:
                            columnspan = 1  # Third item spans 1 column
                            col = 3
            
            # Create frame for this device
            device_frame = ctk.CTkFrame(scrollable_frame, corner_radius=10)
            device_frame.grid(row=row, column=col, columnspan=columnspan, padx=10, pady=10, sticky="nsew")
            
            # Configure device frame to expand
            device_frame.grid_rowconfigure(1, weight=1)  # Graph row should expand
            device_frame.grid_columnconfigure(0, weight=1)
            
            # Device info label
            info_label = ctk.CTkLabel(
                device_frame,
                text=f"{ip} - {device.get('hostname', 'Unknown')}",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            info_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
            
            # Manufacturer label
            manuf_label = ctk.CTkLabel(
                device_frame,
                text=device.get('manufacturer', 'Unknown'),
                font=ctk.CTkFont(size=10)
            )
            manuf_label.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
            
            # Create tooltip label for hover functionality
            tooltip_label = ctk.CTkLabel(
                device_frame,
                text="",
                font=ctk.CTkFont(size=10),
                fg_color=("gray90", "gray20"),
                corner_radius=6,
                padx=8,
                pady=4
            )
            self.monitor_tooltips[ip] = tooltip_label
            
            # Create matplotlib figure for graph
            # Dynamic sizing based on available space
            fig = Figure(figsize=(5, 3.5), facecolor='#2b2b2b', tight_layout=True)
            ax = fig.add_subplot(111)
            ax.set_facecolor('#1e1e1e')
            ax.grid(True, alpha=0.3, color='#444444')
            ax.set_xlabel('Time', color='white', fontsize=9)
            ax.set_ylabel('Latency (ms)', color='white', fontsize=9)
            ax.set_title(f'Real-time Latency', color='white', fontsize=11, fontweight='bold')
            ax.tick_params(colors='white', labelsize=8)
            line, = ax.plot([], [], 'g-', linewidth=2, label='Latency')
            ax.legend(fontsize=8)
            
            # Canvas for matplotlib figure
            canvas = FigureCanvasTkAgg(fig, device_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
            
            # Bind hover events to canvas widget
            canvas_widget.bind("<Enter>", lambda e, ip_addr=ip: self.show_monitor_tooltip(ip_addr))
            canvas_widget.bind("<Leave>", lambda e, ip_addr=ip: self.hide_monitor_tooltip(ip_addr))
            canvas_widget.bind("<Motion>", lambda e, ip_addr=ip: self.update_tooltip_position(e, ip_addr))
            
            # Store graph data
            self.monitor_graphs[ip] = {
                'figure': fig,
                'axis': ax,
                'line': line,
                'canvas': canvas,
                'times': [],
                'latencies': [],
                'status_line': None
            }
            
            # Status frame at bottom of device frame
            status_frame = ctk.CTkFrame(device_frame)
            status_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
            status_frame.grid_columnconfigure(0, weight=1)
            status_frame.grid_columnconfigure(1, weight=1)
            
            # Status label
            status_label = ctk.CTkLabel(
                status_frame,
                text="Status: Initializing...",
                font=ctk.CTkFont(size=10)
            )
            status_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
            
            # Stats label
            stats_label = ctk.CTkLabel(
                status_frame,
                text="Avg: --ms | Loss: --%",
                font=ctk.CTkFont(size=10)
            )
            stats_label.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky="w")
            
            self.monitor_graphs[ip]['status_label'] = status_label
            self.monitor_graphs[ip]['stats_label'] = stats_label
            
            # Store device information for alert context
            self.device_info[ip] = {
                'hostname': device.get('hostname', 'Unknown'),
                'manufacturer': device.get('manufacturer', 'Unknown'),
                'mac': device.get('mac', 'Unknown')
            }
            
            # Start monitoring if not already running
            if ip not in self.device_monitors:
                monitor = DeviceMonitor(ip, interval=1)
                monitor.start(
                    update_callback=self.update_graph_status,
                    graph_callback=self.update_monitor_graph
                )
                self.device_monitors[ip] = monitor
        
        # Initialize monitoring state
        self.monitor_paused = False
        
        # Control buttons
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

        # Create dedicated exit function for the exit button
        def exit_live_monitor():
            """Exit function specifically for the exit button - destroys the live monitor window"""
            print("Exit button clicked - closing live monitor window")
            for monitor in self.device_monitors.values():
                monitor.stop()
            self.device_monitors.clear()
            self.monitor_graphs.clear()
            if hasattr(self, 'monitor_tooltips'):
                self.monitor_tooltips.clear()
            if hasattr(self, 'current_monitor_window') and self.current_monitor_window:
                self.current_monitor_window = None
            plt.close('all')
            monitor_window.destroy()

        # Add exit button
        print("Creating exit button...")  # Debug line
        exit_btn = ctk.CTkButton(
            control_frame,
            text="Exit",
            command=exit_live_monitor,
            fg_color="#d32f2f",
            hover_color="#b71c1c"
        )
        exit_btn.pack(side="left", padx=10)
        print("Exit button created and packed")  # Debug line
        
        # Window state tracking
        self.is_maximized = False
        maximize_btn = ctk.CTkButton(
            control_frame,
            text="Maximize",
            command=lambda: self.toggle_maximize(monitor_window, maximize_btn)
        )
        maximize_btn.pack(side="right", padx=10)
        
        # Add minimize to tray button if tray is available
        if hasattr(self.parent_app, 'tray_manager') and self.parent_app.tray_manager:
            tray_btn = ctk.CTkButton(
                control_frame,
                text="Minimize to Tray",
                command=lambda: self.minimize_monitor_to_tray(monitor_window)
            )
            tray_btn.pack(side="right", padx=10)
        
        # Window close handler
        def on_close():
            # Check if we have a tray manager - if so, minimize to tray instead of closing
            if hasattr(self.parent_app, 'tray_manager') and self.parent_app.tray_manager:
                # Minimize to tray instead of destroying
                self.minimize_monitor_to_tray(monitor_window)
            else:
                # No tray manager, so actually close the window
                for monitor in self.device_monitors.values():
                    monitor.stop()
                self.device_monitors.clear()
                self.monitor_graphs.clear()
                if hasattr(self, 'current_monitor_window') and self.current_monitor_window:
                    self.current_monitor_window = None
                plt.close('all')
                monitor_window.destroy()
        
        monitor_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Bind window resize event to adjust graphs
        monitor_window.bind("<Configure>", lambda e: self.on_monitor_window_resize(e))
    
    def on_monitor_window_resize(self, event):
        """Handle monitor window resize to adjust graph sizes"""
        # Only process if it's the main window resize event
        if event.widget == self.current_monitor_window:
            # Debounce resize events
            if hasattr(self, '_resize_after_id'):
                self.current_monitor_window.after_cancel(self._resize_after_id)
            self._resize_after_id = self.current_monitor_window.after(300, self.resize_monitor_graphs)

    def resize_monitor_graphs(self):
        """Resize all monitor graphs to fit window"""
        if not hasattr(self, 'monitor_graphs') or not self.monitor_graphs:
            return
        
        try:
            for ip, graph_data in self.monitor_graphs.items():
                if 'canvas' in graph_data:
                    # Force canvas redraw
                    graph_data['canvas'].draw()
        except Exception as e:
            print(f"Error resizing graphs: {e}")

    def check_alert_thresholds(self, ip, latency, status):
        """Check if the latency or status exceeds thresholds and send an alert"""
        # Get device info for the alert
        device_info = self.device_info.get(ip, {
            'hostname': 'Unknown',
            'manufacturer': 'Unknown',
            'mac': 'Unknown'
        })
        
        # Use the email alert manager to check and send alerts
        email_alert_manager.check_and_send_alert(ip, latency, status, device_info)

    def update_graph_status(self, ip, latency, status, timestamp):
        """Update graph status labels"""
        # Check for alert thresholds
        self.check_alert_thresholds(ip, latency, status)
        
        def _update_on_main_thread():
            # Check if monitoring window still exists and has valid graphs
            if not hasattr(self, 'monitor_graphs') or ip not in self.monitor_graphs:
                return

            graph_data = self.monitor_graphs[ip]
            
            # Check if the widgets still exist before trying to update them
            try:
                if 'status_label' not in graph_data or not graph_data['status_label'].winfo_exists():
                    return
                if 'stats_label' not in graph_data or not graph_data['stats_label'].winfo_exists():
                    return
            except:
                return  # Widget was destroyed

            # Update status
            try:
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
            except Exception:
                return  # Widget was destroyed

        # Schedule GUI update on main thread
        if hasattr(self.parent_app, 'root') and self.parent_app.root.winfo_exists():
            self.parent_app.root.after(0, _update_on_main_thread)

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
                try:
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
                except Exception:
                    # Canvas or other widget was destroyed
                    return

        # Schedule GUI update on main thread
        if hasattr(self.parent_app, 'root') and self.parent_app.root.winfo_exists():
            self.parent_app.root.after(0, _update_graph_on_main_thread)

    def toggle_monitoring_pause(self, button):
        """Toggle monitoring pause state"""
        self.monitor_paused = not self.monitor_paused

        if self.monitor_paused:
            button.configure(text="Resume Monitoring")
        else:
            button.configure(text="Pause Monitoring")
    
    def show_monitor_tooltip(self, ip):
        """Show tooltip with latency info on hover"""
        if ip not in self.monitor_tooltips or ip not in self.device_monitors:
            return
        
        monitor = self.device_monitors[ip]
        if not monitor.buffer:
            return
        
        # Get latest data
        latest_data = monitor.buffer[-1]
        _, latency, status = latest_data
        
        # Get statistics
        valid_latencies = [lat for _, lat, stat in monitor.buffer if stat == 'up' and not math.isnan(lat)]

        if valid_latencies:
            avg_latency = sum(valid_latencies) / len(valid_latencies)
            text = f"Latest: {latency:.1f}ms\nAvg: {avg_latency:.1f}ms\nStatus: {status.capitalize()}"
        else:
            text = f"Status: {status.capitalize()}"
        
        tooltip = self.monitor_tooltips[ip]
        tooltip.configure(text=text)
        tooltip.lift()
    
    def hide_monitor_tooltip(self, ip):
        """Hide tooltip when mouse leaves"""
        if ip in self.monitor_tooltips:
            self.monitor_tooltips[ip].place_forget()
    
    def update_tooltip_position(self, event, ip):
        """Update tooltip position to follow mouse"""
        if ip not in self.monitor_tooltips:
            return
        
        tooltip = self.monitor_tooltips[ip]
        # Position tooltip near mouse with offset
        x = event.x_root - tooltip.winfo_toplevel().winfo_rootx() + 10
        y = event.y_root - tooltip.winfo_toplevel().winfo_rooty() - 30
        tooltip.place(x=x, y=y)
    
    def minimize_monitor_to_tray(self, monitor_window):
        """Minimize live monitor window to system tray"""
        if hasattr(self.parent_app, 'tray_manager') and self.parent_app.tray_manager:
            # Hide the monitor window
            monitor_window.withdraw()
            
            # Store reference to restore later
            self.minimized_monitor_window = monitor_window
            
            # Update the tray menu to show the restore option
            if hasattr(self.parent_app.tray_manager, 'update_menu'):
                self.parent_app.tray_manager.update_menu()
            
            # Update tray tooltip
            if hasattr(self.parent_app.tray_manager, 'update_tooltip'):
                device_count = len(self.device_info)
                self.parent_app.tray_manager.update_tooltip(f"I.T Assistant - Monitoring {device_count} devices")
            
            # Show notification
            try:
                if hasattr(self.parent_app.tray_manager.icon, 'notify'):
                    self.parent_app.tray_manager.icon.notify(
                        "Live Monitor minimized to tray",
                        f"Monitoring {len(self.device_info)} devices in background"
                    )
            except:
                pass
        else:
            # No tray available, just minimize normally
            monitor_window.iconify()

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
            # Ensure main frame fills available space but preserve control frame fixed height
            if self.is_maximized and hasattr(self, 'current_monitor_window') and self.current_monitor_window:
                for child in self.current_monitor_window.winfo_children():
                    try:
                        # Only expand the main frame, not the control frame
                        if hasattr(child, 'pack_info'):
                            pack_info = child.pack_info()
                            if pack_info.get('side') == 'bottom':
                                # This is the control frame - keep it fixed height
                                child.pack_configure(fill="x", expand=False)
                            else:
                                # This is the main frame - allow it to expand
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
                            # Only expand the main frame, not the control frame
                            if hasattr(child, 'pack_info'):
                                pack_info = child.pack_info()
                                if pack_info.get('side') == 'bottom':
                                    # This is the control frame - keep it fixed height
                                    child.pack_configure(fill="x", expand=False)
                                else:
                                    # This is the main frame - allow it to expand
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

    def run_speed_test(self):
        """Run internet speed test"""
        if not SPEEDTEST_AVAILABLE:
            messagebox.showerror("Speed Test", "speedtest-cli not available")
            return

        # Create speed test window
        speed_window = ctk.CTkToplevel(self.parent_app.root)
        speed_window.title("Internet Speed Test")
        speed_window.geometry("450x350")
        speed_window.transient(self.parent_app.root)
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
