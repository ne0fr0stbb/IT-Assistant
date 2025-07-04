# setup.py
from cx_Freeze import setup, Executable
import sys
import os

# Dependencies from requirements.txt
with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Include all your local Python modules
include_files = [
    "scanthread.py",
    "utils.py", 
    "livemonitor.py",
    "speedtest_dialog.py",
    "NetworkScanner.py",
    "I.T-Assistant.png"
]

build_exe_options = {
    "packages": [
        "PyQt5.QtCore",
        "PyQt5.QtWidgets",
        "PyQt5.QtGui",
        "PyQt5.sip",
        "pyqtgraph",
        "speedtest",
        "pysnmp",
        "manuf",
        "ping3",
        "psutil",
        "scapy",
        "numpy",
        "encodings",
        "encodings.utf_8",
        "encodings.cp1252",
        "dataclasses",
        "inspect",
        "calendar",
    ],
    "includes": [
        "difflib",
        "subprocess",
        "threading",
        "queue",
        "csv",
        "webbrowser",
        "ipaddress",
        "socket",
        "time",
        "concurrent.futures",
        "sys",
        "os",
        "json",
        "re",
        "datetime",
        "collections",
        "urllib",
        "urllib.request",
        "urllib.parse",
        "http",
        "http.client",
        "ssl",
        "hashlib",
        "random",
        "struct",
        "platform",
    ],
    "include_files": include_files,
    "excludes": [
        "tkinter",  # Exclude tkinter if not used
        "unittest",  # Exclude unittest if not needed
        "email",  # Exclude email package if not used
    ],
    "build_exe": "build/exe",
}

setup(
    name="NetworkMonitor",
    version="1.0",
    description="I.T Assistant - Network Monitor and Device Scanner",
    author="Jason Burnham",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "NetworkMonitorGUI.py",
            base="Win32GUI" if sys.platform == "win32" else None,
            icon="I.T-Assistant.png",
            target_name="NetworkMonitor.exe"
        )
    ],
)
