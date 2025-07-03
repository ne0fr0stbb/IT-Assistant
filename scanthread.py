# This module implements threaded network scanning functionality for the NetworkMonitor GUI.
# It performs ARP scanning with enhanced device discovery including hostname, manufacturer, and web services.
from PyQt5.QtCore import QThread, pyqtSignal
from scapy.layers.l2 import ARP, Ether, srp
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from manuf import manuf

class ScanThread(QThread):
    """
    QThread subclass that performs network scanning in a separate thread.
    Emits signals to update the GUI with progress and discovered devices.
    """
    # Signal definitions for communication with the main GUI thread
    result_ready = pyqtSignal(list)  # Emitted when scan is complete with all devices
    progress = pyqtSignal(int)       # Emitted to update progress bar (0-100%)
    device_found = pyqtSignal(dict)  # Emitted when each individual device is found

    def __init__(self, ip_range):
        super().__init__()
        self.ip_range = ip_range
        # Initialize MAC address parser for manufacturer lookup
        self.mac_parser = manuf.MacParser()

    def check_web_port(self, ip):
        """
        Check if a device has web services running on common HTTP/HTTPS ports.

        Args:
            ip: IP address to check

        Returns:
            URL string if web service found, None otherwise
        """
        ports = [(80, 'http'), (443, 'https')]
        for port, scheme in ports:
            try:
                # Attempt to connect to web port with short timeout
                with socket.create_connection((str(ip), port), timeout=0.5):
                    return f"{scheme}://{ip}:{port}"
            except Exception:
                continue
        return None

    def get_hostname(self, ip):
        """
        Perform reverse DNS lookup to get hostname for an IP address.

        Args:
            ip: IP address to lookup

        Returns:
            Hostname string if found, None otherwise
        """
        import socket
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return None

    def get_manufacturer(self, mac):
        """
        Get manufacturer name from MAC address using OUI database.

        Args:
            mac: MAC address string

        Returns:
            Manufacturer name if found, None otherwise
        """
        return self.mac_parser.get_manuf(mac) or None

    def arp_scan_ip(self, ip):
        """
        Perform ARP scan on a single IP address and gather device information.

        Args:
            ip: IP address to scan

        Returns:
            List of device dictionaries (usually 0 or 1 device)
        """
        # Create ARP request packet for specific IP
        arp = ARP(pdst=str(ip))
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")  # Broadcast ethernet frame
        packet = ether / arp

        # Time the ARP request for response time measurement
        start_time = time.time()
        result = srp(packet, timeout=0.5, verbose=0)[0]  # Short timeout for individual IP
        end_time = time.time()

        devices = []
        for _, received in result:
            # Extract basic network information
            ip_addr = received.psrc
            mac = received.hwsrc
            response_time = end_time - start_time

            # Gather additional device information
            web_service = self.check_web_port(ip_addr)
            hostname = self.get_hostname(ip_addr)
            manufacturer = self.get_manufacturer(mac)

            # Create device dictionary with all gathered information
            devices.append({
                'ip': ip_addr,
                'mac': mac,
                'response_time': response_time,
                'web_service': web_service,
                'hostname': hostname,
                'manufacturer': manufacturer
            })
        return devices

    def run(self):
        """
        Main thread execution method. Scans the IP range using multiple threads
        and emits progress updates and device discoveries to the GUI.
        """
        import ipaddress
        devices = []

        # Parse the IP range into individual host addresses
        try:
            network = ipaddress.ip_network(self.ip_range, strict=False)
        except ValueError:
            # Invalid IP range, return empty results
            self.result_ready.emit(devices)
            return

        # Get list of all host IPs in the network (excluding network/broadcast)
        hosts = list(network.hosts())
        total = len(hosts)
        completed = 0

        try:
            # Use ThreadPoolExecutor for concurrent scanning of multiple IPs
            with ThreadPoolExecutor(max_workers=32) as executor:
                # Submit all IP scanning tasks to the thread pool
                future_to_ip = {executor.submit(self.arp_scan_ip, ip): ip for ip in hosts}

                # Process completed scanning tasks as they finish
                for future in as_completed(future_to_ip):
                    try:
                        result_devices = future.result()
                        for device in result_devices:
                            devices.append(device)
                            # Emit signal for each discovered device (real-time updates)
                            self.device_found.emit(device)
                    except Exception as e:
                        print(f"Error in thread: {e}")

                    # Update progress bar based on completed scans
                    completed += 1
                    percent = int((completed) / total * 100)
                    self.progress.emit(percent)

        except Exception as e:
            print(f"ThreadPoolExecutor error: {e}")

        # Emit final results when all scanning is complete
        self.result_ready.emit(devices)
