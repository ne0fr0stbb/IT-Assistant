from cx_Freeze import setup, Executable
import sys
import os

# Dependencies for CustomTkinter version
build_exe_options = {
    "packages": [
        "customtkinter",
        "tkinter", 
        "psutil", 
        "socket", 
        "subprocess", 
        "threading", 
        "time", 
        "datetime", 
        "json", 
        "os",
        "csv",
        "webbrowser",
        "platform",
        "re",
        "ipaddress",
        "collections",
        "concurrent.futures",
        "typing",
        "math"
    ],
    "includes": [
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "tkinter.filedialog",
        "customtkinter",
        "psutil",
        "subprocess",
        "socket",
        "threading",
        "time",
        "datetime",
        "json",
        "os",
        "csv",
        "webbrowser",
        "platform",
        "re",
        "ipaddress",
        "collections",
        "concurrent.futures",
        "typing"
    ],
    "excludes": [
        "PyQt5",
        "PyQt6", 
        "PySide2",
        "PySide6",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "pyqtgraph",
        "qt"
    ],
    "include_files": [
        # Icon file if it exists
        ("I.T-Assistant.png", "I.T-Assistant.png") if os.path.exists("I.T-Assistant.png") else None
    ],
    "zip_include_packages": [
        "email", 
        "http", 
        "urllib", 
        "xml", 
        "logging"
    ]
}

# Remove None values from include_files
build_exe_options["include_files"] = [f for f in build_exe_options["include_files"] if f is not None]

# Base for Windows GUI
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="NetworkMonitor_CustomTkinter",
    version="1.0",
    description="Network Monitor with CustomTkinter Material Design - No PyQt5 Dependencies",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="NetworkMonitor_CTk_Full.py",
            base=base,
            target_name="NetworkMonitor_CTk.exe",
            icon="I.T-Assistant.png" if os.path.exists("I.T-Assistant.png") else None
        )
    ]
)
