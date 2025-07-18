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
        self.monitor_paused = False
        self.is_maximized = False
        self.current_monitor_window = None

    def open_live_monitor(self, selected_devices):
        """Open live monitoring dialog with graphs"""
        if not selected_devices:
            messagebox.showwarning("No Devices", "Please select at least one device to monitor.")
            return

        monitor_window = ctk.CTk()
        monitor_window.title("Live Device Monitoring - Real-time Graphs")

        device_count = len(selected_devices)
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
        self.device_info = {}  # Store device information for alerts

        for i, device in enumerate(selected_devices):
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
            
            # Store device information for alert context
            self.device_info[ip] = {
                'hostname': device.get('hostname', 'Unknown'),
                'manufacturer': device.get('manufacturer', 'Unknown'),
                'mac': device.get('mac', 'Unknown')
            }
            
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
            if hasattr(self, 'current_monitor_window') and self.current_monitor_window:
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
        if hasattr(self.parent_app, 'root'):
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
        if hasattr(self.parent_app, 'root'):
            self.parent_app.root.after(0, _update_graph_on_main_thread)

    def toggle_monitoring_pause(self, button):
        """Toggle monitoring pause state"""
        self.monitor_paused = not self.monitor_paused

        if self.monitor_paused:
            button.configure(text="Resume Monitoring")
        else:
            button.configure(text="Pause Monitoring")

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
