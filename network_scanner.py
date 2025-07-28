#!/usr/bin/env python3
"""
Network Scanner Module
Contains the NetworkScanner class for network device discovery
"""

import socket
import subprocess
import platform
import time
import ipaddress
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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
                with socket.create_connection((str(ip), port), timeout=0.3):  # Reduced timeout
                    return f"{scheme}://{ip}:{port if port != 80 and port != 443 else ''}"
            except:
                continue
        return None
    
    def get_hostname(self, ip):
        """Get hostname for IP with timeout"""
        try:
            # Set a shorter timeout for hostname resolution
            socket.setdefaulttimeout(1.0)  # Reduced to 1 second timeout
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
            # Increase thread pool size for faster scanning
            with ThreadPoolExecutor(max_workers=64) as executor:
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
