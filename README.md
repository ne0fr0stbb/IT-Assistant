# Network Monitor 🌐

A comprehensive CustomTkinter-based GUI application for network device discovery, real-time monitoring, and security analysis. Discover active devices on your network, monitor their health in real-time, and perform security scans with integrated nmap functionality.

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-v5.2+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20|%20Linux%20|%20macOS-lightgrey.svg)

## ✨ Features

### 🔍 Network Discovery
- **ARP-based scanning** for fast and accurate device discovery
- **Automatic gateway detection** with manual IP range override
- **Real-time device discovery** as scanning progresses
- **Manufacturer identification** from MAC addresses using OUI database
- **Web service detection** (HTTP/HTTPS on ports 80/443)
- **Hostname resolution** via reverse DNS lookup
- **Response time monitoring** with problematic device highlighting (>500ms)

### 📊 Real-time Monitoring
- **Live ping monitoring** with customizable intervals
- **Real-time graphs** showing latency over time using matplotlib
- **Multi-device monitoring** in maximizable grid layout
- **Cross-platform ping implementation** (Windows/Linux/macOS)
- **Historical data buffering** for trend analysis
- **Full-screen monitoring window** with optimal screen utilization

### 🔐 Security Analysis
- **Integrated nmap scanning** with multiple scan types:
  - Quick Scan (-F)
  - OS Detection (-O)
  - Port Scan (-p 1-10000)
  - Service Version Detection (-sV)
  - Top 100 Ports (--top-ports 100)
  - Firewall Evasion (-f)
  - Traceroute (--traceroute)
- **Asynchronous scanning** to prevent GUI blocking

### 🌐 Internet Connectivity
- **Built-in speed test** functionality
- **Download/Upload speed measurement** in Mbps
- **Ping latency testing** to internet servers
- **Retry mechanism** for reliable results

### 🎨 Modern User Interface
- **Responsive design** with sortable, filterable device table
- **Modern CustomTkinter styling** with clean, professional appearance
- **Real-time search and filtering** by IP, MAC, or hostname
- **Contextual interactions** (click web services, double-click for nmap)
- **Progress indicators** and status updates
- **CSV import/export** for data persistence
- **Live monitoring window** with maximizable full-screen view

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager
- nmap (for security scanning features)

### Install nmap
#### Windows
Download and install from [nmap.org](https://nmap.org/download.html)

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install nmap
```

#### macOS
```bash
brew install nmap
```

### Install Network Monitor
1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/NetworkMonitor.git
   cd NetworkMonitor
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install additional dependencies**
   ```bash
   pip install scapy manuf speedtest-cli
   ```

## 🖥️ Usage

### Running the Application
```bash
python NetworkMonitorGUI.py
```

### Basic Workflow
1. **Launch the application** - The main window will open with an empty device table
2. **Start scanning** - Click "Scan" to discover devices (uses auto-detected gateway range)
3. **Custom IP range** - Enter specific range like `192.168.1.0/24` before scanning
4. **View results** - Devices appear in real-time with detailed information
5. **Interact with devices**:
   - **Click web services** to open in browser
   - **Double-click IP addresses** to launch nmap scans
   - **Select devices** for live monitoring
6. **Live monitoring** - Check devices and click "Live Monitoring" for real-time graphs
7. **Export data** - Use File → Save to export results as CSV

### Advanced Features
- **Search/Filter**: Use the search box to filter by IP, MAC, or hostname
- **Theme Toggle**: Options → Toggle Theme for dark/light mode
- **Speed Test**: Click "Internet Speed Test" for connectivity analysis
- **Data Management**: File → Open/Save for CSV import/export

## 📁 Project Structure

```
NetworkMonitor/
├── NetworkMonitorGUI.py      # Main application and GUI
├── scanthread.py             # Threaded network scanning
├── NetworkScanner.py         # Basic ARP scanning utilities
├── livemonitor.py            # Real-time device monitoring with matplotlib
├── speedtest_dialog.py       # Internet speed testing
├── utils.py                  # Utility functions
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🔧 Technical Details

### Architecture
- **CustomTkinter** for modern GUI framework
- **Scapy** for low-level network packet manipulation
- **Threading** for non-blocking operations
- **Callback-based communication** for thread-safe GUI updates

### Scanning Technology
- **ARP requests** for Layer 2 device discovery
- **Concurrent scanning** (up to 32 parallel threads)
- **Timeout handling** for unreachable devices
- **MAC OUI lookup** for manufacturer identification

### Monitoring Implementation
- **Cross-platform ping** using subprocess
- **Regex parsing** for latency extraction
- **Circular buffering** for efficient memory usage
- **Real-time plotting** with matplotlib
- **Grid layout optimization** for multiple device monitoring

## 📋 Requirements

### Python Dependencies
```
customtkinter>=5.2
matplotlib>=3.5
pysnmp>=4.4
speedtest-cli>=2.1
scapy
manuf
psutil
```

### System Requirements
- **Operating System**: Windows 7+, Linux, macOS 10.12+
- **Memory**: 512MB RAM minimum
- **Network**: Ethernet or WiFi connection
- **Privileges**: Administrator/root for raw socket access (ARP scanning)

## 🛠️ Troubleshooting

### Common Issues

**"Permission denied" errors**
- Run with administrator privileges on Windows
- Use `sudo` on Linux/macOS for raw socket access

**Devices not appearing**
- Check firewall settings
- Ensure you're on the same network segment
- Try a smaller IP range (e.g., /24 instead of /23)

**nmap features not working**
- Verify nmap is installed and in PATH
- Check that nmap executable is accessible

**Speed test failing**
- Check internet connectivity
- Try running the speed test multiple times
- Verify firewall allows speedtest-cli

### Performance Tips
- Use smaller IP ranges for faster scanning
- Reduce live monitoring interval for less CPU usage
- Close monitoring dialogs when not needed

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Scapy](https://scapy.net/) for powerful packet manipulation capabilities
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern GUI framework
- [Matplotlib](https://matplotlib.org/) for high-quality real-time plotting
- [nmap](https://nmap.org/) for comprehensive network scanning functionality
- [manuf](https://github.com/coolbho3k/manuf) for MAC address manufacturer lookup

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the [documentation](NetworkMonitor_Documentation.md) for detailed technical information
- Review the troubleshooting section above

---

**Made with ❤️ for network administrators, security professionals, and IT enthusiasts**
