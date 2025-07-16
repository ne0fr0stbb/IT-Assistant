#!/usr/bin/env python3
"""
Settings Configuration for Network Monitor
Handles application settings with persistence and validation
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime


@dataclass
class ScanSettings:
    """Network scanning configuration"""
    max_workers: int = 32
    timeout: float = 2.0
    ping_timeout: int = 1000
    enable_scapy: bool = True
    enable_mac_lookup: bool = True
    auto_detect_network: bool = True
    default_network_range: str = "192.168.1.0/24"


@dataclass
class MonitorSettings:
    """Live monitoring configuration"""
    update_interval: int = 1
    buffer_size: int = 100
    graph_refresh_rate: int = 1
    max_monitoring_devices: int = 10
    alert_threshold_ms: int = 500
    enable_alerts: bool = True
    auto_start_monitoring: bool = False


@dataclass
class InterfaceSettings:
    """User interface configuration"""
    theme: str = "dark"  # "dark" or "light"
    window_width: int = 1200
    window_height: int = 800
    sidebar_width: int = 280
    remember_window_size: bool = True
    auto_save_reports: bool = False
    show_tooltips: bool = True
    confirm_exit: bool = True


@dataclass
class NetworkSettings:
    """Network-specific settings"""
    preferred_interface: str = "auto"
    enable_ipv6: bool = False
    dns_servers: list = None
    proxy_settings: dict = None
    connection_timeout: int = 10
    retry_attempts: int = 3

    def __post_init__(self):
        if self.dns_servers is None:
            self.dns_servers = ["8.8.8.8", "8.8.4.4"]
        if self.proxy_settings is None:
            self.proxy_settings = {"enabled": False, "host": "", "port": 8080}


@dataclass
class AlertSettings:
    """Alert and notification settings"""
    enable_sound: bool = True
    enable_desktop_notifications: bool = True
    email_notifications: bool = False
    email_settings: dict = None
    alert_types: dict = None

    def __post_init__(self):
        if self.email_settings is None:
            self.email_settings = {
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "use_tls": True
            }
        if self.alert_types is None:
            self.alert_types = {
                "device_down": True,
                "high_latency": True,
                "new_device": True,
                "network_change": True
            }


@dataclass
class ApplicationSettings:
    """Main application settings container"""
    scan: ScanSettings = None
    monitor: MonitorSettings = None
    interface: InterfaceSettings = None
    network: NetworkSettings = None
    alerts: AlertSettings = None

    def __post_init__(self):
        if self.scan is None:
            self.scan = ScanSettings()
        if self.monitor is None:
            self.monitor = MonitorSettings()
        if self.interface is None:
            self.interface = InterfaceSettings()
        if self.network is None:
            self.network = NetworkSettings()
        if self.alerts is None:
            self.alerts = AlertSettings()


class SettingsManager:
    """Manages application settings with persistence"""

    def __init__(self, app_name: str = "NetworkMonitor"):
        self.app_name = app_name
        self.settings_dir = self._get_settings_directory()
        self.settings_file = self.settings_dir / "settings.json"
        self.settings = ApplicationSettings()

        # Ensure settings directory exists
        self.settings_dir.mkdir(parents=True, exist_ok=True)

        # Load settings on initialization
        self.load_settings()

    def _get_settings_directory(self) -> Path:
        """Get the appropriate settings directory for the OS"""
        import platform

        system = platform.system()
        if system == "Windows":
            # Use AppData/Roaming for Windows
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            return Path(appdata) / self.app_name
        elif system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / self.app_name
        else:  # Linux and others
            # Use XDG_CONFIG_HOME or ~/.config
            config_home = os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')
            return Path(config_home) / self.app_name.lower()

    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Reconstruct settings from JSON data
                self.settings = ApplicationSettings(
                    scan=ScanSettings(**data.get('scan', {})),
                    monitor=MonitorSettings(**data.get('monitor', {})),
                    interface=InterfaceSettings(**data.get('interface', {})),
                    network=NetworkSettings(**data.get('network', {})),
                    alerts=AlertSettings(**data.get('alerts', {}))
                )
                return True
            else:
                # Create default settings file if it doesn't exist
                self.save_settings()
                return False
        except Exception as e:
            print(f"Error loading settings: {e}")
            # If loading fails, use default settings
            self.settings = ApplicationSettings()
            return False

    def save_settings(self) -> bool:
        """Save settings to file"""
        try:
            # Convert settings to dictionary, handling nested dataclasses
            settings_dict = {
                'scan': asdict(self.settings.scan),
                'monitor': asdict(self.settings.monitor),
                'interface': asdict(self.settings.interface),
                'network': asdict(self.settings.network),
                'alerts': asdict(self.settings.alerts)
            }

            # Create backup of existing settings
            if self.settings_file.exists():
                backup_file = self.settings_file.with_suffix('.json.bak')
                self.settings_file.replace(backup_file)

            # Save settings
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_setting(self, category: str, key: str, default=None):
        """Get a specific setting value"""
        try:
            category_obj = getattr(self.settings, category)
            return getattr(category_obj, key, default)
        except AttributeError:
            return default

    def set_setting(self, category: str, key: str, value):
        """Set a specific setting value"""
        try:
            category_obj = getattr(self.settings, category)
            setattr(category_obj, key, value)
            return True
        except AttributeError:
            return False

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        self.settings = ApplicationSettings()
        self.save_settings()

    def export_settings(self, file_path: str) -> bool:
        """Export settings to a file"""
        try:
            export_data = {
                'version': '1.0',
                'exported_at': str(datetime.now()),
                'settings': {
                    'scan': asdict(self.settings.scan),
                    'monitor': asdict(self.settings.monitor),
                    'interface': asdict(self.settings.interface),
                    'network': asdict(self.settings.network),
                    'alerts': asdict(self.settings.alerts)
                }
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False

    def import_settings(self, file_path: str) -> bool:
        """Import settings from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate import data
            if 'settings' not in data:
                return False

            settings_data = data['settings']

            # Import settings
            self.settings = ApplicationSettings(
                scan=ScanSettings(**settings_data.get('scan', {})),
                monitor=MonitorSettings(**settings_data.get('monitor', {})),
                interface=InterfaceSettings(**settings_data.get('interface', {})),
                network=NetworkSettings(**settings_data.get('network', {})),
                alerts=AlertSettings(**settings_data.get('alerts', {}))
            )

            # Save imported settings
            self.save_settings()
            return True
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False


# Global settings manager instance
settings_manager = SettingsManager()


def get_settings() -> ApplicationSettings:
    """Get the global settings instance"""
    return settings_manager.settings


def save_settings() -> bool:
    """Save the global settings"""
    return settings_manager.save_settings()


def get_setting(category: str, key: str, default=None):
    """Get a specific setting value"""
    return settings_manager.get_setting(category, key, default)


def set_setting(category: str, key: str, value):
    """Set a specific setting value and save"""
    if settings_manager.set_setting(category, key, value):
        settings_manager.save_settings()
        return True
    return False


# Helper functions for common settings
def get_theme() -> str:
    """Get the current theme setting"""
    return settings_manager.get_setting('interface', 'theme', 'dark')


def set_theme(theme: str):
    """Set the theme setting"""
    if theme in ['dark', 'light']:
        set_setting('interface', 'theme', theme)


def get_window_size() -> tuple:
    """Get the window size setting"""
    width = settings_manager.get_setting('interface', 'window_width', 1200)
    height = settings_manager.get_setting('interface', 'window_height', 800)
    return width, height


def set_window_size(width: int, height: int):
    """Set the window size setting"""
    set_setting('interface', 'window_width', width)
    set_setting('interface', 'window_height', height)


def get_auto_detect_network() -> bool:
    """Get the auto-detect network setting"""
    return settings_manager.get_setting('scan', 'auto_detect_network', True)


def set_auto_detect_network(enabled: bool):
    """Set the auto-detect network setting"""
    set_setting('scan', 'auto_detect_network', enabled)


def get_monitoring_interval() -> int:
    """Get the monitoring interval setting"""
    return settings_manager.get_setting('monitor', 'update_interval', 1)


def set_monitoring_interval(interval: int):
    """Set the monitoring interval setting"""
    if interval > 0:
        set_setting('monitor', 'update_interval', interval)


if __name__ == "__main__":
    # Test the settings system
    print("Testing settings system...")

    # Test basic functionality
    print(f"Current theme: {get_theme()}")
    print(f"Window size: {get_window_size()}")

    # Test setting values
    set_theme('light')
    set_window_size(1400, 900)

    print(f"New theme: {get_theme()}")
    print(f"New window size: {get_window_size()}")

    # Test export/import
    settings_manager.export_settings('test_settings.json')
    print("Settings exported successfully")
