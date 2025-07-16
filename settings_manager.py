#!/usr/bin/env python3
"""
Settings Dialog for Network Monitor
Comprehensive settings interface with tabbed categories
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from settings import settings_manager, ApplicationSettings
from typing import Dict, Any, Callable


class SettingsDialog:
    """Main settings dialog window with tabbed interface"""

    def __init__(self, parent, callback: Callable = None):
        self.parent = parent
        self.callback = callback
        self.settings = settings_manager.settings
        self.temp_settings = None
        self.setting_vars = {}

        self.create_dialog()
        self.load_current_settings()

    def create_dialog(self):
        """Create the main dialog window"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Network Monitor Settings")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"800x600+{x}+{y}")

        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)

        # Create main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Create tabbed interface
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Add tabs
        self.create_scan_tab()
        self.create_monitor_tab()
        self.create_interface_tab()
        self.create_network_tab()
        self.create_alerts_tab()

        # Create button frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Buttons
        ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults,
            width=120
        ).pack(side="left", padx=5, pady=10)

        ctk.CTkButton(
            button_frame,
            text="Export Settings",
            command=self.export_settings,
            width=120
        ).pack(side="left", padx=5, pady=10)

        ctk.CTkButton(
            button_frame,
            text="Import Settings",
            command=self.import_settings,
            width=120
        ).pack(side="left", padx=5, pady=10)

        # Right side buttons
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=100
        ).pack(side="right", padx=5, pady=10)

        ctk.CTkButton(
            button_frame,
            text="Apply",
            command=self.apply_settings,
            width=100
        ).pack(side="right", padx=5, pady=10)

        ctk.CTkButton(
            button_frame,
            text="OK",
            command=self.ok,
            width=100
        ).pack(side="right", padx=5, pady=10)

    def create_scan_tab(self):
        """Create scanning settings tab"""
        tab = self.tabview.add("Scanning")

        # Scrollable frame for settings
        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Network Scanning Settings")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Max Workers
        self.create_setting_row(
            scroll_frame, 0,
            "Max Workers:",
            "Maximum number of concurrent scanning threads",
            "scan_max_workers",
            "spinbox",
            range_values=(1, 100)
        )

        # Timeout
        self.create_setting_row(
            scroll_frame, 1,
            "Timeout (seconds):",
            "Network connection timeout",
            "scan_timeout",
            "spinbox",
            range_values=(1, 30),
            increment=0.5
        )

        # Ping Timeout
        self.create_setting_row(
            scroll_frame, 2,
            "Ping Timeout (ms):",
            "Ping timeout in milliseconds",
            "scan_ping_timeout",
            "spinbox",
            range_values=(100, 5000),
            increment=100
        )

        # Enable Scapy
        self.create_setting_row(
            scroll_frame, 3,
            "Enable Scapy:",
            "Use Scapy for advanced network scanning",
            "scan_enable_scapy",
            "switch"
        )

        # Enable MAC Lookup
        self.create_setting_row(
            scroll_frame, 4,
            "Enable MAC Lookup:",
            "Look up device manufacturers from MAC addresses",
            "scan_enable_mac_lookup",
            "switch"
        )

        # Auto Detect Network
        self.create_setting_row(
            scroll_frame, 5,
            "Auto-Detect Network:",
            "Automatically detect network range on startup",
            "scan_auto_detect_network",
            "switch"
        )

        # Default Network Range
        self.create_setting_row(
            scroll_frame, 6,
            "Default Network Range:",
            "Default network range for scanning",
            "scan_default_network_range",
            "entry",
            placeholder="192.168.1.0/24"
        )

    def create_monitor_tab(self):
        """Create monitoring settings tab"""
        tab = self.tabview.add("Monitoring")

        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Live Monitoring Settings")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Update Interval
        self.create_setting_row(
            scroll_frame, 0,
            "Update Interval (seconds):",
            "How often to ping monitored devices",
            "monitor_update_interval",
            "spinbox",
            range_values=(1, 60)
        )

        # Buffer Size
        self.create_setting_row(
            scroll_frame, 1,
            "Buffer Size:",
            "Number of ping results to keep in memory",
            "monitor_buffer_size",
            "spinbox",
            range_values=(10, 1000),
            increment=10
        )

        # Graph Refresh Rate
        self.create_setting_row(
            scroll_frame, 2,
            "Graph Refresh Rate (seconds):",
            "How often to update monitoring graphs",
            "monitor_graph_refresh_rate",
            "spinbox",
            range_values=(1, 10)
        )

        # Max Monitoring Devices
        self.create_setting_row(
            scroll_frame, 3,
            "Max Monitoring Devices:",
            "Maximum number of devices to monitor simultaneously",
            "monitor_max_monitoring_devices",
            "spinbox",
            range_values=(1, 50)
        )

        # Alert Threshold
        self.create_setting_row(
            scroll_frame, 4,
            "Alert Threshold (ms):",
            "Latency threshold for problem alerts",
            "monitor_alert_threshold_ms",
            "spinbox",
            range_values=(100, 5000),
            increment=50
        )

        # Enable Alerts
        self.create_setting_row(
            scroll_frame, 5,
            "Enable Alerts:",
            "Show alerts for high latency and connection issues",
            "monitor_enable_alerts",
            "switch"
        )

        # Auto Start Monitoring
        self.create_setting_row(
            scroll_frame, 6,
            "Auto-Start Monitoring:",
            "Automatically start monitoring selected devices",
            "monitor_auto_start_monitoring",
            "switch"
        )

    def create_interface_tab(self):
        """Create interface settings tab"""
        tab = self.tabview.add("Interface")

        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="User Interface Settings")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Theme
        self.create_setting_row(
            scroll_frame, 0,
            "Theme:",
            "Application color theme",
            "interface_theme",
            "combobox",
            values=["dark", "light"]
        )

        # Window Width
        self.create_setting_row(
            scroll_frame, 1,
            "Window Width:",
            "Default window width",
            "interface_window_width",
            "spinbox",
            range_values=(800, 2000),
            increment=50
        )

        # Window Height
        self.create_setting_row(
            scroll_frame, 2,
            "Window Height:",
            "Default window height",
            "interface_window_height",
            "spinbox",
            range_values=(600, 1500),
            increment=50
        )

        # Sidebar Width
        self.create_setting_row(
            scroll_frame, 3,
            "Sidebar Width:",
            "Width of the sidebar panel",
            "interface_sidebar_width",
            "spinbox",
            range_values=(200, 400),
            increment=20
        )

        # Remember Window Size
        self.create_setting_row(
            scroll_frame, 4,
            "Remember Window Size:",
            "Save and restore window size on startup",
            "interface_remember_window_size",
            "switch"
        )

        # Auto Save Reports
        self.create_setting_row(
            scroll_frame, 5,
            "Auto-Save Reports:",
            "Automatically save scan reports",
            "interface_auto_save_reports",
            "switch"
        )

        # Show Tooltips
        self.create_setting_row(
            scroll_frame, 6,
            "Show Tooltips:",
            "Display helpful tooltips on hover",
            "interface_show_tooltips",
            "switch"
        )

        # Confirm Exit
        self.create_setting_row(
            scroll_frame, 7,
            "Confirm Exit:",
            "Show confirmation dialog when closing",
            "interface_confirm_exit",
            "switch"
        )

    def create_network_tab(self):
        """Create network settings tab"""
        tab = self.tabview.add("Network")

        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Network Configuration")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Preferred Interface
        self.create_setting_row(
            scroll_frame, 0,
            "Preferred Interface:",
            "Network interface to prefer for scanning",
            "network_preferred_interface",
            "entry",
            placeholder="auto"
        )

        # Enable IPv6
        self.create_setting_row(
            scroll_frame, 1,
            "Enable IPv6:",
            "Include IPv6 addresses in scanning",
            "network_enable_ipv6",
            "switch"
        )

        # Connection Timeout
        self.create_setting_row(
            scroll_frame, 2,
            "Connection Timeout (seconds):",
            "Timeout for network connections",
            "network_connection_timeout",
            "spinbox",
            range_values=(1, 30)
        )

        # Retry Attempts
        self.create_setting_row(
            scroll_frame, 3,
            "Retry Attempts:",
            "Number of retry attempts for failed connections",
            "network_retry_attempts",
            "spinbox",
            range_values=(1, 10)
        )

        # DNS Servers section
        dns_frame = ctk.CTkFrame(scroll_frame)
        dns_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        dns_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(dns_frame, text="DNS Servers:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )

        self.dns_text = ctk.CTkTextbox(dns_frame, height=60)
        self.dns_text.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.setting_vars["network_dns_servers"] = self.dns_text

    def create_alerts_tab(self):
        """Create alerts settings tab"""
        tab = self.tabview.add("Alerts")

        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Alert & Notification Settings")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Enable Sound
        self.create_setting_row(
            scroll_frame, 0,
            "Enable Sound:",
            "Play sound alerts",
            "alerts_enable_sound",
            "switch"
        )

        # Enable Desktop Notifications
        self.create_setting_row(
            scroll_frame, 1,
            "Desktop Notifications:",
            "Show desktop notifications",
            "alerts_enable_desktop_notifications",
            "switch"
        )

        # Email Notifications
        self.create_setting_row(
            scroll_frame, 2,
            "Email Notifications:",
            "Send email alerts",
            "alerts_email_notifications",
            "switch"
        )

        # Alert Types section
        alert_types_frame = ctk.CTkFrame(scroll_frame)
        alert_types_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(alert_types_frame, text="Alert Types:", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=5, pady=5
        )

        alert_types = [
            ("Device Down", "alerts_device_down"),
            ("High Latency", "alerts_high_latency"),
            ("New Device", "alerts_new_device"),
            ("Network Change", "alerts_network_change")
        ]

        for i, (label, key) in enumerate(alert_types):
            var = tk.BooleanVar()
            self.setting_vars[key] = var

            ctk.CTkCheckBox(
                alert_types_frame,
                text=label,
                variable=var
            ).pack(anchor="w", padx=20, pady=2)

    def create_setting_row(self, parent, row, label_text, description, key, widget_type, **kwargs):
        """Create a standardized setting row"""
        # Label
        label = ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(weight="bold"))
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

        # Widget
        if widget_type == "entry":
            var = tk.StringVar()
            widget = ctk.CTkEntry(parent, textvariable=var, placeholder_text=kwargs.get("placeholder", ""))

        elif widget_type == "spinbox":
            var = tk.DoubleVar() if kwargs.get("increment", 1) != 1 else tk.IntVar()
            widget = ctk.CTkEntry(parent, textvariable=var, width=100)
            # Note: CTk doesn't have spinbox, using entry with validation

        elif widget_type == "switch":
            var = tk.BooleanVar()
            widget = ctk.CTkSwitch(parent, text="", variable=var)

        elif widget_type == "combobox":
            var = tk.StringVar()
            widget = ctk.CTkComboBox(parent, variable=var, values=kwargs.get("values", []))

        widget.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.setting_vars[key] = var

        # Description
        desc_label = ctk.CTkLabel(parent, text=description, font=ctk.CTkFont(size=10))
        desc_label.grid(row=row, column=2, sticky="w", padx=5, pady=5)

        # Configure column weights
        parent.grid_columnconfigure(1, weight=1)

    def load_current_settings(self):
        """Load current settings into the dialog"""
        # Scan settings
        self.setting_vars["scan_max_workers"].set(self.settings.scan.max_workers)
        self.setting_vars["scan_timeout"].set(self.settings.scan.timeout)
        self.setting_vars["scan_ping_timeout"].set(self.settings.scan.ping_timeout)
        self.setting_vars["scan_enable_scapy"].set(self.settings.scan.enable_scapy)
        self.setting_vars["scan_enable_mac_lookup"].set(self.settings.scan.enable_mac_lookup)
        self.setting_vars["scan_auto_detect_network"].set(self.settings.scan.auto_detect_network)
        self.setting_vars["scan_default_network_range"].set(self.settings.scan.default_network_range)

        # Monitor settings
        self.setting_vars["monitor_update_interval"].set(self.settings.monitor.update_interval)
        self.setting_vars["monitor_buffer_size"].set(self.settings.monitor.buffer_size)
        self.setting_vars["monitor_graph_refresh_rate"].set(self.settings.monitor.graph_refresh_rate)
        self.setting_vars["monitor_max_monitoring_devices"].set(self.settings.monitor.max_monitoring_devices)
        self.setting_vars["monitor_alert_threshold_ms"].set(self.settings.monitor.alert_threshold_ms)
        self.setting_vars["monitor_enable_alerts"].set(self.settings.monitor.enable_alerts)
        self.setting_vars["monitor_auto_start_monitoring"].set(self.settings.monitor.auto_start_monitoring)

        # Interface settings
        self.setting_vars["interface_theme"].set(self.settings.interface.theme)
        self.setting_vars["interface_window_width"].set(self.settings.interface.window_width)
        self.setting_vars["interface_window_height"].set(self.settings.interface.window_height)
        self.setting_vars["interface_sidebar_width"].set(self.settings.interface.sidebar_width)
        self.setting_vars["interface_remember_window_size"].set(self.settings.interface.remember_window_size)
        self.setting_vars["interface_auto_save_reports"].set(self.settings.interface.auto_save_reports)
        self.setting_vars["interface_show_tooltips"].set(self.settings.interface.show_tooltips)
        self.setting_vars["interface_confirm_exit"].set(self.settings.interface.confirm_exit)

        # Network settings
        self.setting_vars["network_preferred_interface"].set(self.settings.network.preferred_interface)
        self.setting_vars["network_enable_ipv6"].set(self.settings.network.enable_ipv6)
        self.setting_vars["network_connection_timeout"].set(self.settings.network.connection_timeout)
        self.setting_vars["network_retry_attempts"].set(self.settings.network.retry_attempts)

        # DNS servers
        dns_text = "\n".join(self.settings.network.dns_servers)
        self.setting_vars["network_dns_servers"].delete("1.0", "end")
        self.setting_vars["network_dns_servers"].insert("1.0", dns_text)

        # Alert settings
        self.setting_vars["alerts_enable_sound"].set(self.settings.alerts.enable_sound)
        self.setting_vars["alerts_enable_desktop_notifications"].set(self.settings.alerts.enable_desktop_notifications)
        self.setting_vars["alerts_email_notifications"].set(self.settings.alerts.email_notifications)

        # Alert types
        self.setting_vars["alerts_device_down"].set(self.settings.alerts.alert_types["device_down"])
        self.setting_vars["alerts_high_latency"].set(self.settings.alerts.alert_types["high_latency"])
        self.setting_vars["alerts_new_device"].set(self.settings.alerts.alert_types["new_device"])
        self.setting_vars["alerts_network_change"].set(self.settings.alerts.alert_types["network_change"])

    def apply_settings(self):
        """Apply settings without closing dialog"""
        if self.save_current_settings():
            if self.callback:
                self.callback(settings_manager.settings)
            messagebox.showinfo("Settings", "Settings applied successfully!")

    def save_current_settings(self):
        """Save current dialog values to settings"""
        try:
            # Scan settings
            settings_manager.update_setting("scan", "max_workers", self.setting_vars["scan_max_workers"].get())
            settings_manager.update_setting("scan", "timeout", self.setting_vars["scan_timeout"].get())
            settings_manager.update_setting("scan", "ping_timeout", self.setting_vars["scan_ping_timeout"].get())
            settings_manager.update_setting("scan", "enable_scapy", self.setting_vars["scan_enable_scapy"].get())
            settings_manager.update_setting("scan", "enable_mac_lookup", self.setting_vars["scan_enable_mac_lookup"].get())
            settings_manager.update_setting("scan", "auto_detect_network", self.setting_vars["scan_auto_detect_network"].get())
            settings_manager.update_setting("scan", "default_network_range", self.setting_vars["scan_default_network_range"].get())

            # Monitor settings
            settings_manager.update_setting("monitor", "update_interval", self.setting_vars["monitor_update_interval"].get())
            settings_manager.update_setting("monitor", "buffer_size", self.setting_vars["monitor_buffer_size"].get())
            settings_manager.update_setting("monitor", "graph_refresh_rate", self.setting_vars["monitor_graph_refresh_rate"].get())
            settings_manager.update_setting("monitor", "max_monitoring_devices", self.setting_vars["monitor_max_monitoring_devices"].get())
            settings_manager.update_setting("monitor", "alert_threshold_ms", self.setting_vars["monitor_alert_threshold_ms"].get())
            settings_manager.update_setting("monitor", "enable_alerts", self.setting_vars["monitor_enable_alerts"].get())
            settings_manager.update_setting("monitor", "auto_start_monitoring", self.setting_vars["monitor_auto_start_monitoring"].get())

            # Interface settings
            settings_manager.update_setting("interface", "theme", self.setting_vars["interface_theme"].get())
            settings_manager.update_setting("interface", "window_width", self.setting_vars["interface_window_width"].get())
            settings_manager.update_setting("interface", "window_height", self.setting_vars["interface_window_height"].get())
            settings_manager.update_setting("interface", "sidebar_width", self.setting_vars["interface_sidebar_width"].get())
            settings_manager.update_setting("interface", "remember_window_size", self.setting_vars["interface_remember_window_size"].get())
            settings_manager.update_setting("interface", "auto_save_reports", self.setting_vars["interface_auto_save_reports"].get())
            settings_manager.update_setting("interface", "show_tooltips", self.setting_vars["interface_show_tooltips"].get())
            settings_manager.update_setting("interface", "confirm_exit", self.setting_vars["interface_confirm_exit"].get())

            # Network settings
            settings_manager.update_setting("network", "preferred_interface", self.setting_vars["network_preferred_interface"].get())
            settings_manager.update_setting("network", "enable_ipv6", self.setting_vars["network_enable_ipv6"].get())
            settings_manager.update_setting("network", "connection_timeout", self.setting_vars["network_connection_timeout"].get())
            settings_manager.update_setting("network", "retry_attempts", self.setting_vars["network_retry_attempts"].get())

            # DNS servers
            dns_text = self.setting_vars["network_dns_servers"].get("1.0", "end-1c")
            dns_servers = [line.strip() for line in dns_text.split("\n") if line.strip()]
            settings_manager.update_setting("network", "dns_servers", dns_servers)

            # Alert settings
            settings_manager.update_setting("alerts", "enable_sound", self.setting_vars["alerts_enable_sound"].get())
            settings_manager.update_setting("alerts", "enable_desktop_notifications", self.setting_vars["alerts_enable_desktop_notifications"].get())
            settings_manager.update_setting("alerts", "email_notifications", self.setting_vars["alerts_email_notifications"].get())

            # Alert types
            alert_types = {
                "device_down": self.setting_vars["alerts_device_down"].get(),
                "high_latency": self.setting_vars["alerts_high_latency"].get(),
                "new_device": self.setting_vars["alerts_new_device"].get(),
                "network_change": self.setting_vars["alerts_network_change"].get()
            }
            settings_manager.update_setting("alerts", "alert_types", alert_types)

            # Save to file
            settings_manager.save_settings()
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            return False

    def ok(self):
        """OK button - save and close"""
        if self.save_current_settings():
            if self.callback:
                self.callback(settings_manager.settings)
            self.dialog.destroy()

    def cancel(self):
        """Cancel button - close without saving"""
        self.dialog.destroy()

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            settings_manager.reset_to_defaults()
            self.load_current_settings()
            messagebox.showinfo("Settings", "Settings reset to defaults!")

    def export_settings(self):
        """Export settings to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Settings"
        )
        if filename:
            if settings_manager.export_settings(filename):
                messagebox.showinfo("Export", f"Settings exported to {filename}")
            else:
                messagebox.showerror("Export", "Failed to export settings")

    def import_settings(self):
        """Import settings from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Settings"
        )
        if filename:
            if settings_manager.import_settings(filename):
                self.load_current_settings()
                messagebox.showinfo("Import", "Settings imported successfully!")
            else:
                messagebox.showerror("Import", "Failed to import settings")


def show_settings_dialog(parent, callback=None):
    """Convenience function to show settings dialog"""
    return SettingsDialog(parent, callback)
