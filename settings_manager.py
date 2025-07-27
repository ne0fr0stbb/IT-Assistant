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
from email_tester import email_tester
from email_test_dialog import show_email_test_results, show_email_test_progress


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
        self.dialog.geometry("900x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"900x700+{x}+{y}")

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
        self.create_profile_tab()
        self.create_alerts_tab()

        # Create button frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Buttons
        reset_btn = ctk.CTkButton(
            button_frame,
            text="Reset to Defaults",
            command=self.reset_to_defaults,
            width=120
        )
        reset_btn.pack(side="left", padx=5, pady=10)

        export_btn = ctk.CTkButton(
            button_frame,
            text="Export Settings",
            command=self.export_settings,
            width=120
        )
        export_btn.pack(side="left", padx=5, pady=10)

        import_btn = ctk.CTkButton(
            button_frame,
            text="Import Settings",
            command=self.import_settings,
            width=120
        )
        import_btn.pack(side="left", padx=5, pady=10)

        # Right side buttons
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=100
        )
        cancel_btn.pack(side="right", padx=5, pady=10)

        apply_btn = ctk.CTkButton(
            button_frame,
            text="Apply",
            command=self.apply_settings,
            width=100
        )
        apply_btn.pack(side="right", padx=5, pady=10)

        ok_btn = ctk.CTkButton(
            button_frame,
            text="OK",
            command=self.ok,
            width=100
        )
        ok_btn.pack(side="right", padx=5, pady=10)

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

    def create_profile_tab(self):
        """Create profile settings tab"""
        tab = self.tabview.add("Profile")

        scroll_frame = ctk.CTkScrollableFrame(tab, label_text="Profile Settings")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Default Profile
        self.create_setting_row(
            scroll_frame, 0,
            "Default Profile:",
            "Select a default profile to load on startup",
            "profile_default",
            "combobox",
            values=self.load_profiles()
        )

        # Save the selected default profile
        selected_profile_var = self.setting_vars["profile_default"]
        selected_profile_var.trace_add("write", self.save_default_profile)

    def save_default_profile(self, *args):
        """Save profile_default setting when updated"""
        selected_profile = self.setting_vars["profile_default"].get()
        settings_manager.update_setting('interface', 'default_profile', selected_profile)

    def load_profiles(self):
        """Load profile names from the database or file"""
        try:
            import sqlite3
            conn = sqlite3.connect('network.db')
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT Profile FROM Profile ORDER BY Profile")
            profiles = [row[0] for row in cursor.fetchall()]
            conn.close()
            # Add option for no default profile
            return ["[No default profile]"] + profiles if profiles else ["[No default profile]"]
        except Exception:
            return ["[No default profile]"]

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

        # Email Configuration section
        email_config_frame = ctk.CTkFrame(scroll_frame)
        email_config_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        email_config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(email_config_frame, text="Email Configuration:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5
        )

        # SMTP Server
        self.create_email_setting_row(
            email_config_frame, 1,
            "SMTP Server:",
            "SMTP server address",
            "alerts_smtp_server",
            "entry",
            placeholder="smtp.gmail.com"
        )

        # SMTP Port
        self.create_email_setting_row(
            email_config_frame, 2,
            "SMTP Port:",
            "SMTP server port",
            "alerts_smtp_port",
            "spinbox",
            range_values=(1, 65535)
        )

        # Username
        self.create_email_setting_row(
            email_config_frame, 3,
            "Username:",
            "SMTP username/email",
            "alerts_smtp_username",
            "entry",
            placeholder="user@example.com"
        )

        # Password
        self.create_email_setting_row(
            email_config_frame, 4,
            "Password:",
            "SMTP password",
            "alerts_smtp_password",
            "entry",
            show="*"
        )

        # Use TLS
        self.create_email_setting_row(
            email_config_frame, 5,
            "Use TLS:",
            "Enable TLS encryption",
            "alerts_smtp_tls",
            "switch"
        )

        # From Address
        self.create_email_setting_row(
            email_config_frame, 6,
            "From Address:",
            "Sender email address",
            "alerts_from_address",
            "entry",
            placeholder="monitor@example.com"
        )

        # Test Email Configuration button
        test_email_btn = ctk.CTkButton(
            email_config_frame,
            text="Test Email Configuration",
            command=self.test_email_configuration,
            width=200
        )
        test_email_btn.grid(row=7, column=0, columnspan=3, pady=10)

        # Email Recipients
        email_recipients_frame = ctk.CTkFrame(scroll_frame)
        email_recipients_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        email_recipients_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(email_recipients_frame, text="Email Recipients:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )

        self.recipients_text = ctk.CTkTextbox(email_recipients_frame, height=80)
        self.recipients_text.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.setting_vars["alerts_email_recipients"] = self.recipients_text

        ctk.CTkLabel(email_recipients_frame, text="One email per line", font=ctk.CTkFont(size=10)).grid(
            row=1, column=1, sticky="w", padx=5, pady=2
        )

        # Email Alert Thresholds section
        email_thresholds_frame = ctk.CTkFrame(scroll_frame)
        email_thresholds_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        email_thresholds_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(email_thresholds_frame, text="Email Alert Thresholds:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5
        )

        # Email Threshold
        self.create_email_setting_row(
            email_thresholds_frame, 1,
            "Email Threshold (ms):",
            "Latency threshold for email alerts",
            "alerts_email_threshold_ms",
            "spinbox",
            range_values=(100, 10000),
            increment=100
        )

        # Consecutive Failures
        self.create_email_setting_row(
            email_thresholds_frame, 2,
            "Consecutive Failures:",
            "Number of consecutive failures before email",
            "alerts_email_consecutive_failures",
            "spinbox",
            range_values=(1, 10)
        )

        # Cooldown Period
        self.create_email_setting_row(
            email_thresholds_frame, 3,
            "Cooldown Period (min):",
            "Minutes between emails for same device",
            "alerts_email_cooldown_minutes",
            "spinbox",
            range_values=(1, 120),
            increment=5
        )

        # Batch Alerts
        self.create_email_setting_row(
            email_thresholds_frame, 4,
            "Batch Alerts:",
            "Combine multiple alerts into single email",
            "alerts_email_batch_alerts",
            "switch"
        )

        # Batch Interval
        self.create_email_setting_row(
            email_thresholds_frame, 5,
            "Batch Interval (min):",
            "Minutes to wait before sending batched alerts",
            "alerts_email_batch_interval_minutes",
            "spinbox",
            range_values=(1, 60)
        )

        # Send Reports
        self.create_email_setting_row(
            email_thresholds_frame, 6,
            "Send Reports:",
            "Send periodic monitoring reports",
            "alerts_email_send_reports",
            "switch"
        )

        # Report Interval
        self.create_email_setting_row(
            email_thresholds_frame, 7,
            "Report Interval (hours):",
            "Hours between periodic reports",
            "alerts_email_report_interval_hours",
            "spinbox",
            range_values=(1, 168),
            increment=1
        )

        # Subject Template
        self.create_email_setting_row(
            email_thresholds_frame, 8,
            "Subject Template:",
            "Email subject template ({alert_type} will be replaced)",
            "alerts_email_subject_template",
            "entry",
            placeholder="[Network Monitor] Alert: {alert_type}"
        )

        # Alert Types section
        alert_types_frame = ctk.CTkFrame(scroll_frame)
        alert_types_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(alert_types_frame, text="Alert Types:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5
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
            ).grid(row=i+1, column=0, sticky="w", padx=20, pady=2)

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
            # Use StringVar to avoid type conversion errors
            var = tk.StringVar()
            # Set default value based on range
            range_values = kwargs.get("range_values", (0, 100))
            default_val = kwargs.get("default", range_values[0])
            var.set(str(default_val))
            
            # Create entry with validation
            widget = ctk.CTkEntry(parent, textvariable=var, width=100)
            
            # Add validation to ensure numeric input
            def validate_numeric(value):
                if value == "":
                    return True  # Allow empty for typing
                try:
                    int(value)
                    return True
                except ValueError:
                    return False
            
            vcmd = (parent.register(validate_numeric), '%P')
            widget.configure(validate="key", validatecommand=vcmd)
            
            # Store the variable type info for later conversion
            var._var_type = "int"
            var._default = default_val

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

    def create_email_setting_row(self, parent, row, label_text, description, key, widget_type, **kwargs):
        """Create a standardized email setting row"""
        # Label
        label = ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(weight="bold"))
        label.grid(row=row, column=0, sticky="w", padx=5, pady=5)

        # Widget
        if widget_type == "entry":
            var = tk.StringVar()
            show = kwargs.get("show", None)
            widget = ctk.CTkEntry(parent, textvariable=var, 
                                placeholder_text=kwargs.get("placeholder", ""),
                                show=show if show else None)

        elif widget_type == "spinbox":
            # Use StringVar to avoid type conversion errors
            var = tk.StringVar()
            # Set default value based on range
            range_values = kwargs.get("range_values", (0, 100))
            default_val = kwargs.get("default", range_values[0])
            var.set(str(default_val))
            
            # Create entry with validation
            widget = ctk.CTkEntry(parent, textvariable=var, width=100)
            
            # Add validation to ensure numeric input
            def validate_numeric(value):
                if value == "":
                    return True  # Allow empty for typing
                try:
                    int(value)
                    return True
                except ValueError:
                    return False
            
            vcmd = (parent.register(validate_numeric), '%P')
            widget.configure(validate="key", validatecommand=vcmd)
            
            # Store the variable type info for later conversion
            var._var_type = "int"
            var._default = default_val

        elif widget_type == "switch":
            var = tk.BooleanVar()
            widget = ctk.CTkSwitch(parent, text="", variable=var)

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

        # Email configuration settings
        self.setting_vars["alerts_smtp_server"].set(self.settings.alerts.smtp_server)
        self.setting_vars["alerts_smtp_port"].set(self.settings.alerts.smtp_port)
        self.setting_vars["alerts_smtp_username"].set(self.settings.alerts.smtp_username)
        self.setting_vars["alerts_smtp_password"].set(self.settings.alerts.smtp_password)
        self.setting_vars["alerts_smtp_tls"].set(self.settings.alerts.smtp_tls)
        self.setting_vars["alerts_from_address"].set(self.settings.alerts.from_address)

        # Email recipients
        recipients_text = "\n".join(self.settings.alerts.email_recipient_list)
        self.setting_vars["alerts_email_recipients"].delete("1.0", "end")
        self.setting_vars["alerts_email_recipients"].insert("1.0", recipients_text)

        # Email alert thresholds
        self.setting_vars["alerts_email_threshold_ms"].set(self.settings.alerts.email_threshold_ms)
        self.setting_vars["alerts_email_consecutive_failures"].set(self.settings.alerts.email_consecutive_failures)
        self.setting_vars["alerts_email_cooldown_minutes"].set(self.settings.alerts.email_cooldown_minutes)
        self.setting_vars["alerts_email_batch_alerts"].set(self.settings.alerts.email_batch_alerts)
        self.setting_vars["alerts_email_batch_interval_minutes"].set(self.settings.alerts.email_batch_interval_minutes)
        self.setting_vars["alerts_email_send_reports"].set(self.settings.alerts.email_send_reports)
        self.setting_vars["alerts_email_report_interval_hours"].set(self.settings.alerts.email_report_interval_hours)
        self.setting_vars["alerts_email_subject_template"].set(self.settings.alerts.email_subject_template)

        # Alert types
        self.setting_vars["alerts_device_down"].set(self.settings.alerts.alert_types["device_down"])
        self.setting_vars["alerts_high_latency"].set(self.settings.alerts.alert_types["high_latency"])
        self.setting_vars["alerts_new_device"].set(self.settings.alerts.alert_types["new_device"])
        self.setting_vars["alerts_network_change"].set(self.settings.alerts.alert_types["network_change"])

        # Profile settings
        if "profile_default" in self.setting_vars:
            default_profile = self.settings.interface.default_profile or "[No default profile]"
            self.setting_vars["profile_default"].set(default_profile)

    def apply_settings(self):
        """Apply settings without closing dialog"""
        if self.save_current_settings():
            if self.callback:
                self.callback(settings_manager.settings)
            messagebox.showinfo("Settings", "Settings applied successfully!")

    def save_current_settings(self):
        """Save current dialog values to settings"""
        try:
            # Helper function to get numeric value from StringVar
            def get_numeric_value(var):
                val = var.get()
                if hasattr(var, '_var_type') and var._var_type == "int":
                    return int(val) if val else getattr(var, '_default', 0)
                return val
            
            # Scan settings
            settings_manager.update_setting("scan", "max_workers", get_numeric_value(self.setting_vars["scan_max_workers"]))
            settings_manager.update_setting("scan", "timeout", get_numeric_value(self.setting_vars["scan_timeout"]))
            settings_manager.update_setting("scan", "ping_timeout", get_numeric_value(self.setting_vars["scan_ping_timeout"]))
            settings_manager.update_setting("scan", "enable_scapy", self.setting_vars["scan_enable_scapy"].get())
            settings_manager.update_setting("scan", "enable_mac_lookup", self.setting_vars["scan_enable_mac_lookup"].get())
            settings_manager.update_setting("scan", "auto_detect_network", self.setting_vars["scan_auto_detect_network"].get())
            settings_manager.update_setting("scan", "default_network_range", self.setting_vars["scan_default_network_range"].get())

            # Monitor settings
            settings_manager.update_setting("monitor", "update_interval", get_numeric_value(self.setting_vars["monitor_update_interval"]))
            settings_manager.update_setting("monitor", "buffer_size", get_numeric_value(self.setting_vars["monitor_buffer_size"]))
            settings_manager.update_setting("monitor", "graph_refresh_rate", get_numeric_value(self.setting_vars["monitor_graph_refresh_rate"]))
            settings_manager.update_setting("monitor", "max_monitoring_devices", get_numeric_value(self.setting_vars["monitor_max_monitoring_devices"]))
            settings_manager.update_setting("monitor", "alert_threshold_ms", get_numeric_value(self.setting_vars["monitor_alert_threshold_ms"]))
            settings_manager.update_setting("monitor", "enable_alerts", self.setting_vars["monitor_enable_alerts"].get())
            settings_manager.update_setting("monitor", "auto_start_monitoring", self.setting_vars["monitor_auto_start_monitoring"].get())

            # Interface settings
            settings_manager.update_setting("interface", "theme", self.setting_vars["interface_theme"].get())
            settings_manager.update_setting("interface", "window_width", get_numeric_value(self.setting_vars["interface_window_width"]))
            settings_manager.update_setting("interface", "window_height", get_numeric_value(self.setting_vars["interface_window_height"]))
            settings_manager.update_setting("interface", "sidebar_width", get_numeric_value(self.setting_vars["interface_sidebar_width"]))
            settings_manager.update_setting("interface", "remember_window_size", self.setting_vars["interface_remember_window_size"].get())
            settings_manager.update_setting("interface", "auto_save_reports", self.setting_vars["interface_auto_save_reports"].get())
            settings_manager.update_setting("interface", "show_tooltips", self.setting_vars["interface_show_tooltips"].get())
            settings_manager.update_setting("interface", "confirm_exit", self.setting_vars["interface_confirm_exit"].get())

            # Network settings
            settings_manager.update_setting("network", "preferred_interface", self.setting_vars["network_preferred_interface"].get())
            settings_manager.update_setting("network", "enable_ipv6", self.setting_vars["network_enable_ipv6"].get())
            settings_manager.update_setting("network", "connection_timeout", get_numeric_value(self.setting_vars["network_connection_timeout"]))
            settings_manager.update_setting("network", "retry_attempts", get_numeric_value(self.setting_vars["network_retry_attempts"]))

            # DNS servers
            dns_text = self.setting_vars["network_dns_servers"].get("1.0", "end-1c")
            dns_servers = [line.strip() for line in dns_text.split("\n") if line.strip()]
            settings_manager.update_setting("network", "dns_servers", dns_servers)

            # Alert settings
            settings_manager.update_setting("alerts", "enable_sound", self.setting_vars["alerts_enable_sound"].get())
            settings_manager.update_setting("alerts", "enable_desktop_notifications", self.setting_vars["alerts_enable_desktop_notifications"].get())
            settings_manager.update_setting("alerts", "email_notifications", self.setting_vars["alerts_email_notifications"].get())

            # Email configuration settings - save as individual properties
            settings_manager.update_setting("alerts", "smtp_server", self.setting_vars["alerts_smtp_server"].get())
            settings_manager.update_setting("alerts", "smtp_port", get_numeric_value(self.setting_vars["alerts_smtp_port"]))
            settings_manager.update_setting("alerts", "smtp_username", self.setting_vars["alerts_smtp_username"].get())
            settings_manager.update_setting("alerts", "smtp_password", self.setting_vars["alerts_smtp_password"].get())
            settings_manager.update_setting("alerts", "smtp_tls", self.setting_vars["alerts_smtp_tls"].get())
            settings_manager.update_setting("alerts", "from_address", self.setting_vars["alerts_from_address"].get())

            # Email recipients
            recipients_text = self.setting_vars["alerts_email_recipients"].get("1.0", "end-1c")
            recipients_list = [line.strip() for line in recipients_text.split("\n") if line.strip()]
            settings_manager.update_setting("alerts", "email_recipient_list", recipients_list)

            # Email alert thresholds
            settings_manager.update_setting("alerts", "email_threshold_ms", get_numeric_value(self.setting_vars["alerts_email_threshold_ms"]))
            settings_manager.update_setting("alerts", "email_consecutive_failures", get_numeric_value(self.setting_vars["alerts_email_consecutive_failures"]))
            settings_manager.update_setting("alerts", "email_cooldown_minutes", get_numeric_value(self.setting_vars["alerts_email_cooldown_minutes"]))
            settings_manager.update_setting("alerts", "email_batch_alerts", self.setting_vars["alerts_email_batch_alerts"].get())
            settings_manager.update_setting("alerts", "email_batch_interval_minutes", get_numeric_value(self.setting_vars["alerts_email_batch_interval_minutes"]))
            settings_manager.update_setting("alerts", "email_send_reports", self.setting_vars["alerts_email_send_reports"].get())
            settings_manager.update_setting("alerts", "email_report_interval_hours", get_numeric_value(self.setting_vars["alerts_email_report_interval_hours"]))
            settings_manager.update_setting("alerts", "email_subject_template", self.setting_vars["alerts_email_subject_template"].get())

            # Alert types
            alert_types = {
                "device_down": self.setting_vars["alerts_device_down"].get(),
                "high_latency": self.setting_vars["alerts_high_latency"].get(),
                "new_device": self.setting_vars["alerts_new_device"].get(),
                "network_change": self.setting_vars["alerts_network_change"].get()
            }
            settings_manager.update_setting("alerts", "alert_types", alert_types)

            # Profile settings
            if "profile_default" in self.setting_vars:
                profile_default = self.setting_vars["profile_default"].get()
                if profile_default == "[No default profile]":
                    profile_default = ""
                settings_manager.update_setting("interface", "default_profile", profile_default)

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
    
    def test_email_configuration(self):
        """Test the current email configuration"""
        try:
            # Check if test is already in progress
            if email_tester.is_test_in_progress():
                messagebox.showwarning("Test in Progress", "Email test is already in progress. Please wait for it to complete.")
                return
            
            # Get current email configuration from dialog
            email_config = {
                "smtp_server": self.setting_vars["alerts_smtp_server"].get(),
                "smtp_port": int(self.setting_vars["alerts_smtp_port"].get()) if self.setting_vars["alerts_smtp_port"].get() else 587,
                "username": self.setting_vars["alerts_smtp_username"].get(),
                "password": self.setting_vars["alerts_smtp_password"].get(),
                "use_tls": self.setting_vars["alerts_smtp_tls"].get(),
                "use_ssl": False,
                "from_address": self.setting_vars["alerts_from_address"].get(),
                "from_name": "Network Monitor"
            }
            
            # Get recipients
            recipients_text = self.setting_vars["alerts_email_recipients"].get("1.0", "end-1c")
            recipients = [line.strip() for line in recipients_text.split("\n") if line.strip()]
            
            # Basic validation
            if not email_config["smtp_server"]:
                messagebox.showerror("Configuration Error", "SMTP server is required")
                return
            
            if not email_config["username"]:
                messagebox.showerror("Configuration Error", "Username is required")
                return
            
            if not email_config["password"]:
                messagebox.showerror("Configuration Error", "Password is required")
                return
            
            if not email_config["from_address"]:
                messagebox.showerror("Configuration Error", "From address is required")
                return
            
            if not recipients:
                messagebox.showerror("Configuration Error", "At least one recipient is required")
                return
            
            # Show progress dialog
            progress_dialog = show_email_test_progress(self.dialog)
            progress_dialog.set_cancel_callback(lambda: email_tester.cancel_test())
            
            # Create test callback
            def test_callback(message, results=None):
                if results:
                    # Test completed
                    progress_dialog.close_dialog()
                    show_email_test_results(self.dialog, results)
                else:
                    # Progress update
                    progress_steps = {
                        "Validating email configuration...": 0.1,
                        "Testing DNS resolution and connectivity...": 0.3,
                        "Establishing SMTP connection...": 0.5,
                        "Testing SMTP authentication...": 0.7,
                        "Sending test email...": 0.9,
                        "Test completed": 1.0
                    }
                    progress = progress_steps.get(message, 0.5)
                    progress_dialog.update_progress(message, progress)
            
            # Start the test
            result = email_tester.test_email_configuration(email_config, recipients, test_callback)
            
            if not result["success"]:
                progress_dialog.close_dialog()
                messagebox.showerror("Test Error", result["error"])
            
        except Exception as e:
            messagebox.showerror("Test Error", f"Failed to start email test: {str(e)}")


def show_settings_dialog(parent, callback=None):
    """Convenience function to show settings dialog"""
    return SettingsDialog(parent, callback)
