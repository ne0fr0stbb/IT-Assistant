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
    window_width: int = 1100
    window_height: int = 650
    sidebar_width: int = 280
    remember_window_size: bool = True
    auto_save_reports: bool = False
    show_tooltips: bool = True
    confirm_exit: bool = True


@dataclass
class NetworkSettings:
    """Network configuration"""
    preferred_interface: str = ""
    preferred_dns: str = "8.8.8.8"
    secondary_dns: str = "8.8.4.4"
    connection_timeout: int = 5
    retry_attempts: int = 3
    enable_ipv6: bool = False
    dns_servers: str = "8.8.8.8,8.8.4.4"


@dataclass
class AlertSettings:
    """Alert and notification configuration"""
    enable_sound_alerts: bool = True
    enable_email_alerts: bool = False
    email_server: str = ""
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: str = ""
    email_threshold_ms: int = 1000
    alert_cooldown: int = 60
    # Additional fields that the settings dialog expects
    enable_sound: bool = True
    enable_desktop_notifications: bool = True
    email_notifications: bool = False
    email_recipient_list: list = None
    email_consecutive_failures: int = 3
    email_cooldown_minutes: int = 5
    email_batch_alerts: bool = False
    email_batch_interval_minutes: int = 15
    email_send_reports: bool = False
    email_report_interval_hours: int = 24
    email_subject_template: str = "Network Monitor Alert - {alert_type}"
    alert_types: dict = None
    # SMTP settings (replacing the problematic email_settings string)
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_tls: bool = True
    from_address: str = ""

    def __post_init__(self):
        """Initialize default values for complex fields"""
        if self.email_recipient_list is None:
            self.email_recipient_list = []
        if self.alert_types is None:
            self.alert_types = {
                'device_down': True,
                'high_latency': True,
                'new_device': False,
                'network_change': False
            }


@dataclass
class ApplicationSettings:
    """Complete application settings"""
    scan: ScanSettings
    monitor: MonitorSettings
    interface: InterfaceSettings
    network: NetworkSettings
    alerts: AlertSettings

    def __init__(self):
        self.scan = ScanSettings()
        self.monitor = MonitorSettings()
        self.interface = InterfaceSettings()
        self.network = NetworkSettings()
        self.alerts = AlertSettings()


class SettingsManager:
    """Settings persistence and management"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path.home() / '.network_monitor'
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'settings.json'
        self.settings = ApplicationSettings()
        self.load_settings()

    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)

                # Load each section
                if 'scan' in data:
                    for key, value in data['scan'].items():
                        if hasattr(self.settings.scan, key):
                            setattr(self.settings.scan, key, value)

                if 'monitor' in data:
                    for key, value in data['monitor'].items():
                        if hasattr(self.settings.monitor, key):
                            setattr(self.settings.monitor, key, value)

                if 'interface' in data:
                    for key, value in data['interface'].items():
                        if hasattr(self.settings.interface, key):
                            setattr(self.settings.interface, key, value)

                if 'network' in data:
                    for key, value in data['network'].items():
                        if hasattr(self.settings.network, key):
                            setattr(self.settings.network, key, value)

                if 'alerts' in data:
                    for key, value in data['alerts'].items():
                        if hasattr(self.settings.alerts, key):
                            setattr(self.settings.alerts, key, value)

                return True
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Reset to defaults on error
            self.settings = ApplicationSettings()

        return False

    def save_settings(self) -> bool:
        """Save current settings to file"""
        try:
            data = {
                'scan': asdict(self.settings.scan),
                'monitor': asdict(self.settings.monitor),
                'interface': asdict(self.settings.interface),
                'network': asdict(self.settings.network),
                'alerts': asdict(self.settings.alerts),
                'last_saved': datetime.now().isoformat()
            }

            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def update_setting(self, section: str, key: str, value: Any) -> bool:
        """Update a specific setting"""
        try:
            if hasattr(self.settings, section):
                section_obj = getattr(self.settings, section)
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)
                    return self.save_settings()
                else:
                    print(f"Unknown setting key: {section}.{key}")
                    return False
            else:
                print(f"Unknown settings section: {section}")
                return False
        except Exception as e:
            print(f"Error updating setting {section}.{key}: {e}")
            return False

    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        try:
            if hasattr(self.settings, section):
                section_obj = getattr(self.settings, section)
                if hasattr(section_obj, key):
                    return getattr(section_obj, key)
                else:
                    return default
            else:
                return default
        except Exception as e:
            print(f"Error getting setting {section}.{key}: {e}")
            return default

    def reset_to_defaults(self) -> bool:
        """Reset all settings to default values"""
        try:
            self.settings = ApplicationSettings()
            return self.save_settings()
        except Exception as e:
            print(f"Error resetting settings: {e}")
            return False

    def export_settings(self, file_path: str) -> bool:
        """Export settings to a file"""
        try:
            data = {
                'scan': asdict(self.settings.scan),
                'monitor': asdict(self.settings.monitor),
                'interface': asdict(self.settings.interface),
                'network': asdict(self.settings.network),
                'alerts': asdict(self.settings.alerts),
                'exported': datetime.now().isoformat()
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return False

    def import_settings(self, file_path: str) -> bool:
        """Import settings from a file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Create new settings object and load data
            new_settings = ApplicationSettings()

            if 'scan' in data:
                for key, value in data['scan'].items():
                    if hasattr(new_settings.scan, key):
                        setattr(new_settings.scan, key, value)

            if 'monitor' in data:
                for key, value in data['monitor'].items():
                    if hasattr(new_settings.monitor, key):
                        setattr(new_settings.monitor, key, value)

            if 'interface' in data:
                for key, value in data['interface'].items():
                    if hasattr(new_settings.interface, key):
                        setattr(new_settings.interface, key, value)

            if 'network' in data:
                for key, value in data['network'].items():
                    if hasattr(new_settings.network, key):
                        setattr(new_settings.network, key, value)

            if 'alerts' in data:
                for key, value in data['alerts'].items():
                    if hasattr(new_settings.alerts, key):
                        setattr(new_settings.alerts, key, value)

            # If validation passed, update current settings
            self.settings = new_settings
            return self.save_settings()

        except Exception as e:
            print(f"Error importing settings: {e}")
            return False


# Global settings manager instance
settings_manager = SettingsManager()


# Convenience functions for common operations
def get_theme() -> str:
    """Get current theme setting"""
    return settings_manager.settings.interface.theme


def set_theme(theme: str) -> bool:
    """Set theme setting"""
    return settings_manager.update_setting('interface', 'theme', theme)


def get_window_size() -> tuple:
    """Get window size settings"""
    return (
        settings_manager.settings.interface.window_width,
        settings_manager.settings.interface.window_height
    )


def set_window_size(width: int, height: int) -> bool:
    """Set window size settings"""
    result1 = settings_manager.update_setting('interface', 'window_width', width)
    result2 = settings_manager.update_setting('interface', 'window_height', height)
    return result1 and result2


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
