# This file implements the main GUI for the NetworkMonitor application.
# It provides device scanning, filtering, and live monitoring features using PyQt5.
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QHBoxLayout, QProgressBar, QHeaderView, QDialog, QTextEdit, QCheckBox, QDialogButtonBox, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from scanthread import ScanThread
from utils import get_default_gateway
import webbrowser
from livemonitor import LiveMonitorManager
import pyqtgraph as pg
import csv
from speedtest_dialog import SpeedTestDialog

class NmapThread(QThread):
    # Thread for running nmap scans asynchronously
    result_ready = pyqtSignal(str)
    def __init__(self, ip, args):
        super().__init__()
        self.ip = ip
        self.args = args
    def run(self):
        # Run nmap and emit the result
        import subprocess
        try:
            result = subprocess.run(['nmap'] + self.args + [self.ip], capture_output=True, text=True, timeout=60)
            output = result.stdout or result.stderr
        except Exception as e:
            output = f'Error running nmap: {e}'
        self.result_ready.emit(output)

class NmapDialog(QDialog):
    # Dialog for selecting and running nmap scans on a device
    def __init__(self, ip, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Nmap Options for {ip}')
        self.ip = ip
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.info_label = QLabel(f'Select an Nmap scan to run on {ip}:')
        self.info_label.setStyleSheet('font-size: 16px; font-weight: bold;')  # Larger font for info label
        layout.addWidget(self.info_label)
        btn_layout = QHBoxLayout()

        # Create buttons with larger font sizes
        self.quick_btn = QPushButton('Quick Scan (-F)')
        self.quick_btn.setStyleSheet('font-size: 14px; padding: 8px;')
        self.os_btn = QPushButton('OS Detection (-O)')
        self.os_btn.setStyleSheet('font-size: 14px; padding: 8px;')
        self.ports_btn = QPushButton('Port Scan (-p 1-10000)')
        self.ports_btn.setStyleSheet('font-size: 14px; padding: 8px;')
        self.sv_btn = QPushButton('Service Version (-sV)')
        self.sv_btn.setStyleSheet('font-size: 14px; padding: 8px;')
        self.top_ports_btn = QPushButton('Top 100 Ports (--top-ports 100)')
        self.top_ports_btn.setStyleSheet('font-size: 14px; padding: 8px;')
        self.firewall_btn = QPushButton('Firewall Evasion (-f)')
        self.firewall_btn.setStyleSheet('font-size: 14px; padding: 8px;')
        self.traceroute_btn = QPushButton('Traceroute (--traceroute)')
        self.traceroute_btn.setStyleSheet('font-size: 14px; padding: 8px;')

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
        self.result_text.setStyleSheet('font-size: 12px; font-family: "Consolas", "Courier New", monospace;')  # Larger font for results
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

class LiveMonitorDialog(QDialog):
    # Dialog for displaying live monitoring graphs and statuses for selected devices
    def __init__(self, parent, devices):
        super().__init__(parent)
        self.setWindowTitle('Live Device Monitoring')
        self.resize(900, 600)
        self.manager = LiveMonitorManager()
        self.manager.device_update.connect(self.update_graph)
        self.selected_ips = [d['ip'] for d in devices]
        layout = QVBoxLayout()
        self.graphs = {}  # Maps IP to plot widget
        self.status_labels = {}  # Maps IP to status label
        for device in devices:
            ip = device['ip']
            group = QWidget()
            group_layout = QHBoxLayout()
            label = QLabel(f"{ip}")
            label.setStyleSheet('font-size: 18px;')  # Larger font for IP
            status = QLabel('Status: Unknown')
            status.setStyleSheet('font-size: 16px;')  # Larger font for status
            self.status_labels[ip] = status
            plot = pg.PlotWidget()
            plot.setYRange(0, 2000)
            plot.setLabel('left', 'Latency (ms)')
            plot.setLabel('bottom', 'Time (s)')
            plot.showGrid(x=True, y=True)
            self.graphs[ip] = plot
            group_layout.addWidget(label)
            group_layout.addWidget(status)
            group_layout.addWidget(plot)
            group.setLayout(group_layout)
            layout.addWidget(group)
            self.manager.start_monitoring(ip)
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.setStyleSheet('font-size: 16px;')  # Larger font for button
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)
        self.setLayout(layout)

    def update_graph(self, ip, latency, status, ts):
        if ip in self.graphs:
            buf = self.manager.get_buffer(ip)
            times = [t - buf[0][0] for t, _, _ in buf]
            lats = [l for _, l, _ in buf]
            self.graphs[ip].clear()
            self.graphs[ip].plot(times, lats, pen=pg.mkPen('b', width=2))
            self.status_labels[ip].setText(f'Status: {status} | Last: {latency:.2f} ms')

    def closeEvent(self, event):
        self.manager.stop_all()
        event.accept()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About I.T Assistant")
        self.setFixedSize(420, 320)
        layout = QVBoxLayout()
        app_name = QLabel("<b>I.T Assistant v1.0</b>")
        app_name.setStyleSheet("font-size: 20px;")
        desc = QLabel("A modern network scanner and live device monitor.<br>"
                      "Features: device discovery, latency/uptime monitoring, speed test, and more.")
        desc.setWordWrap(True)
        author = QLabel("Author: Jason Burnham (<a href='mailto:jason.o.burnham@gmail.com'>Contact</a>)")
        author.setOpenExternalLinks(True)
        license_ = QLabel("License: MIT")
        repo = QLabel("<a href='https://github.com/ne0fr0stbb/IT-Assistant'>Project Repository</a>")
        repo.setOpenExternalLinks(True)
        copyright_ = QLabel("2025 Jason Burnham")
        copyright_.setStyleSheet("color: #888; font-size: 11px;")
        ack = QLabel("Built with PyQt5, pyqtgraph, pysnmp, speedtest-cli")
        ack.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(app_name)
        layout.addWidget(desc)
        layout.addSpacing(10)
        layout.addWidget(author)
        layout.addWidget(license_)
        layout.addWidget(repo)
        layout.addSpacing(10)
        layout.addWidget(ack)
        layout.addStretch()
        layout.addWidget(copyright_)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)
        self.setLayout(layout)

class NetworkMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('I.T Assistant - Network Monitor')
        self.setGeometry(300, 300, 1100, 500)

        # Initialize theme state (default to light theme)
        self.dark_theme = False

        # Widgets
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(['IP Address', 'MAC Address', 'Hostname', 'Manufacturer', 'Response Time (ms)', 'Web Service', 'Live Monitoring'])
        self.table_widget.cellClicked.connect(self.handle_cell_click)
        self.table_widget.cellDoubleClicked.connect(self.handle_cell_double_click)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setSortingEnabled(True)

        # Hide row numbers (vertical header)
        self.table_widget.verticalHeader().setVisible(False)

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

        # Add live monitoring and internet speed test buttons to the input layout
        self.speedtest_btn = QPushButton('Internet Speed Test')
        self.speedtest_btn.clicked.connect(self.open_speedtest_dialog)
        input_layout.addWidget(self.speedtest_btn)

        self.live_monitor_btn = QPushButton('Live Monitoring')
        self.live_monitor_btn.clicked.connect(self.open_live_monitor)
        input_layout.addWidget(self.live_monitor_btn)

        # Create menu bar
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu('File')
        open_action = file_menu.addAction('Open')
        open_action.triggered.connect(self.open_file)
        save_action = file_menu.addAction('Save')
        save_action.triggered.connect(self.save_report)
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)

        # Options menu
        options_menu = menu_bar.addMenu('Options')
        theme_action = options_menu.addAction('Toggle Theme')
        theme_action.triggered.connect(self.toggle_theme)

        # About menu (placeholder for now)
        about_menu = menu_bar.addMenu('About')
        about_action = about_menu.addAction('About Network Monitor')
        about_action.triggered.connect(self.show_about_dialog)

        # Initialize checkboxes attribute
        self.checkboxes = []

        # Apply the theme immediately after initializing the UI
        self.apply_theme()

    def open_speedtest_dialog(self):

        dlg = SpeedTestDialog(self)
        dlg.exec_()

    def save_report(self):
        # Logic to save the scanned devices report as a CSV file
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save Report', '', 'CSV Files (*.csv);;All Files (*)')
        if file_path:
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                # Write header row
                headers = [self.table_widget.horizontalHeaderItem(i).text() for i in range(self.table_widget.columnCount())]
                writer.writerow(headers)
                # Write data rows
                for row in range(self.table_widget.rowCount()):
                    row_data = []
                    for column in range(self.table_widget.columnCount()):
                        item = self.table_widget.item(row, column)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)

    def open_file(self):
        # Logic to open a CSV file and populate the table
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'CSV Files (*.csv);;All Files (*)')
        if file_path:
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                headers = next(reader, None)  # Read the header row
                self.table_widget.setRowCount(0)  # Clear existing rows
                self.table_widget.setColumnCount(len(headers))
                self.table_widget.setHorizontalHeaderLabels(headers)
                for row_data in reader:
                    row = self.table_widget.rowCount()
                    self.table_widget.insertRow(row)
                    for column, data in enumerate(row_data):
                        self.table_widget.setItem(row, column, QTableWidgetItem(data))

    def load_data(self):
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
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def add_device_row(self, device):
        row = self.device_rows
        self.table_widget.insertRow(row)

        # Create and center align all items
        ip_item = QTableWidgetItem(device['ip'])
        ip_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(row, 0, ip_item)

        mac_item = QTableWidgetItem(device['mac'])
        mac_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(row, 1, mac_item)

        hostname_item = QTableWidgetItem(device.get('hostname') or '')
        hostname_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(row, 2, hostname_item)

        manufacturer_item = QTableWidgetItem(device.get('manufacturer') or '')
        manufacturer_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(row, 3, manufacturer_item)

        # Convert response time to milliseconds with 0 decimal places
        response_ms = device['response_time'] * 1000
        response_item = QTableWidgetItem(f"{response_ms:.0f}")
        response_item.setTextAlignment(Qt.AlignCenter)
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
        item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(row, 5, item)

        # Don't add checkbox here - it will be added by add_checkboxes method
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
        self.add_checkboxes()
        # Final problematic count
        problematic = sum(1 for d in devices_sorted if d['response_time'] * 1000 > 500)
        self.summary_label.setText(f"Devices found: {len(devices_sorted)} | Problematic (>500ms): {problematic}")

    def add_checkboxes(self):
        # Remove old checkboxes from the live monitoring column (index 6)
        for cb in self.checkboxes:
            self.table_widget.setCellWidget(cb[0], 6, None)
        self.checkboxes = []
        for row in range(self.table_widget.rowCount()):
            cb = QCheckBox()
            # Center the checkbox in the cell
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(cb)
            layout.setAlignment(cb, Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            cell_widget.setLayout(layout)
            self.table_widget.setCellWidget(row, 6, cell_widget)
            self.checkboxes.append((row, cb))

    def get_selected_devices(self):
        selected = []
        for row in range(self.table_widget.rowCount()):
            cell_widget = self.table_widget.cellWidget(row, 6)
            if cell_widget is not None:
                cb = cell_widget.findChild(QCheckBox)
                if cb and cb.isChecked():
                    ip = self.table_widget.item(row, 0).text()
                    for d in self.all_devices:
                        if d['ip'] == ip:
                            selected.append(d)
                            break
        return selected

    def open_live_monitor(self):
        selected = self.get_selected_devices()
        if not selected:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, 'No Devices Selected', 'Please select at least one device to monitor.')
            return
        dlg = LiveMonitorDialog(self, selected)
        dlg.exec_()

    def filter_table(self):
        query = self.search_input.text().strip().lower()
        self.table_widget.setRowCount(0)
        self.device_rows = 0
        for device in self.all_devices:
            if (query in device['ip'].lower()) or (query in device['mac'].lower()) or (query in (device.get('hostname') or '').lower()):
                self.add_device_row(device)
        # Add checkboxes after filtering
        self.add_checkboxes()
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

    def toggle_theme(self):
        # Toggle the theme state
        self.dark_theme = not self.dark_theme
        # Apply the theme
        self.apply_theme()

    def apply_theme(self):
        if self.dark_theme:
            # Modern Dark Theme - Material Design inspired
            bg_color = '#1e1e1e'
            surface_color = '#2d2d30'
            text_color = '#ffffff'
            text_secondary = '#b3b3b3'
            header_color = '#3c3c3c'
            button_color = '#0d7377'
            button_hover = '#14a085'
            button_text_color = '#ffffff'
            accent_color = '#00d4aa'
            link_color = '#4fc3f7'
            border_color = '#404040'
            input_bg = '#383838'
        else:
            # Modern Light Theme - Clean and minimal
            bg_color = '#fafafa'
            surface_color = '#ffffff'
            text_color = '#212121'
            text_secondary = '#757575'
            header_color = '#f5f5f5'
            button_color = '#1976d2'
            button_hover = '#1565c0'
            button_text_color = '#ffffff'
            accent_color = '#2196f3'
            link_color = '#1976d2'
            border_color = '#e0e0e0'
            input_bg = '#ffffff'

        # Apply modern styling to all widgets
        self.setStyleSheet(f"""
            /* Main Window */
            QMainWindow {{
                background-color: {bg_color};
                color: {text_color};
            }}
            
            /* Labels */
            QLabel {{
                color: {text_color};
                background-color: transparent;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
            
            /* Input Fields */
            QLineEdit {{
                background-color: {input_bg};
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: {text_color};
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
            QLineEdit:focus {{
                border-color: {accent_color};
                background-color: {surface_color};
            }}
            QLineEdit::placeholder {{
                color: {text_secondary};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {button_color};
                color: {button_text_color};
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {button_color};
                transform: translateY(0px);
            }}
            QPushButton:disabled {{
                background-color: {text_secondary};
                color: {bg_color};
            }}
            
            /* Table Widget */
            QTableWidget {{
                background-color: {surface_color};
                alternate-background-color: {header_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                color: {text_color};
                gridline-color: {border_color};
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {border_color};
            }}
            QTableWidget::item:selected {{
                background-color: {accent_color}40;
                color: {text_color};
            }}
            QTableWidget::item:hover {{
                background-color: {accent_color}20;
            }}
            
            /* Table Headers */
            QHeaderView::section {{
                background-color: {header_color};
                color: {text_color};
                border: none;
                border-right: 1px solid {border_color};
                border-bottom: 2px solid {accent_color};
                padding: 12px 8px;
                font-weight: 600;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 12px;
            }}
            QHeaderView::section:hover {{
                background-color: {accent_color}30;
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background-color: {header_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                text-align: center;
                font-weight: 600;
                color: {text_color};
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {accent_color}, stop:1 {button_hover});
                border-radius: 6px;
                margin: 2px;
            }}
            
            /* Checkboxes */
            QCheckBox {{
                color: {text_color};
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {border_color};
                border-radius: 4px;
                background-color: {input_bg};
            }}
            QCheckBox::indicator:checked {{
                background-color: {accent_color};
                border-color: {accent_color};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDRMNCA3TDExIDEiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
            QCheckBox::indicator:hover {{
                border-color: {accent_color};
            }}
            
            /* Dialogs */
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 12px;
            }}
            
            /* Text Edit */
            QTextEdit {{
                background-color: {surface_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                color: {text_color};
                font-family: 'Consolas', 'Courier New', monospace;
                padding: 8px;
            }}
            QTextEdit:focus {{
                border-color: {accent_color};
            }}
            
            /* Dialog Button Box */
            QDialogButtonBox QPushButton {{
                min-width: 80px;
                margin: 4px;
            }}
            
            /* Scrollbars */
            QScrollBar:vertical {{
                background-color: {header_color};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {text_secondary};
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {accent_color};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)

        # Apply theme-specific styling to special elements
        if hasattr(self, 'summary_label'):
            self.summary_label.setStyleSheet(f"""
                QLabel {{
                    color: {text_secondary};
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px;
                    background-color: {surface_color};
                    border-radius: 6px;
                    border: 1px solid {border_color};
                }}
            """)

        if hasattr(self, 'info_label'):
            self.info_label.setStyleSheet(f"""
                QLabel {{
                    color: {text_color};
                    font-size: 14px;
                    font-weight: 500;
                    padding: 8px 0px;
                }}
            """)

        # Apply modern theme to existing dialogs and plots
        for widget in self.findChildren(QDialog):
            widget.setStyleSheet(self.styleSheet())

        # Style plot widgets with modern colors
        for plot in self.findChildren(pg.PlotWidget):
            plot.setBackground(surface_color)
            plot.getAxis('left').setPen(text_color)
            plot.getAxis('bottom').setPen(text_color)
            plot.getAxis('left').setTextPen(text_color)
            plot.getAxis('bottom').setTextPen(text_color)
            # Update plot grid
            plot.showGrid(x=True, y=True, alpha=0.3)

    def show_about_dialog(self):
        dlg = AboutDialog(self)
        dlg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkMonitor()
    window.show()
    sys.exit(app.exec_())
