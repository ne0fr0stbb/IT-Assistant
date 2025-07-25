# I.T Assistant - Network Monitor Documentation

## Overview
I.T Assistant Network Monitor is a comprehensive CustomTkinter-based GUI application for network device discovery, monitoring, and analysis. It provides real-time network scanning, device monitoring, nmap integration, internet speed testing, and system tray functionality.

## Program Architecture

### Core Components
The program is organized into multiple Python modules:

1. **`NetworkMonitor_CTk_Full.py`** - Main GUI application and entry point
2. **`live_monitor.py`** - Real-time device monitoring module
3. **`nmap_monitor.py`** - Nmap integration module
4. **`settings.py`** & **`settings_manager.py`** - Application settings and preferences
5. **`system_tray.py`** - System tray integration
6. **`email_alert_manager.py`** - Email notification system

## Main Application (NetworkMonitor_CTk_Full.py)

### Key Classes

#### `NetworkMonitorApp` (Main Application Class)
- **Purpose**: Main application window with modern CustomTkinter interface
- **Inheritance**: Creates and manages `customtkinter.CTk` root window
- **Features**:
  - Auto-detects network interfaces and ranges
  - Threaded network scanning with real-time updates
  - Device table with selection capabilities
  - Integrated tools and network information display
  - System tray minimization support
  - Theme switching (dark/light mode)
  - Settings persistence

#### `NetworkScanner` (Network Discovery Engine)
- **Purpose**: Handles comprehensive network device discovery
- **Key Features**:
  - ARP scanning using Scapy (with ping fallback)
  - Parallel scanning using ThreadPoolExecutor
  - MAC address manufacturer lookup
  - Web service detection (HTTP/HTTPS)
  - Hostname resolution with timeout handling
  - Real-time progress callbacks

**Key Methods**:
- `arp_scan_ip()`: Scans single IP using ARP requests
- `ping_host_simple()`: Fallback ping scanning with response time
- `check_web_port()`: Tests for web services on ports 80/443
- `get_hostname()`: Reverse DNS lookup with timeout
- `get_manufacturer()`: MAC address to manufacturer mapping

#### `DeviceMonitor` (Live Monitoring)
- **Purpose**: Continuous monitoring of selected devices
- **Features**:
  - Real-time ping monitoring with configurable intervals
  - Latency history buffering
  - Status tracking (up/down)
  - Thread-safe callback system

#### `SpeedTestRunner` (Internet Speed Testing)
- **Purpose**: Internet speed test functionality
- **Features**:
  - Download/upload speed measurement
  - Ping latency testing
  - Server selection
  - Progress callbacks and cancellation support

## User Interface Design

### Main Window Layout

#### Sidebar (Fixed Width: 260px)
1. **Logo and Branding**
   - I.T Assistant logo
   - Application title and subtitle

2. **Network Settings Frame**
   - Interface dropdown (auto-detect + manual selection)
   - Network range input field
   - Auto-detect button
   - Network scan button

3. **Network Tools Frame**
   - Live Monitor button
   - Nmap Scan button
   - Internet Speed Test button

4. **Network Information Frame**
   - Local IP address
   - Subnet mask
   - Gateway address
   - MAC address
   - External IP address
   - Internet connectivity status

#### Main Content Area
1. **Header Section**
   - Information label
   - Search bar with real-time filtering
   - Progress bar
   - Device summary statistics

2. **Device Table** (Scrollable)
   - **Columns**:
     - Select (checkbox)
     - Profile
     - IP Address
     - MAC Address
     - Hostname
     - Friendly Name
     - Manufacturer
     - Response Time
     - Web Service (clickable "Open" button)
     - **Actions** (Individual buttons):
       - **Details** button - Shows device information dialog
       - **Nmap** button - Opens nmap scanning dialog
     - Notes

3. **Status Bar**
   - Current application status
   - Scan progress information

### Menu System
- **File Menu**: Open, Save Report, Exit
- **Options Menu**: Toggle Theme, Settings
- **About Menu**: Application information

## Key Features

### Network Scanning
- **Auto-detection**: Automatically detects active network interfaces
- **CIDR Support**: Accepts standard CIDR notation (e.g., 192.168.1.0/24)
- **Parallel Scanning**: Multi-threaded scanning for fast results
- **Real-time Updates**: Devices appear in table as they're discovered
- **Comprehensive Data**: IP, MAC, hostname, manufacturer, response time, web services

### Device Actions
- **Details Button**: Shows comprehensive device information dialog
- **Nmap Button**: Opens nmap scanning dialog with preset scan types:
  - Quick Scan (-F)
  - OS Detection (-O)
  - Port Scan (-p 1-10000)
  - Service Version (-sV)
  - Top 100 Ports (--top-ports 100)
  - Firewall Evasion (-f)
  - Traceroute (--traceroute)

### Live Monitoring
- **Device Selection**: Multi-select devices for monitoring
- **Real-time Graphs**: Live latency plots using matplotlib
- **Status Indicators**: Up/down status with color coding
- **Configurable Intervals**: Adjustable ping intervals
- **Historical Data**: Maintains ping history buffers

### Internet Speed Testing
- **Full Speed Test**: Download, upload, and ping measurements
- **Server Selection**: Automatic best server selection
- **Progress Tracking**: Real-time progress with cancellation
- **Results Display**: Detailed results with server information

### System Integration
- **System Tray**: Minimize to system tray (if available)
- **Theme Support**: Dark/light theme switching
- **Settings Persistence**: Saves preferences across sessions
- **Window State**: Remembers window size and position

## Technical Implementation

### Dependencies
- **CustomTkinter**: Modern GUI framework
- **scapy**: ARP scanning and network analysis
- **psutil**: System and network interface information
- **matplotlib**: Real-time graphing
- **speedtest-cli**: Internet speed testing
- **manuf**: MAC address manufacturer lookup
- **PIL (Pillow)**: Image handling for icons

### Threading Architecture
- **Main Thread**: GUI updates and user interaction
- **Scan Thread**: Network discovery operations
- **Monitor Threads**: Individual device monitoring
- **Speed Test Thread**: Internet speed testing
- **Callback System**: Thread-safe GUI updates

### Data Management
- **Device Storage**: In-memory list with search/filter capabilities
- **Settings**: JSON-based configuration persistence
- **Export/Import**: CSV format for scan results
- **Real-time Updates**: Observer pattern for live data

### Error Handling
- **Network Failures**: Graceful degradation with fallback methods
- **Missing Dependencies**: Feature detection with user notifications
- **Platform Compatibility**: Windows, macOS, and Linux support
- **Permission Issues**: Clear error messages for administrator requirements

## Installation and Deployment

### Requirements
- Python 3.7+
- Network access for scanning
- Optional: Nmap for advanced scanning features
- Optional: Administrator privileges for some scan types

### Packaging
- **PyInstaller**: Single executable generation
- **Frozen Assets**: Embedded icons and resources
- **Installer Support**: Windows installer creation
- **Portable Mode**: Self-contained deployment option

## Usage Scenarios

### Basic Network Discovery
1. Launch application
2. Auto-detect network or enter IP range
3. Click "Network Scan"
4. View discovered devices in table
5. Use Details/Nmap buttons for more information

### Live Device Monitoring
1. Perform network scan
2. Select devices to monitor (checkboxes)
3. Click "Live Monitor"
4. View real-time latency graphs and status

### Network Troubleshooting
1. Scan network to identify devices
2. Use Nmap button for detailed port/service analysis
3. Monitor problematic devices with live monitoring
4. Export results for documentation

### Speed Testing
1. Click "Internet Speed Test" in sidebar
2. Wait for automatic server selection
3. Monitor download/upload progress
4. View detailed results with server information

## Configuration and Customization

### Settings Options
- **Theme**: Dark/light mode selection
- **Window Size**: Persistent window dimensions
- **Scan Parameters**: Timeout and thread configuration
- **Monitor Intervals**: Live monitoring frequency
- **Network Interface**: Manual interface selection

### Advanced Features
- **Email Alerts**: Device monitoring notifications
- **Custom Profiles**: Device categorization
- **Friendly Names**: Custom device naming
- **Notes**: Device annotation system

## Troubleshooting

### Common Issues
1. **Nmap Not Found**: Install nmap and ensure PATH configuration
2. **Permission Errors**: Run as administrator for some scan types
3. **Network Access**: Verify network connectivity and firewall settings
4. **Slow Scanning**: Adjust thread count or network range
5. **Missing Dependencies**: Install required Python packages

### Performance Optimization
- **Thread Pool Size**: Adjust for network capacity
- **Scan Timeouts**: Balance speed vs. accuracy
- **Monitor Buffer Size**: Configure history retention
- **Interface Selection**: Choose optimal network interface

This documentation reflects the current state of the I.T Assistant Network Monitor application as of the latest updates, including the new individual action buttons, comprehensive network information display, and integrated tool functionality.
