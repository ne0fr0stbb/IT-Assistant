# Network Monitor Program Documentation

## Overview
The Network Monitor is a comprehensive CustomTkinter-based GUI application for network device discovery, monitoring, and analysis. It uses ARP scanning to find active devices on a network and provides real-time monitoring, nmap integration, and internet speed testing capabilities.

## Program Architecture

### Core Components
The program is organized into 6 main Python modules:

1. **`NetworkMonitorGUI.py`** - Main GUI application and entry point
2. **`scanthread.py`** - Threaded network scanning functionality  
3. **`NetworkScanner.py`** - Basic ARP scanning utilities
4. **`livemonitor.py`** - Real-time device monitoring
5. **`speedtest_dialog.py`** - Internet speed testing dialog
6. **`utils.py`** - Utility functions

## Detailed Module Breakdown

### 1. NetworkMonitorGUI.py (Main Application)

This is the heart of the application containing the main GUI and application logic.

#### Key Classes:

##### `NetworkMonitor` (Main Window Class)
- **Purpose**: Main application window with device table, scan controls, and menu system
- **Inheritance**: Inherits from `customtkinter.CTk`
- **Key Attributes**:
  - `tree`: CTkTreeview displaying discovered devices
  - `scan_button`: CTkButton triggering network scanning
  - `ip_input`: CTkEntry for user input of IP range
  - `search_input`: CTkEntry to filter devices by IP/MAC
  - `all_devices`: Stores all scan results for filtering
  - `live_monitor_window`: Reference to live monitoring window

- **Key Methods**:
  - `load_data()`: Initiates network scan using ScanThread
  - `add_device_row()`: Adds discovered device to CTkTreeview
  - `filter_table()`: Filters displayed devices based on search
  - `handle_cell_click()`: Handles web service URL clicks
  - `handle_cell_double_click()`: Opens nmap dialog for IP addresses
  - `open_live_monitor()`: Opens full-screen live monitoring window
  - `update_monitor_display()`: Callback for live monitor updates

##### `NmapThread` (Background Nmap Execution)
- **Purpose**: Runs nmap commands asynchronously without blocking GUI
- **Inheritance**: Inherits from `threading.Thread`
- **Key Attributes**:
  - `ip`: Target IP address for scanning
  - `args`: Command line arguments for nmap
  - `callback`: Function to call when scan completes
- **Communication**: Uses callback mechanism for thread-safe updates

##### `NmapDialog` (Nmap Interface Dialog)
- **Purpose**: Provides GUI interface for various nmap scan types
- **Inheritance**: Inherits from `customtkinter.CTkToplevel`
- **Features**: 
  - Quick Scan (-F)
  - OS Detection (-O)  
  - Port Scan (-p 1-10000)
  - Service Version (-sV)
  - Top 100 Ports (--top-ports 100)
  - Firewall Evasion (-f)
  - Traceroute (--traceroute)

##### `LiveMonitorWindow` (Real-time Monitoring Interface)
- **Purpose**: Full-screen window displaying real-time ping graphs and device status
- **Inheritance**: Inherits from `customtkinter.CTk`
- **Key Features**:
  - Grid layout for multiple device graphs
  - Real-time latency plotting using matplotlib
  - Status indicators (up/down) with color coding
  - Maximizable interface with control buttons
  - Adaptive grid sizing based on device count
  - Thread-safe updates via main window callbacks

### 2. scanthread.py (Network Scanning Engine)

Handles the core network discovery functionality using ARP scanning.

#### Key Class:

##### `ScanThread` (Threaded Network Scanner)
- **Purpose**: Performs comprehensive network scanning without blocking the GUI
- **Inheritance**: Inherits from `threading.Thread`
- **Key Attributes**:
  - `ip_range`: CIDR notation IP range to scan
  - `mac_parser`: manuf.MacParser for manufacturer lookup
  - `callback`: Function to call with scan results

- **Communication**: Uses callback mechanism for thread-safe GUI updates
  - Real-time device discovery through callbacks
  - Progress updates via callback mechanism
  - Final results delivered through callback

- **Key Methods**:
  - `run()`: Main scanning loop using ThreadPoolExecutor for parallel scanning
  - `arp_scan_ip()`: Scans single IP using ARP requests
  - `check_web_port()`: Tests for HTTP/HTTPS services on ports 80/443
  - `get_hostname()`: Performs reverse DNS lookup
  - `get_manufacturer()`: Gets manufacturer from MAC OUI database

#### Data Flow in Scanning:
1. User clicks "Scan" button
2. `NetworkMonitor.load_data()` creates and starts `ScanThread`
3. `ScanThread.run()` parses IP range into individual hosts
4. ThreadPoolExecutor scans up to 32 IPs concurrently
5. Each completed scan calls back to GUI with device data
6. GUI updates CTkTreeview in real-time as devices are discovered
7. Main window uses `after()` method for thread-safe GUI updates

### 3. NetworkScanner.py (Basic Scanning Utilities)

Provides foundational network scanning functions that can be used standalone.

#### Key Functions:

##### `get_default_gateway()`
- **Purpose**: Discovers the default gateway for automatic IP range detection
- **Logic**: Searches network interfaces for 192.168.x.x addresses
- **Returns**: Gateway IP (e.g., "192.168.1.1") or None

##### `scan_network(ip_range)`
- **Purpose**: Basic ARP scan implementation
- **Parameters**: IP range in CIDR notation
- **Returns**: List of device dictionaries with ip, mac, response_time
- **Implementation**: Uses scapy's `srp()` function for ARP discovery

### 4. livemonitor.py (Real-time Monitoring)

Implements continuous device monitoring using ping-based health checks.

#### Key Classes:

##### `DeviceMonitor` (Individual Device Monitor)
- **Purpose**: Monitors a single device with continuous ping tests
- **Inheritance**: Inherits from `threading.Thread`
- **Key Attributes**:
  - `ip`: Device IP address to monitor
  - `interval`: Ping interval (default 2 seconds)
  - `buffer`: deque storing recent ping results (timestamp, latency, status)
  - `_running`: Thread control flag
  - `callback`: Function to call with ping updates

- **Communication**: Uses callback mechanism for real-time updates

- **Key Methods**:
  - `start()`: Begins monitoring thread
  - `stop()`: Stops monitoring thread
  - `ping_device()`: Cross-platform ping implementation
  - `_monitor_loop()`: Main monitoring loop

##### `LiveMonitorManager` (Monitor Coordinator)
- **Purpose**: Manages multiple DeviceMonitor instances
- **Key Methods**:
  - `start_monitoring(ip)`: Creates and starts monitor for device
  - `stop_monitoring(ip)`: Stops specific device monitor
  - `stop_all()`: Stops all active monitors
  - `get_buffer(ip)`: Retrieves ping history for device

#### Ping Implementation Details:
- **Windows**: Uses `ping -n 1 -w 1000 <ip>` command
- **Linux/Mac**: Uses `ping -c 1 -w 1000 <ip>` command  
- **Latency Parsing**: Regex extracts millisecond values from ping output
- **Error Handling**: Network failures return NaN latency and "down" status

### 5. speedtest_dialog.py (Internet Speed Testing)

Provides internet speed testing functionality using the speedtest-cli library.

#### Key Classes:

##### `SpeedTestThread` (Background Speed Test)
- **Purpose**: Runs speed test without blocking GUI
- **Inheritance**: Inherits from `threading.Thread`
- **Communication**: Uses callback mechanism for results
  - Success callback with download/upload/ping results
  - Error callback for test failures

##### `SpeedTestDialog` (Speed Test Interface)
- **Purpose**: Displays speed test progress and results
- **Inheritance**: Inherits from `customtkinter.CTkToplevel`
- **Features**: Shows download speed, upload speed, and ping in Mbps/ms

### 6. utils.py (Utility Functions)

Contains shared utility functions used across modules.

#### Key Functions:

##### `get_default_gateway()`
- **Purpose**: Duplicate of NetworkScanner function for modular access
- **Used by**: Main GUI for automatic IP range detection

## Data Structures

### Device Dictionary Structure
Each discovered device is represented as a dictionary containing:

```python
{
    'ip': '192.168.1.100',           # IP address string
    'mac': '00:11:22:33:44:55',     # MAC address string  
    'response_time': 0.045,          # ARP response time in seconds
    'web_service': 'http://192.168.1.100:80',  # Web service URL or None
    'hostname': 'router.local',      # DNS hostname or None
    'manufacturer': 'Apple Inc.'     # MAC manufacturer or None
}
```

## Callback-based Communication Pattern

The application uses callback mechanisms for thread-safe communication:

### Main Scanning Flow:
```
ScanThread → callback → NetworkMonitor.add_device_row()
Progress updates → callback → NetworkMonitor.update_progress()  
Scan completion → callback → NetworkMonitor.scan_complete()
```

### Live Monitoring Flow:
```
DeviceMonitor → callback → MainWindow.after() → LiveMonitorWindow.update_graph()
Ping results → main thread → matplotlib graph updates
```

### Nmap Scanning Flow:
```
NmapThread → callback → NmapDialog.display_result()
```

## Threading Architecture

The application uses multiple threading strategies:

1. **Python threading.Thread**: ScanThread, NmapThread, SpeedTestThread, DeviceMonitor
2. **ThreadPoolExecutor for Parallel Scanning**: Up to 32 concurrent IP scans
3. **Daemon Threads for Monitoring**: Background ping monitoring threads
4. **Main Thread GUI Updates**: All GUI updates via main window's after() method

## Dependencies and External Libraries

### Core Dependencies (requirements.txt):
- **customtkinter ≥5.2**: Modern GUI framework
- **matplotlib ≥3.5**: Real-time plotting for monitoring graphs
- **pysnmp ≥4.4**: SNMP functionality (imported but not used in current code)
- **speedtest-cli ≥2.1**: Internet speed testing

### Additional Python Libraries:
- **scapy**: ARP scanning and packet manipulation
- **manuf**: MAC address manufacturer lookup
- **psutil**: System and network interface information
- **ipaddress**: IP range parsing and validation
- **socket**: Network connectivity and DNS operations
- **subprocess**: System command execution (ping, nmap)
- **concurrent.futures**: Parallel execution framework

## File I/O and Persistence

### CSV Import/Export:
- **Save Report**: Exports device table to CSV format
- **Open File**: Imports previously saved CSV data
- **Format**: All table columns including IP, MAC, hostname, manufacturer, response time, web service, live monitoring status

## Theme System

The application supports dynamic theming with two modes:

### CustomTkinter Modern Styling:
- Clean, professional appearance with built-in CustomTkinter theming
- Consistent styling across all UI elements
- Modern button designs with hover effects
- Clean input fields and dropdown menus
- Professional table/tree view styling

Built-in styling includes:
- Main window with modern frame styling
- CTkTreeview with clean row and header styling
- CTkEntry with focus states
- CTkButton with hover effects
- CTkProgressBar with smooth animations
- CTkCheckBox with modern indicators
- Consistent color schemes throughout

## Error Handling

The application implements robust error handling:

- **Network Scanning**: Graceful handling of unreachable devices
- **DNS Lookups**: Fallback to IP display when hostname unavailable
- **Web Service Detection**: Timeout protection for unresponsive services
- **External Commands**: Exception handling for nmap and ping failures
- **Thread Safety**: Proper cleanup and joining of background threads

## Application Entry Point

The program starts execution in `NetworkMonitorGUI.py`:

```python
if __name__ == "__main__":
    app = NetworkMonitor()
    app.mainloop()
```

This creates the CustomTkinter application, instantiates the main window, and starts the event loop.

## Key Features Summary

1. **Network Discovery**: ARP-based device scanning with manufacturer identification
2. **Real-time Monitoring**: Full-screen monitoring window with grid layout and matplotlib graphs
3. **Security Scanning**: Integrated nmap functionality with multiple scan types
4. **Web Service Detection**: Automatic discovery of HTTP/HTTPS services
5. **Internet Speed Testing**: Built-in speed test functionality
6. **Modern UI**: CustomTkinter-based responsive design with professional styling
7. **Data Export**: CSV import/export for scan results
8. **Multi-threading**: Non-blocking operations with callback-based thread safety

This architecture provides a scalable, maintainable foundation for network monitoring and analysis tasks.
