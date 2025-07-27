# I.T Assistant - Network Monitor Build Guide

## Application Overview

**I.T Assistant** is a comprehensive network monitoring and management tool built with CustomTkinter. The application features modern Material UI themes, real-time device monitoring, network scanning, and advanced network management capabilities.

### Current Application State

The application has evolved significantly and now includes:

#### Core Features
- **Network Device Discovery**: ARP-based scanning with automatic network detection
- **Live Device Monitoring**: Real-time ping monitoring with graphical displays
- **Internet Speed Testing**: Built-in speedtest functionality
- **Nmap Integration**: Multiple scan types with dedicated dialog interface
- **Profile Management**: Device profiles with friendly names and notes
- **System Tray Support**: Minimize to system tray functionality
- **Email Alerts**: Network monitoring alerts via email
- **Settings Management**: Persistent application settings

#### User Interface Updates
- **Actions Buttons**: The tree view actions are now individual buttons instead of dropdown:
  - **Details Button**: Shows comprehensive device information
  - **Nmap Button**: Opens the nmap dialog window for the selected device
- **Enhanced Device Table**: Includes Profile, Friendly Name, and Notes columns
- **Responsive Design**: Proper window scaling and theme switching
- **Modern Styling**: CustomTkinter-based interface with dark/light theme support

## Build Requirements

### Python Dependencies
```txt
customtkinter>=5.2
matplotlib>=3.5
pysnmp>=4.4
speedtest-cli>=2.1
manuf
psutil
scapy
ping3
numpy<2
pystray
```

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: Windows, Linux, or macOS
- **Nmap**: Optional but recommended for advanced scanning features
- **Administrator/Root Privileges**: Required for some network scanning features

## File Structure

### Core Application Files
- `NetworkMonitor_CTk_Full.py` - Main application file
- `settings.py` - Settings management system
- `settings_manager.py` - Settings dialog interface
- `live_monitor.py` - Real-time device monitoring
- `nmap_monitor.py` - Nmap integration module
- `system_tray.py` - System tray functionality
- `profile_manager.py` - Device profile management
- `email_alert_manager.py` - Email notification system
- `network.db` - SQLite database for profiles and settings

### Build Files
- `build_pyinstaller.bat` - Windows build script
- `pyinstaller config.json` - PyInstaller configuration
- `requirements.txt` - Python dependencies

### Assets
- `I.T-Assistant.ico` - Application icon
- `I.T-Assistant.png` - Application logo

## Quick Build Instructions

### Method 1: Auto-Py-to-Exe with Config (Recommended)

The project includes a pre-configured PyInstaller configuration file that can be imported into auto-py-to-exe for easy GUI-based building.

#### Step 1: Install Auto-Py-to-Exe
```batch
pip install auto-py-to-exe
```

#### Step 2: Launch Auto-Py-to-Exe
```batch
auto-py-to-exe
```

#### Step 3: Import Configuration
1. In the auto-py-to-exe interface, click "Import Config" (usually in the top-right)
2. Navigate to your project folder and select `pyinstaller config.json`
3. The configuration will automatically populate all settings:
   - **Script Location**: NetworkMonitor_CTk_Full.py
   - **One Directory**: Selected (creates folder with executable and dependencies)
   - **Window Based**: Selected (no console window)
   - **Icon**: I.T-Assistant.ico
   - **Name**: I.T Assistant
   - **Clean Build**: Enabled
   - **Optimization**: Level 1

#### Step 4: Build
1. Verify all settings are correct
2. Click "Convert .py to .exe"
3. The build process will start and show progress
4. Once complete, find your executable in the `output/I.T Assistant/` folder

#### Step 5: Test
Navigate to `output/I.T Assistant/` and run `I.T Assistant.exe`

### Method 2: Automated Batch Build
```batch
# Windows
build_pyinstaller.bat
```

### Method 3: Manual PyInstaller Build
```batch
# Install PyInstaller if not already installed
pip install pyinstaller

# Install dependencies
pip install -r requirements.txt

# Clean previous builds
rmdir /s /q dist build

# Build application
pyinstaller --clean --onedir --windowed ^
    --icon=I.T-Assistant.ico ^
    --name="I.T Assistant" ^
    --add-data="I.T-Assistant.png;." ^
    --add-data="I.T-Assistant.ico;." ^
    --hidden-import=pystray ^
    --hidden-import=PIL ^
    --hidden-import=matplotlib ^
    --hidden-import=scapy ^
    NetworkMonitor_CTk_Full.py
```

## Configuration Details

### Pre-configured Settings (pyinstaller config.json)
The included configuration file sets up the following optimized build settings:

- **Build Type**: One Directory (--onedir) - Creates a folder with the executable and all dependencies
- **Console**: Disabled (--windowed) - No console window appears
- **Icon**: I.T-Assistant.ico - Custom application icon
- **Name**: "I.T Assistant" - Final executable name
- **Clean Build**: Enabled - Removes previous build artifacts
- **Optimization**: Level 1 - Basic Python optimization
- **UPX Compression**: Enabled - Reduces file size

### Why Auto-Py-to-Exe is Recommended

1. **Visual Interface**: Easy-to-use GUI instead of command line
2. **Configuration Management**: Save and reuse build settings
3. **Real-time Preview**: See the PyInstaller command as you configure
4. **Error Handling**: Better error messages and debugging information
5. **Progress Tracking**: Visual progress bar during build process
6. **Cross-platform**: Works on Windows, macOS, and Linux

## Distribution

### Windows Installer
The project includes an Inno Setup script for creating a Windows installer:
- Location: `Windows Installer/install_script.iss`
- Output: `ITAssistantSetup.exe`

### Portable Distribution
The built executable can run as a portable application without installation.

## Module Dependencies and Features

### Required Modules
- **CustomTkinter**: Modern UI framework
- **psutil**: System and network information
- **matplotlib**: Real-time monitoring graphs
- **sqlite3**: Profile and settings database

### Optional Modules (with graceful degradation)
- **scapy**: Advanced ARP scanning (falls back to ping)
- **manuf**: MAC address manufacturer lookup
- **speedtest-cli**: Internet speed testing
- **pystray**: System tray integration
- **nmap**: Advanced network scanning

### Feature Availability
The application detects available modules at runtime and adjusts functionality accordingly:
- Missing `scapy`: Falls back to ping-based scanning
- Missing `speedtest-cli`: Speed test feature disabled
- Missing `pystray`: No system tray support
- Missing `nmap`: Nmap scanning unavailable with installation instructions

## Troubleshooting

### Common Build Issues

1. **Missing Dependencies**
   ```batch
   pip install -r requirements.txt
   ```

2. **PyInstaller Not Found**
   ```batch
   pip install pyinstaller
   ```

3. **Permission Issues (Windows)**
   - Run command prompt as Administrator
   - Disable antivirus temporarily during build

4. **Large File Size**
   - Use `--exclude-module` flags for unused modules
   - Consider using `--onedir` instead of `--onefile`

### Runtime Issues

1. **Network Scanning Failures**
   - Ensure administrator/root privileges
   - Check firewall settings
   - Verify network interface detection

2. **Nmap Not Found**
   - Install nmap from https://nmap.org/download.html
   - Add nmap to system PATH
   - Restart application after installation

3. **System Tray Issues**
   - Install pystray: `pip install pystray`
   - Check system tray settings in OS

## Development Notes

### Code Structure
- **Modular Design**: Features are separated into individual modules
- **Graceful Degradation**: Missing optional dependencies don't break core functionality
- **Thread Safety**: Network operations use proper threading
- **Error Handling**: Comprehensive error handling with user-friendly messages

### Testing
Individual test files are available for debugging specific components:
- `test_gui_scan.py` - GUI scanning functionality
- `test_email_functionality.py` - Email alert system
- `test_buttons.py` - UI button functionality
- Various other test files for specific features

### Database
- **SQLite Database**: `network.db` stores device profiles and settings
- **Automatic Creation**: Database is created automatically on first run
- **Profile Management**: Devices can be saved to profiles with custom names and notes

This build guide reflects the current state of the I.T Assistant application as of July 2025, including all implemented features and current UI design with individual action buttons instead of dropdown menus.
