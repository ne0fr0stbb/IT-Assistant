from PyQt5.QtCore import QThread, pyqtSignal
from scapy.layers.l2 import ARP, Ether, srp
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from manuf import manuf

class ScanThread(QThread):
    result_ready = pyqtSignal(list)
    progress = pyqtSignal(int)
    device_found = pyqtSignal(dict)
    def __init__(self, ip_range):
        super().__init__()
        self.ip_range = ip_range
        self.mac_parser = manuf.MacParser()
    def check_web_port(self, ip):
        ports = [(80, 'http'), (443, 'https')]
        for port, scheme in ports:
            try:
                with socket.create_connection((str(ip), port), timeout=0.5):
                    return f"{scheme}://{ip}:{port}"
            except Exception:
                continue
        return None
    def get_hostname(self, ip):
        import socket
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return None
    def get_manufacturer(self, mac):
        return self.mac_parser.get_manuf(mac) or None
    def arp_scan_ip(self, ip):
        arp = ARP(pdst=str(ip))
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        start_time = time.time()
        result = srp(packet, timeout=0.5, verbose=0)[0]
        end_time = time.time()
        devices = []
        for _, received in result:
            ip_addr = received.psrc
            mac = received.hwsrc
            response_time = end_time - start_time
            web_service = self.check_web_port(ip_addr)
            hostname = self.get_hostname(ip_addr)
            manufacturer = self.get_manufacturer(mac)
            devices.append({'ip': ip_addr, 'mac': mac, 'response_time': response_time, 'web_service': web_service, 'hostname': hostname, 'manufacturer': manufacturer})
        return devices
    def run(self):
        import ipaddress
        devices = []
        try:
            network = ipaddress.ip_network(self.ip_range, strict=False)
        except ValueError:
            self.result_ready.emit(devices)
            return
        hosts = list(network.hosts())
        total = len(hosts)
        completed = 0
        try:
            with ThreadPoolExecutor(max_workers=32) as executor:
                future_to_ip = {executor.submit(self.arp_scan_ip, ip): ip for ip in hosts}
                for future in as_completed(future_to_ip):
                    try:
                        result_devices = future.result()
                        for device in result_devices:
                            devices.append(device)
                            self.device_found.emit(device)
                    except Exception as e:
                        print(f"Error in thread: {e}")
                    completed += 1
                    percent = int((completed) / total * 100)
                    self.progress.emit(percent)
        except Exception as e:
            print(f"ThreadPoolExecutor error: {e}")
        self.result_ready.emit(devices)
