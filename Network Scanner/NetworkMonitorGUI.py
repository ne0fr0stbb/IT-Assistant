import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QHBoxLayout, QProgressBar, QHeaderView, QDialog, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from scanthread import ScanThread
from utils import get_default_gateway
import webbrowser
import subprocess

class NmapThread(QThread):
    result_ready = pyqtSignal(str)
    def __init__(self, ip, args):
        super().__init__()
        self.ip = ip
        self.args = args
    def run(self):
        import subprocess
        try:
            result = subprocess.run(['nmap'] + self.args + [self.ip], capture_output=True, text=True, timeout=60)
            output = result.stdout or result.stderr
        except Exception as e:
            output = f'Error running nmap: {e}'
        self.result_ready.emit(output)

class NmapDialog(QDialog):
    def __init__(self, ip, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Nmap Options for {ip}')
        self.ip = ip
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.info_label = QLabel(f'Select an Nmap scan to run on {ip}:')
        layout.addWidget(self.info_label)
        btn_layout = QHBoxLayout()
        self.quick_btn = QPushButton('Quick Scan (-F)')
        self.os_btn = QPushButton('OS Detection (-O)')
        self.ports_btn = QPushButton('Port Scan (-p 1-10000)')
        self.sv_btn = QPushButton('Service Version (-sV)')
        self.top_ports_btn = QPushButton('Top 100 Ports (--top-ports 100)')
        self.firewall_btn = QPushButton('Firewall Evasion (-f)')
        self.traceroute_btn = QPushButton('Traceroute (--traceroute)')
        btn_layout.addWidget(self.quick_btn)
        btn_layout.addWidget(self.os_btn)
        btn_layout.addWidget(self.ports_btn)
        btn_layout.addWidget(self.sv_btn)
        btn_layout.addWidget(self.top_ports_btn)
        btn_layout.addWidget(self.firewall_btn)
        btn_layout.addWidget(self.traceroute_btn)
        layout.addLayout(btn_layout)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        self.setLayout(layout)
        self.quick_btn.clicked.connect(self.run_quick)
        self.os_btn.clicked.connect(self.run_os)
        self.ports_btn.clicked.connect(self.run_ports)
        self.sv_btn.clicked.connect(self.run_sv)
        self.top_ports_btn.clicked.connect(self.run_top_ports)
        self.firewall_btn.clicked.connect(self.run_firewall)
        self.traceroute_btn.clicked.connect(self.run_traceroute)
        self.nmap_thread = None

    def run_nmap(self, args):
        self.result_text.setText('Scanning...')
        if self.nmap_thread and self.nmap_thread.isRunning():
            return
        self.nmap_thread = NmapThread(self.ip, args)
        self.nmap_thread.result_ready.connect(self.display_result)
        self.nmap_thread.start()

    def display_result(self, output):
        self.result_text.setText(output)

    def run_quick(self):
        self.run_nmap(['-F'])

    def run_os(self):
        self.run_nmap(['-O'])

    def run_ports(self):
        self.run_nmap(['-p', '1-10000'])

    def run_sv(self):
        self.run_nmap(['-sV'])

    def run_top_ports(self):
        self.run_nmap(['--top-ports', '100'])

    def run_firewall(self):
        self.run_nmap(['-f'])

    def run_traceroute(self):
        self.run_nmap(['--traceroute'])

class NetworkMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Network Scanner')
        self.setGeometry(300, 300, 1100, 500)

        # Widgets
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(['IP Address', 'MAC Address', 'Hostname', 'Manufacturer', 'Response Time (ms)', 'Web Service'])
        self.table_widget.cellClicked.connect(self.handle_cell_click)
        self.table_widget.cellDoubleClicked.connect(self.handle_cell_double_click)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setSortingEnabled(True)

        self.scan_button = QPushButton('Scan')
        self.scan_button.clicked.connect(self.load_data)
        
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText('Enter IP range (e.g., 192.168.1.0/24)')
        
        self.info_label = QLabel('Enter IP range or leave blank for default gateway')
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.summary_label = QLabel('Devices found: 0 | Problematic (>500ms): 0')
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search IP or MAC...')
        self.search_input.textChanged.connect(self.filter_table)

        # Layouts
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.scan_button)
        input_layout.addWidget(self.ip_input)
        input_layout.addWidget(self.search_input)

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addLayout(input_layout)
        layout.addWidget(self.table_widget)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.all_devices = []  # Store all scan results for filtering

    def load_data(self):
        print("Checking IP range input...")
        ip_range = self.ip_input.text().strip()
        if not ip_range:
            default_gateway = get_default_gateway()
            if not default_gateway:
                self.info_label.setText('Gateway not found. Please enter IP range.')
                return
            ip_range = f"{default_gateway}/23"
        self.scan_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.info_label.setText('Scanning...')
        self.table_widget.setRowCount(0)  # Clear table before scan
        self.device_rows = 0
        self.thread = ScanThread(ip_range)
        self.thread.result_ready.connect(self.display_results)
        self.thread.progress.connect(self.update_progress)
        self.thread.device_found.connect(self.add_device_row)
        self.thread.finished.connect(lambda: self.scan_button.setEnabled(True))
        print("Starting scan thread...")
        self.thread.start()

    def update_progress(self, value):
        print(f"Updating progress: {value}%")
        self.progress_bar.setValue(value)

    def add_device_row(self, device):
        row = self.device_rows
        self.table_widget.insertRow(row)
        self.table_widget.setItem(row, 0, QTableWidgetItem(device['ip']))
        self.table_widget.setItem(row, 1, QTableWidgetItem(device['mac']))
        self.table_widget.setItem(row, 2, QTableWidgetItem(device.get('hostname') or ''))
        self.table_widget.setItem(row, 3, QTableWidgetItem(device.get('manufacturer') or ''))
        # Convert response time to milliseconds
        response_ms = device['response_time'] * 1000
        response_item = QTableWidgetItem(f"{response_ms:.2f}")
        if response_ms > 500:
            response_item.setForeground(Qt.red)
        self.table_widget.setItem(row, 4, response_item)
        if device.get('web_service'):
            item = QTableWidgetItem(device['web_service'])
            item.setForeground(Qt.blue)
            item.setToolTip('Click to open')
            item.setData(Qt.UserRole, device['web_service'])
        else:
            item = QTableWidgetItem('None')
        self.table_widget.setItem(row, 5, item)
        self.device_rows += 1
        # Count problematic devices
        problematic = 0
        for i in range(self.device_rows):
            try:
                val = float(self.table_widget.item(i, 4).text())
                if val > 500:
                    problematic += 1
            except Exception:
                continue
        self.summary_label.setText(f"Devices found: {self.device_rows} | Problematic (>500ms): {problematic}")

    def handle_cell_click(self, row, column):
        if column == 5:
            item = self.table_widget.item(row, column)
            url = item.data(Qt.UserRole)
            if url:
                webbrowser.open(url)

    def handle_cell_double_click(self, row, column):
        if column == 0:  # IP Address column
            ip = self.table_widget.item(row, 0).text()
            dlg = NmapDialog(ip, self)
            dlg.exec_()

    def display_results(self, devices):
        print("Scan complete. Displaying results...")
        self.progress_bar.setValue(100)
        self.info_label.setText('Scan complete.')
        # Sort devices by response_time descending
        devices_sorted = sorted(devices, key=lambda d: d['response_time'], reverse=True)
        self.table_widget.setRowCount(0)
        self.device_rows = 0
        for device in devices_sorted:
            self.add_device_row(device)
        # Save all devices for filtering
        self.all_devices = devices_sorted
        # Final problematic count
        problematic = sum(1 for d in devices_sorted if d['response_time'] * 1000 > 500)
        self.summary_label.setText(f"Devices found: {len(devices_sorted)} | Problematic (>500ms): {problematic}")

    def filter_table(self):
        query = self.search_input.text().strip().lower()
        self.table_widget.setRowCount(0)
        self.device_rows = 0
        for device in self.all_devices:
            if (query in device['ip'].lower()) or (query in device['mac'].lower()) or (query in (device.get('hostname') or '').lower()):
                self.add_device_row(device)
        # Update summary for filtered view
        problematic = 0
        for i in range(self.device_rows):
            try:
                val = float(self.table_widget.item(i, 4).text())
                if val > 500:
                    problematic += 1
            except Exception:
                continue
        self.summary_label.setText(f"Devices found: {self.device_rows} | Problematic (>500ms): {problematic}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkMonitor()
    window.show()
    sys.exit(app.exec_())
