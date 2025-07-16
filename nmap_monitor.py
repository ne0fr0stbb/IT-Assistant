#!/usr/bin/env python3
"""
Nmap Monitor Module for Network Monitor
Handles Nmap scanning functionality and related operations
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import platform


class NmapMonitor:
    """Nmap scanning functionality"""

    def __init__(self, parent_app):
        self.parent_app = parent_app

    def show_nmap_dialog(self, ip):
        """Show nmap options dialog"""
        nmap_window = ctk.CTkToplevel(self.parent_app.root)
        nmap_window.title(f"Nmap Options for {ip}")
        nmap_window.geometry("800x600")
        nmap_window.transient(self.parent_app.root)

        # Info label
        info_label = ctk.CTkLabel(
            nmap_window,
            text=f"Select an Nmap scan to run on {ip}:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        info_label.pack(pady=20)

        # Buttons frame
        buttons_frame = ctk.CTkFrame(nmap_window)
        buttons_frame.pack(pady=10, padx=20, fill="x")

        # Nmap scan buttons
        scans = [
            ("Quick Scan", ["-F"]),
            ("OS Detection", ["-O"]),
            ("Port Scan", ["-p", "1-10000"]),
            ("Service Version", ["-sV"]),
            ("Top 100 Ports", ["--top-ports", "100"]),
            ("Firewall Evasion", ["-f"]),
            ("Traceroute", ["--traceroute"])
        ]

        for i, (name, args) in enumerate(scans):
            btn = ctk.CTkButton(
                buttons_frame,
                text=name,
                command=lambda a=args: self.run_nmap(ip, a, result_text)
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="ew")
            buttons_frame.grid_columnconfigure(i%3, weight=1)

        # Results text area
        result_text = ctk.CTkTextbox(nmap_window, font=ctk.CTkFont(family="Consolas"))
        result_text.pack(pady=20, padx=20, fill="both", expand=True)

    def run_nmap(self, ip, args, result_widget):
        """Run nmap scan"""
        result_widget.delete("1.0", "end")
        result_widget.insert("1.0", "Scanning...")

        def nmap_thread():
            try:
                if platform.system().lower() == 'windows':
                    result = subprocess.run(
                        ['nmap'] + args + [ip],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    result = subprocess.run(
                        ['nmap'] + args + [ip],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                output = result.stdout or result.stderr
            except subprocess.TimeoutExpired:
                output = "Nmap scan timed out"
            except FileNotFoundError:
                output = self.get_nmap_installation_message()
            except Exception as e:
                output = f"Error running nmap: {e}"

            self.parent_app.root.after(0, lambda: self.update_nmap_result(result_widget, output))

        threading.Thread(target=nmap_thread, daemon=True).start()

    def get_nmap_installation_message(self):
        """Get detailed nmap installation instructions"""
        os_name = platform.system().lower()

        if os_name == "windows":
            return """NMAP NOT FOUND - Installation Required

Nmap is not installed on your system. To use network scanning features, please install Nmap:

📋 INSTALLATION INSTRUCTIONS FOR WINDOWS:

1. Visit the official Nmap website:
   https://nmap.org/download.html

2. Download the Windows installer:
   - Look for "Latest stable release self-installer"
   - Download the .exe file (usually named nmap-X.XX-setup.exe)

3. Install Nmap:
   - Run the downloaded .exe file as Administrator
   - Follow the installation wizard
   - Make sure to check "Add Nmap to PATH" during installation

4. Restart the application:
   - Close this Network Monitor application
   - Restart it after Nmap installation completes

💡 ALTERNATIVE INSTALLATION METHODS:

• Using Chocolatey (if installed):
  choco install nmap

• Using Windows Package Manager:
  winget install Insecure.Nmap

⚠️  IMPORTANT NOTES:
- Nmap requires administrator privileges for some scan types
- Windows Defender or antivirus may flag Nmap (this is normal)
- Add Nmap to your antivirus whitelist if needed

🔄 After installation, try the scan again."""

        elif os_name == "darwin":  # macOS
            return """NMAP NOT FOUND - Installation Required

Nmap is not installed on your system. To use network scanning features, please install Nmap:

📋 INSTALLATION INSTRUCTIONS FOR macOS:

1. Using Homebrew (Recommended):
   brew install nmap

2. Using MacPorts:
   sudo port install nmap

3. Manual Installation:
   - Visit: https://nmap.org/download.html
   - Download the macOS installer (.dmg file)
   - Run the installer and follow instructions

4. Restart the application after installation.

🔄 After installation, try the scan again."""

        else:  # Linux and others
            return """NMAP NOT FOUND - Installation Required

Nmap is not installed on your system. To use network scanning features, please install Nmap:

📋 INSTALLATION INSTRUCTIONS FOR LINUX:

• Ubuntu/Debian:
  sudo apt update
  sudo apt install nmap

• CentOS/RHEL/Fedora:
  sudo yum install nmap     (or: sudo dnf install nmap)

• Arch Linux:
  sudo pacman -S nmap

• From source:
  Visit https://nmap.org/download.html

🔄 After installation, try the scan again."""

    def update_nmap_result(self, widget, result):
        """Update nmap result display"""
        widget.delete("1.0", "end")
        widget.insert("1.0", result)
