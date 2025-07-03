# This module provides live device monitoring functionality for the NetworkMonitor application.
# It defines DeviceMonitor for pinging devices and LiveMonitorManager for managing multiple monitors.
import time
import threading
from collections import deque
import platform
import subprocess
from PyQt5.QtCore import QObject, pyqtSignal

class DeviceMonitor(QObject):
    update_signal = pyqtSignal(str, float, str, float)  # ip, latency, status, timestamp

    def __init__(self, ip, interval=2, buffer_size=100):
        super().__init__()
        self.ip = ip  # IP address to monitor
        self.interval = interval  # Ping interval in seconds
        self.buffer = deque(maxlen=buffer_size)  # Stores (timestamp, latency, status)
        self._running = False
        self.thread = None

    def start(self):
        # Start the monitoring thread
        if not self._running:
            self._running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        # Stop the monitoring thread
        self._running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _monitor_loop(self):
        # Main loop for pinging the device and emitting updates
        while self._running:
            latency, status = self.ping_device()
            ts = time.time()
            self.buffer.append((ts, latency, status))
            self.update_signal.emit(self.ip, latency, status, ts)
            time.sleep(self.interval)

    def ping_device(self):
        # Cross-platform ping implementation
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        try:
            output = subprocess.check_output([
                'ping', param, '1', '-w', '1000', self.ip
            ], stderr=subprocess.STDOUT, universal_newlines=True)
            if 'unreachable' in output.lower() or 'timed out' in output.lower():
                return float('nan'), 'down'
            # Parse latency from ping output
            if platform.system().lower() == 'windows':
                import re
                # Look for time=XXXms or time<Xms patterns in Windows ping output
                match = re.search(r'time[<=](\d+(?:\.\d+)?)ms', output)
                if match:
                    latency = float(match.group(1))
                    return latency, 'up'
                # Also check for time<1ms case
                if 'time<1ms' in output.lower():
                    return 0.5, 'up'  # Estimate sub-millisecond as 0.5ms
            else:
                import re
                # Linux/Mac ping output format
                match = re.search(r'time=(\d+\.?\d*) ms', output)
                if match:
                    latency = float(match.group(1))
                    return latency, 'up'
            return float('nan'), 'down'
        except Exception:
            return float('nan'), 'down'

class LiveMonitorManager(QObject):
    device_update = pyqtSignal(str, float, str, float)  # ip, latency, status, timestamp

    def __init__(self):
        super().__init__()
        self.monitors = {}  # Maps IP addresses to DeviceMonitor instances

    def start_monitoring(self, ip):
        # Start monitoring a device by IP address
        if ip not in self.monitors:
            monitor = DeviceMonitor(ip)
            monitor.update_signal.connect(self.device_update.emit)
            self.monitors[ip] = monitor
            monitor.start()

    def stop_monitoring(self, ip):
        # Stop monitoring a device by IP address
        if ip in self.monitors:
            self.monitors[ip].stop()
            del self.monitors[ip]

    def stop_all(self):
        # Stop monitoring all devices
        for ip in list(self.monitors.keys()):
            self.stop_monitoring(ip)

    def get_buffer(self, ip):
        # Get the monitoring buffer for a device
        if ip in self.monitors:
            return list(self.monitors[ip].buffer)
        return []
