# cx_Freeze build script for NetworkMonitor
from cx_Freeze import setup, Executable
import sys
import os

base = None
# Dependencies are automatically detected, but some modules need manual configuration
build_exe_options = {
    "packages": ["os", "scapy", "manuf", "customtkinter", "psutil", "ping3", "psutil","speedtest", "matplotlib"],
    "include_files": [
        ("I.T-Assistant.png", "I.T-Assistant.ico"),
    ],
    "excludes": [],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="I.T Assistant",
    version="1.1",
    description="Network Monitor App",
    options={"build_exe": build_exe_options},
    executables=[Executable("NetworkMonitor_CTk_Full.py", base=base, icon="I.T-Assistant.ico")],
)
