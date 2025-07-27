import sqlite3
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import datetime
import threading
import webbrowser

class ProfileManager:
    def __init__(self, app):
        self.app = app
        self.db_path = 'network.db'
        self.default_profile = None
        self.loaded_profile_label = None  # Will be set by setup_profile_buttons
        self.load_default_profile()
    
    def load_default_profile(self):
        """Load the default profile if set"""
        # Load default profile from settings
        try:
            from settings import settings_manager
            self.default_profile = settings_manager.get_setting('interface', 'default_profile', '')
            if self.default_profile and self.default_profile != "[No default profile]":
                # Use after to ensure UI is fully initialized
                self.app.root.after(1000, lambda: self.load_profile_by_name(self.default_profile))
        except Exception as e:
            print(f"Error loading default profile: {e}")

    def save_profile(self):
        """Save current selected devices as a profile"""
        if not self.app.selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device to save as a profile.")
            return
            
        # Create dialog for profile name
        dialog = ctk.CTkToplevel(self.app.root)
        dialog.title("Save Profile")
        dialog.geometry("400x200")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Profile name entry
        label = ctk.CTkLabel(dialog, text="Enter profile name:", font=ctk.CTkFont(size=14))
        label.pack(pady=20)
        
        entry = ctk.CTkEntry(dialog, width=300, placeholder_text="My Network Profile")
        entry.pack(pady=10)
        entry.focus()
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)
        
        def save():
            profile_name = entry.get().strip()
            if not profile_name:
                messagebox.showerror("Error", "Please enter a profile name.")
                return
                
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Save each selected device
                for device in self.app.selected_devices:
                    cursor.execute("""
                        INSERT INTO Profile (Date, Time, Profile, IPAddress, MACAddress, FriendlyName, 
                                           Hostname, Manufacturer, Response, WebService, Notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        datetime.date.today().strftime('%Y-%m-%d'),
                        datetime.datetime.now().strftime('%H:%M:%S'),
                        profile_name,
                        device.get('ip', ''),
                        device.get('mac', ''),
                        device.get('friendly_name', ''),
                        device.get('hostname', ''),
                        device.get('manufacturer', ''),
                        int(device.get('response_time', 0) * 1000),  # Convert to ms
                        device.get('web_service', ''),
                        device.get('notes', '')
                    ))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Success", f"Profile '{profile_name}' saved with {len(self.app.selected_devices)} devices!")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save profile: {str(e)}")
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save, width=100)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy, width=100)
        cancel_btn.pack(side="left")
        
        # Bind Enter key to save
        entry.bind('<Return>', lambda e: save())
        
    def load_profile(self):
        """Load devices from a saved profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get list of profiles
            cursor.execute("SELECT DISTINCT Profile FROM Profile ORDER BY Profile")
            profiles = [row[0] for row in cursor.fetchall()]
            
            if not profiles:
                messagebox.showinfo("No Profiles", "No saved profiles found.")
                conn.close()
                return
                
            # Create profile selection dialog
            dialog = ctk.CTkToplevel(self.app.root)
            dialog.title("Load Profile")
            dialog.geometry("500x400")
            dialog.transient(self.app.root)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            # Profile list
            label = ctk.CTkLabel(dialog, text="Select a profile to load:", font=ctk.CTkFont(size=14))
            label.pack(pady=10)
            
            # Create scrollable frame for profiles
            scroll_frame = ctk.CTkScrollableFrame(dialog, width=450, height=250)
            scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
            
            selected_profile = ctk.StringVar()
            
            for profile in profiles:
                # Get device count for this profile
                cursor.execute("SELECT COUNT(*) FROM Profile WHERE Profile = ?", (profile,))
                count = cursor.fetchone()[0]
                
                radio = ctk.CTkRadioButton(
                    scroll_frame,
                    text=f"{profile} ({count} devices)",
                    variable=selected_profile,
                    value=profile
                )
                radio.pack(pady=5, padx=10, anchor="w")
            
            # Set default selection
            if profiles:
                selected_profile.set(profiles[0])
            
            # Button frame
            button_frame = ctk.CTkFrame(dialog)
            button_frame.pack(pady=20)
            
            def load():
                profile_name = selected_profile.get()
                if not profile_name:
                    messagebox.showerror("Error", "Please select a profile.")
                    return
                    
                # Load devices from profile
                cursor.execute("""
                    SELECT IPAddress, MACAddress, FriendlyName, Hostname, Manufacturer, 
                           Response, WebService, Notes
                    FROM Profile WHERE Profile = ?
                    ORDER BY IPAddress
                """, (profile_name,))
                
                devices = cursor.fetchall()
                
                # Clear current devices and add loaded ones
                self.app.clear_device_table()
                
                for device_data in devices:
                    device = {
                        'ip': device_data[0],
                        'mac': device_data[1] or 'Unknown',
                        'friendly_name': device_data[2] or '',
                        'hostname': device_data[3] or 'Unknown',
                        'manufacturer': device_data[4] or 'Unknown',
                        'response_time': device_data[5] / 1000.0 if device_data[5] else 0,  # Convert from ms
                        'web_service': device_data[6] or '',
                        'notes': device_data[7] or '',
                        'status': 'Loaded',
                        'profile': profile_name
                    }
                    self.app.all_devices.append(device)
                    self.app.add_device_to_table(device)
                
                # Update summary
                problematic = sum(1 for d in self.app.all_devices if d.get('response_time', 0) * 1000 > 500)
                self.app.summary_label.configure(
                    text=f"Devices found: {len(self.app.all_devices)} | Problematic (>500ms): {problematic}"
                )
                
                messagebox.showinfo("Success", f"Loaded {len(devices)} devices from profile '{profile_name}'")
                self.app.update_status(f"Loaded profile: {profile_name}")
                # Update the loaded profile label
                if self.loaded_profile_label:
                    self.loaded_profile_label.configure(text=f"Profile: {profile_name}")
                dialog.destroy()
                conn.close()
            
            def delete():
                profile_name = selected_profile.get()
                if not profile_name:
                    messagebox.showerror("Error", "Please select a profile.")
                    return
                    
                if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the profile '{profile_name}'?"):
                    cursor.execute("DELETE FROM Profile WHERE Profile = ?", (profile_name,))
                    conn.commit()
                    messagebox.showinfo("Success", f"Profile '{profile_name}' deleted.")
                    dialog.destroy()
                    conn.close()
                    # Re-open the load dialog with updated list
                    self.load_profile()
            
            load_btn = ctk.CTkButton(button_frame, text="Load", command=load, width=100)
            load_btn.pack(side="left", padx=5)
            
            delete_btn = ctk.CTkButton(button_frame, text="Delete", command=delete, width=100, fg_color="#d32f2f")
            delete_btn.pack(side="left", padx=5)
            
            cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy, width=100)
            cancel_btn.pack(side="left", padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profiles: {str(e)}")
            if 'conn' in locals():
                conn.close()

    def load_profile_by_name(self, profile_name):
        """Load devices for a specific profile name"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT IPAddress, MACAddress, FriendlyName, Hostname, Manufacturer, 
                       Response, WebService, Notes
                FROM Profile WHERE Profile = ?
                ORDER BY IPAddress
            """, (profile_name,))
            
            devices = cursor.fetchall()
            
            if not devices:
                return
                
            self.app.clear_device_table()
            
            for device_data in devices:
                device = {
                    'ip': device_data[0],
                    'mac': device_data[1] or 'Unknown',
                    'friendly_name': device_data[2] or '',
                    'hostname': device_data[3] or 'Unknown',
                    'manufacturer': device_data[4] or 'Unknown',
                    'response_time': device_data[5] / 1000.0 if device_data[5] else 0,
                    'web_service': device_data[6] or '',
                    'notes': device_data[7] or '',
                    'status': 'Loaded',
                    'profile': profile_name
                }
                self.app.all_devices.append(device)
                self.app.add_device_to_table(device)
            
            problematic = sum(1 for d in self.app.all_devices if d.get('response_time', 0) * 1000 > 500)
            self.app.summary_label.configure(
                text=f"Devices found: {len(self.app.all_devices)} | Problematic (>500ms): {problematic}"
            )
            
            self.app.update_status(f"Loaded default profile: {profile_name}")
            # Update the loaded profile label
            if self.loaded_profile_label:
                self.loaded_profile_label.configure(text=f"Profile: {profile_name}")
            conn.close()
        except Exception as e:
            print(f"Error loading default profile: {e}")

    def add_to_profile(self):
        """Add selected devices to the currently loaded profile"""
        if not self.app.selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device.")
            return

        profile_devices = [d for d in self.app.all_devices if d.get('profile')]
        if not profile_devices:
            messagebox.showinfo("No Profile Loaded", "Please load a profile before adding devices.")
            return

        # Assume a single profile is loaded
        profile_name = profile_devices[0].get('profile')

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check which devices already exist in the profile
            existing_macs = set()
            cursor.execute("SELECT MACAddress FROM Profile WHERE Profile = ?", (profile_name,))
            existing_macs = {self.normalize_mac(row[0]) for row in cursor.fetchall()}

            added_count = 0
            skipped_count = 0

            for device in self.app.selected_devices:
                # Normalize device MAC
                mac = self.normalize_mac(device.get('mac', ''))
                if not mac or mac in existing_macs:
                    skipped_count += 1
                    continue

                cursor.execute("""
                    INSERT INTO Profile (Date, Time, Profile, IPAddress, MACAddress, FriendlyName, 
                                       Hostname, Manufacturer, Response, WebService, Notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        datetime.date.today().strftime('%Y-%m-%d'),
                        datetime.datetime.now().strftime('%H:%M:%S'),
                        profile_name,
                        device.get('ip', ''),
                        device.get('mac', ''),
                        device.get('friendly_name', ''),
                        device.get('hostname', ''),
                        device.get('manufacturer', ''),
                        int(device.get('response_time', 0) * 1000),
                        device.get('web_service', ''),
                        device.get('notes', '')
                    ))
                added_count += 1

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", 
                                f"Added {added_count} device(s) to profile '{profile_name}'. {skipped_count} already exist.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add devices to profile: {str(e)}")

    def set_default_profile(self):
        """Set a selected profile as default"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Profile FROM Profile ORDER BY Profile")
        profiles = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not profiles:
            messagebox.showinfo("No Profiles", "No profiles found.")
            return

        dialog = ctk.CTkToplevel(self.app.root)
        dialog.title("Set Default Profile")
        dialog.geometry("500x350")
        dialog.transient(self.app.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Current default profile
        current_default = ""
        try:
            with open('default_profile.txt', 'r') as f:
                current_default = f.read().strip()
        except FileNotFoundError:
            pass

        if current_default:
            info_label = ctk.CTkLabel(dialog, 
                text=f"Current default: {current_default}", 
                font=ctk.CTkFont(size=12, slant="italic"))
            info_label.pack(pady=5)

        label = ctk.CTkLabel(dialog, text="Select a default profile:", font=ctk.CTkFont(size=14))
        label.pack(pady=10)

        scroll_frame = ctk.CTkScrollableFrame(dialog, width=450, height=150)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        selected_profile = ctk.StringVar()

        # Add option to clear default
        clear_radio = ctk.CTkRadioButton(
            scroll_frame,
            text="[No default profile]",
            variable=selected_profile,
            value=""
        )
        clear_radio.pack(pady=5, padx=10, anchor="w")

        for profile in profiles:
            radio = ctk.CTkRadioButton(
                scroll_frame,
                text=profile,
                variable=selected_profile,
                value=profile
            )
            radio.pack(pady=5, padx=10, anchor="w")

        if current_default in profiles:
            selected_profile.set(current_default)
        elif profiles:
            selected_profile.set(profiles[0])

        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)

        def set_default():
            profile_name = selected_profile.get()

            try:
                if profile_name:
                    with open('default_profile.txt', 'w') as f:
                        f.write(profile_name)
                    messagebox.showinfo("Success", f"Default profile set to '{profile_name}'")
                else:
                    # Remove default profile file
                    import os
                    if os.path.exists('default_profile.txt'):
                        os.remove('default_profile.txt')
                    messagebox.showinfo("Success", "Default profile cleared")
                    
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to set default profile: {str(e)}")

        set_btn = ctk.CTkButton(button_frame, text="Set Default", command=set_default, width=100)
        set_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy, width=100)
        cancel_btn.pack(side="left", padx=5)

    def remove_from_profile(self):
        """Remove selected devices from their profiles"""
        if not self.app.selected_devices:
            messagebox.showwarning("No Devices Selected", "Please select at least one device to remove.")
            return
            
        # Get devices that have profiles
        devices_with_profiles = [d for d in self.app.selected_devices if d.get('profile')]
        
        if not devices_with_profiles:
            messagebox.showinfo("No Profile", "Selected devices are not part of any profile.")
            return
            
        # Confirm removal
        profile_names = list(set(d.get('profile') for d in devices_with_profiles))
        device_count = len(devices_with_profiles)
        
        if len(profile_names) == 1:
            msg = f"Remove {device_count} device(s) from profile '{profile_names[0]}'?"
        else:
            msg = f"Remove {device_count} device(s) from multiple profiles?"
            
        if not messagebox.askyesno("Confirm Remove", msg):
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            removed_count = 0
            for device in devices_with_profiles:
                # Remove from database using MAC address as primary identifier
                cursor.execute("""
                    DELETE FROM Profile 
                    WHERE Profile = ? AND MACAddress = ?
                """, (device.get('profile'), device.get('mac')))
                
                # Update device in UI to remove profile
                device['profile'] = ''
                removed_count += 1
                
            conn.commit()
            conn.close()
            
            # Refresh the device table to update profile column
            self.app.refresh_device_table()
            
            messagebox.showinfo("Success", f"Removed {removed_count} device(s) from profile(s).")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove devices: {str(e)}")
            
    def normalize_mac(self, mac):
        """Normalize MAC address to a consistent format (uppercase with colons)"""
        if not mac or mac.upper() == 'UNKNOWN':
            return None
        # Remove all separators (colons, hyphens, dots)
        mac_clean = mac.upper().replace(':', '').replace('-', '').replace('.', '')
        # Insert colons every 2 characters
        if len(mac_clean) == 12:  # Valid MAC has 12 hex characters
            return ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2))
        return None
    
    def update_profile(self):
        """Update the response times for devices in the loaded profile"""
        # Check if a profile is loaded
        profile_devices = [d for d in self.app.all_devices if d.get('profile')]
        if not profile_devices:
            messagebox.showinfo("No Profile Loaded", "Please load a profile before updating.")
            return
        
        # Get the profile name
        profile_names = list(set(d.get('profile') for d in profile_devices if d.get('profile')))
        if not profile_names:
            messagebox.showinfo("No Profile", "No profile loaded.")
            return
        profile_name = profile_names[0]  # Assume single profile loaded
        
        # Confirm update
        device_count = len(profile_devices)
        if not messagebox.askyesno("Update Profile", 
                                  f"Update {device_count} device(s) in profile '{profile_name}'?\n\n" +
                                  "This will scan the network and update:\n" +
                                  "• IP addresses (if changed)\n" +
                                  "• Response times\n" +
                                  "• Online/offline status"):
            return
        
        # Update status
        self.app.update_status(f"Updating profile '{profile_name}'...")
        
        # Create a thread to perform the update scan
        update_thread = threading.Thread(target=self._perform_profile_update, args=(profile_devices, profile_name))
        update_thread.daemon = True
        update_thread.start()
    
    def _perform_profile_update(self, profile_devices, profile_name):
        """Perform the profile update in a background thread"""
        try:
            from NetworkMonitor_CTk_Full import NetworkScanner
            import socket
            import time
            
            # Track update progress
            updated_count = 0
            total_devices = len(profile_devices)
            
            # Create mapping of normalized MAC to device
            mac_to_device = {}
            for device in profile_devices:
                normalized_mac = self.normalize_mac(device.get('mac', ''))
                if normalized_mac:
                    mac_to_device[normalized_mac] = device
            
            # Get IP range from the first device's IP
            if profile_devices:
                first_ip = profile_devices[0].get('ip', '')
                # Extract network range (assume /24)
                ip_parts = first_ip.split('.')
                if len(ip_parts) == 4:
                    ip_range = f"{'.'.join(ip_parts[:3])}.0/24"
                else:
                    ip_range = "192.168.1.0/24"  # Default fallback
            else:
                ip_range = "192.168.1.0/24"
            
            # Scan the network
            scanner = NetworkScanner(
                ip_range,
                progress_callback=lambda p: self.app.root.after(0, lambda: self.app.progress_bar.set(p / 100))
            )
            
            scanned_devices = scanner.scan()
            
            # Create a mapping of normalized MAC to scanned device
            scanned_mac_to_device = {}
            for scanned in scanned_devices:
                normalized_mac = self.normalize_mac(scanned.get('mac', ''))
                if normalized_mac:
                    scanned_mac_to_device[normalized_mac] = scanned
            
            # Update database and UI
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update each device in the profile
            for normalized_mac, device in mac_to_device.items():
                if normalized_mac in scanned_mac_to_device:
                    # Device found in scan - update with new response time and IP
                    scanned = scanned_mac_to_device[normalized_mac]
                    new_response_time = scanned.get('response_time', 0)
                    new_ip = scanned.get('ip', device.get('ip', ''))
                    
                    # Update database with new IP and response time
                    cursor.execute("""
                        UPDATE Profile 
                        SET IPAddress = ?, Response = ?, Date = ?, Time = ?
                        WHERE Profile = ? AND MACAddress = ?
                    """, (
                        new_ip,
                        int(new_response_time * 1000),  # Convert to ms
                        datetime.date.today().strftime('%Y-%m-%d'),
                        datetime.datetime.now().strftime('%H:%M:%S'),
                        profile_name,
                        device.get('mac', '')
                    ))
                    
                    # Update device in memory
                    device['ip'] = new_ip
                    device['response_time'] = new_response_time
                    device['status'] = 'Online'
                    updated_count += 1
                else:
                    # Device not found in scan - mark as offline
                    cursor.execute("""
                        UPDATE Profile 
                        SET Response = ?, Date = ?, Time = ?
                        WHERE Profile = ? AND MACAddress = ?
                    """, (
                        -1,  # -1 indicates offline
                        datetime.date.today().strftime('%Y-%m-%d'),
                        datetime.datetime.now().strftime('%H:%M:%S'),
                        profile_name,
                        device.get('mac', '')
                    ))
                    
                    # Update device in memory
                    device['response_time'] = -1
                    device['status'] = 'Offline'
                    updated_count += 1
            
            conn.commit()
            conn.close()
            
            # Refresh UI on main thread
            self.app.root.after(0, lambda: self._complete_profile_update(updated_count, profile_name))
            
        except Exception as e:
            self.app.root.after(0, lambda: messagebox.showerror("Error", f"Failed to update profile: {str(e)}"))
    
    def _complete_profile_update(self, updated_count, profile_name):
        """Complete the profile update on the main thread"""
        # Refresh the device table to show updated response times
        self.app.refresh_device_table()
        
        # Update summary
        problematic = sum(1 for d in self.app.all_devices if d.get('response_time', 0) * 1000 > 500)
        offline = sum(1 for d in self.app.all_devices if d.get('response_time', 0) < 0)
        self.app.summary_label.configure(
            text=f"Devices found: {len(self.app.all_devices)} | Problematic (>500ms): {problematic} | Offline: {offline}"
        )
        
        # Reset progress bar
        self.app.progress_bar.set(1.0)
        
        # Show completion message
        messagebox.showinfo("Update Complete", 
                          f"Successfully updated {updated_count} device(s) in profile '{profile_name}'.\n\n" +
                          "Response times have been refreshed and saved to the database.")
        
        self.app.update_status(f"Profile '{profile_name}' updated successfully")
    
    def scan_new(self):
        """Scan for new devices not in the current profile"""
        # Check if we have devices loaded from a profile
        profile_devices = [d for d in self.app.all_devices if d.get('profile')]
        
        if not profile_devices:
            messagebox.showinfo("No Profile", "Please load a profile first before scanning for new devices.")
            return
            
        # Get the profile name
        profile_names = list(set(d.get('profile') for d in profile_devices if d.get('profile')))
        if not profile_names:
            messagebox.showinfo("No Profile", "No profile loaded.")
            return
        profile_name = profile_names[0]  # Assume single profile loaded
            
        # Get normalized MAC addresses from ALL devices currently in the table
        existing_macs = set()
        for device in self.app.all_devices:
            normalized_mac = self.normalize_mac(device.get('mac', ''))
            if normalized_mac:
                existing_macs.add(normalized_mac)
        
        # Also specifically track which MACs are from the profile for reporting
        profile_macs = set()
        for device in profile_devices:
            normalized_mac = self.normalize_mac(device.get('mac', ''))
            if normalized_mac:
                profile_macs.add(normalized_mac)
        
        # Get current network range
        ip_range = self.app.ip_input.get().strip()
        if not ip_range:
            messagebox.showerror("Error", "Please enter an IP range to scan.")
            return
            
        # Update status
        self.app.update_status(f"Scanning for devices not in profile '{profile_name}'...")
        messagebox.showinfo("Scanning", f"Starting scan for new devices.\n\nThis will preserve your loaded profile and:\n• Highlight new devices in green\n• Highlight removed devices in red")
        
        # Create a thread to perform the scan without clearing existing devices
        scan_thread = threading.Thread(target=self._perform_new_device_scan, args=(ip_range, existing_macs, profile_macs, profile_name))
        scan_thread.daemon = True
        scan_thread.start()
        
    def _perform_new_device_scan(self, ip_range, existing_macs, profile_macs, profile_name):
        """Perform network scan in background thread"""
        try:
            # Create a scanner without clearing the existing table
            from NetworkMonitor_CTk_Full import NetworkScanner
            
            new_devices_found = []
            found_macs = set()  # Track MACs found in this scan
            
            def device_callback(device):
                # Normalize the device's MAC address for comparison
                device_mac = device.get('mac', '')
                normalized_device_mac = self.normalize_mac(device_mac)
                
                if not normalized_device_mac:
                    return  # Skip devices without valid MAC addresses
                
                # Add to found MACs
                found_macs.add(normalized_device_mac)
                    
                # Check if this device is already in the table (by normalized MAC address)
                if normalized_device_mac in existing_macs:
                    return  # Skip devices already displayed
                    
                # Check if this device is new (not in the profile)
                if normalized_device_mac not in profile_macs:
                    device['is_new'] = True
                    device['highlight_color'] = "#90EE90"  # Light green
                    new_devices_found.append(device)
                    # Add to UI on main thread
                    self.app.root.after(0, lambda d=device: self._add_new_device_to_table(d))
            
            scanner = NetworkScanner(
                ip_range,
                progress_callback=lambda p: self.app.root.after(0, lambda: self.app.progress_bar.set(p / 100)),
                device_callback=device_callback
            )
            
            # Run the scan
            scanner.scan()
            
            # After scan completes, check for missing devices
            missing_devices = []
            for device in self.app.all_devices:
                if device.get('profile') == profile_name:  # Only check devices in the current profile
                    normalized_mac = self.normalize_mac(device.get('mac', ''))
                    if normalized_mac and normalized_mac not in found_macs:
                        # Device was not found in scan
                        device['is_missing'] = True
                        device['status'] = 'Removed'
                        missing_devices.append(device)
            
            # Update UI for missing devices on main thread
            self.app.root.after(0, lambda: self._mark_missing_devices(missing_devices))
            
            # Process results on main thread
            self.app.root.after(0, lambda: self._show_new_device_results(new_devices_found, missing_devices, profile_name))
            
        except Exception as e:
            self.app.root.after(0, lambda: messagebox.showerror("Error", f"Scan failed: {str(e)}"))
    
    def _add_new_device_to_table(self, device):
        """Add a new device to the table with green highlighting"""
        # Add device to the list
        self.app.all_devices.append(device)
        
        # Add to table with special highlighting
        row_num = len(self.app.device_rows) + 1
        row_widgets = []
        
        # Create widgets with green highlighting for new devices
        highlight_color = "#90EE90" if device.get('is_new') else None
        text_color = "#006400" if device.get('is_new') else None  # Dark green text
        
        # Select checkbox
        var = tk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            self.app.table_frame, 
            text="",
            variable=var,
            command=lambda: self.app.toggle_device_selection(device, var.get())
        )
        checkbox.grid(row=row_num, column=0, padx=5, pady=2, sticky="w")
        row_widgets.append(checkbox)
        
        # Profile (empty for new devices)
        profile_label = ctk.CTkLabel(self.app.table_frame, text="", text_color=text_color)
        profile_label.grid(row=row_num, column=1, padx=5, pady=2)
        row_widgets.append(profile_label)

        # IP Address
        ip_label = ctk.CTkLabel(self.app.table_frame, text=device['ip'], text_color=text_color)
        ip_label.grid(row=row_num, column=2, padx=5, pady=2)
        row_widgets.append(ip_label)

        # MAC Address
        mac_label = ctk.CTkLabel(self.app.table_frame, text=device.get('mac', 'Unknown'), text_color=text_color)
        mac_label.grid(row=row_num, column=3, padx=5, pady=2)
        row_widgets.append(mac_label)
        
        # Hostname
        hostname_label = ctk.CTkLabel(self.app.table_frame, text=device.get('hostname', 'Unknown'), text_color=text_color)
        hostname_label.grid(row=row_num, column=4, padx=5, pady=2)
        row_widgets.append(hostname_label)
        
        # Friendly Name
        friendly_name_label = ctk.CTkLabel(self.app.table_frame, text="", text_color=text_color)
        friendly_name_label.grid(row=row_num, column=5, padx=5, pady=2)
        row_widgets.append(friendly_name_label)

        # Manufacturer
        manufacturer_label = ctk.CTkLabel(self.app.table_frame, text=device.get('manufacturer', 'Unknown'), text_color=text_color)
        manufacturer_label.grid(row=row_num, column=6, padx=5, pady=2)
        row_widgets.append(manufacturer_label)
        
        # Response Time
        response_ms = device.get('response_time', 0) * 1000
        response_color = "#f44336" if response_ms > 500 else text_color
        response_label = ctk.CTkLabel(
            self.app.table_frame, 
            text=f"{response_ms:.0f}ms",
            text_color=response_color
        )
        response_label.grid(row=row_num, column=7, padx=5, pady=2)
        row_widgets.append(response_label)
        
        # Web Service
        web_service = device.get('web_service')
        if web_service:
            web_btn = ctk.CTkButton(
                self.app.table_frame,
                text="Open",
                width=60,
                height=24,
                command=lambda: webbrowser.open(web_service)
            )
            web_btn.grid(row=row_num, column=8, padx=5, pady=2)
            row_widgets.append(web_btn)
        else:
            web_label = ctk.CTkLabel(self.app.table_frame, text="None", text_color=text_color)
            web_label.grid(row=row_num, column=8, padx=5, pady=2)
            row_widgets.append(web_label)
        
        # Actions buttons
        actions_frame = ctk.CTkFrame(self.app.table_frame)
        actions_frame.grid(row=row_num, column=9, padx=5, pady=2)

        details_btn = ctk.CTkButton(
            actions_frame,
            text="Details",
            width=60,
            height=20,
            command=lambda dev=device: self.app.show_device_details(dev)
        )
        details_btn.grid(row=0, column=0, padx=2, pady=1)

        nmap_btn = ctk.CTkButton(
            actions_frame,
            text="Nmap",
            width=50,
            height=20,
            command=lambda dev=device: self.app.show_nmap_dialog(dev.get('ip'))
        )
        nmap_btn.grid(row=0, column=1, padx=2, pady=1)

        row_widgets.append(actions_frame)

        # Notes button for new devices
        notes_btn = ctk.CTkButton(
            self.app.table_frame,
            text="Add Notes",
            width=80,
            height=24,
            fg_color=None,  # Default color for new devices
            command=lambda dev=device: self.app.show_notes_dialog(dev)
        )
        notes_btn.grid(row=row_num, column=10, padx=5, pady=2)
        row_widgets.append(notes_btn)

        self.app.device_rows.append(row_widgets)
        
        # Update summary
        problematic = sum(1 for d in self.app.all_devices if d.get('response_time', 0) * 1000 > 500)
        self.app.summary_label.configure(text=f"Devices found: {len(self.app.all_devices)} | Problematic (>500ms): {problematic}")
    
    def _mark_missing_devices(self, missing_devices):
        """Mark devices that were not found in the scan as removed"""
        # Instead of refreshing the entire table, we need to update specific rows
        # Find the row index for each missing device and update its appearance
        for missing_device in missing_devices:
            # Find the row index for this device
            for i, device in enumerate(self.app.all_devices):
                if (device.get('mac') == missing_device.get('mac') and 
                    device.get('profile') == missing_device.get('profile')):
                    # Update the labels in the corresponding row to show red text
                    if i < len(self.app.device_rows):
                        row_widgets = self.app.device_rows[i]
                        # Update text color to red for all labels except checkbox
                        red_color = "#FF0000"
                        
                        # Profile label (index 1)
                        if len(row_widgets) > 1 and hasattr(row_widgets[1], 'configure'):
                            row_widgets[1].configure(text_color=red_color)
                        
                        # IP label (index 2)
                        if len(row_widgets) > 2 and hasattr(row_widgets[2], 'configure'):
                            row_widgets[2].configure(text_color=red_color)
                        
                        # MAC label (index 3)
                        if len(row_widgets) > 3 and hasattr(row_widgets[3], 'configure'):
                            row_widgets[3].configure(text_color=red_color)
                        
                        # Hostname label (index 4)
                        if len(row_widgets) > 4 and hasattr(row_widgets[4], 'configure'):
                            row_widgets[4].configure(text_color=red_color)
                        
                        # Friendly name label (index 5)
                        if len(row_widgets) > 5 and hasattr(row_widgets[5], 'configure'):
                            row_widgets[5].configure(text_color=red_color)
                        
                        # Manufacturer label (index 6)
                        if len(row_widgets) > 6 and hasattr(row_widgets[6], 'configure'):
                            row_widgets[6].configure(text_color=red_color)
                        
                        # Response time label (index 7)
                        if len(row_widgets) > 7 and hasattr(row_widgets[7], 'configure'):
                            row_widgets[7].configure(text_color=red_color)
                        
                        # Notes button (index 10) - Update color and keep functionality
                        if len(row_widgets) > 10 and hasattr(row_widgets[10], 'configure'):
                            # Keep the button but change its color to indicate removed device
                            row_widgets[10].configure(fg_color="#FF6B6B")  # Light red color for removed devices
                    break
    
    def _show_new_device_results(self, new_devices, missing_devices, profile_name):
        """Show results of new device scan"""
        self.app.progress_bar.set(1.0)
        
        # Build status message
        status_parts = []
        if new_devices:
            status_parts.append(f"{len(new_devices)} new device(s) found")
        if missing_devices:
            status_parts.append(f"{len(missing_devices)} device(s) removed")
        
        if status_parts:
            self.app.update_status(f"Scan complete: {' and '.join(status_parts)} for profile '{profile_name}'")
        else:
            self.app.update_status("Scan complete: No changes detected")
        
        # Build detailed message
        message_parts = []
        
        if new_devices:
            message_parts.append(f"Found {len(new_devices)} new device(s) (highlighted in green):\n")
            device_list = "\n".join([f"• {d.get('ip')} ({d.get('hostname', 'Unknown')})\n  MAC: {d.get('mac')}\n  Manufacturer: {d.get('manufacturer', 'Unknown')}" 
                                   for d in new_devices[:5]])
            message_parts.append(device_list)
            if len(new_devices) > 5:
                message_parts.append(f"\n... and {len(new_devices) - 5} more")
        
        if missing_devices:
            if new_devices:
                message_parts.append("\n\n")
            message_parts.append(f"Found {len(missing_devices)} removed device(s) (highlighted in red):\n")
            removed_list = "\n".join([f"• {d.get('ip')} ({d.get('hostname', 'Unknown')})\n  MAC: {d.get('mac')}\n  Last seen: {d.get('friendly_name', 'Unknown')}" 
                                     for d in missing_devices[:5]])
            message_parts.append(removed_list)
            if len(missing_devices) > 5:
                message_parts.append(f"\n... and {len(missing_devices) - 5} more")
            message_parts.append("\n\nThese devices can be manually removed using 'Remove from Profile'")
        
        if new_devices or missing_devices:
            messagebox.showinfo("Scan Results", 
                              f"Scan completed for profile '{profile_name}'\n\n" + "".join(message_parts))
        else:
            messagebox.showinfo("Scan Complete", 
                              f"No changes detected.\n\nAll devices in profile '{profile_name}' are still present, and no new devices were found.")


def setup_profile_buttons(app):
    """Add profile buttons to the main window"""
    # Create profile manager instance
    profile_manager = ProfileManager(app)
    
    # Create a new frame for profile buttons that sits between search bar and device table
    # This will be inserted as row 2, pushing the device table down to row 3
    profile_frame = ctk.CTkFrame(app.main_frame)
    profile_frame.grid(row=2, column=0, padx=20, pady=(10, 10), sticky="ew")
    profile_frame.grid_columnconfigure(0, weight=1)  # Allow frame to expand
    
    # Create left frame for loaded profile name
    left_frame = ctk.CTkFrame(profile_frame)
    left_frame.pack(side="left", pady=5, padx=10)
    
    # Add loaded profile label
    loaded_profile_label = ctk.CTkLabel(
        left_frame,
        text="No profile loaded",
        font=ctk.CTkFont(size=16, weight="bold")
    )
    loaded_profile_label.pack(side="left")
    
    # Store reference to update later
    profile_manager.loaded_profile_label = loaded_profile_label
    
    # Create inner frame for right-aligning buttons
    button_container = ctk.CTkFrame(profile_frame)
    button_container.pack(side="right", pady=5, padx=10)
    
    # Add label
    profile_label = ctk.CTkLabel(
        button_container,
        text="Profile Management:",
        font=ctk.CTkFont(size=14, weight="bold")
    )
    profile_label.pack(side="left", padx=(10, 20))
    
    save_profile_btn = ctk.CTkButton(
        button_container,
        text="Save Profile",
        command=profile_manager.save_profile,
        width=120,
        height=32
    )
    save_profile_btn.pack(side="left", padx=5)
    
    load_profile_btn = ctk.CTkButton(
        button_container,
        text="Load Profile",
        command=profile_manager.load_profile,
        width=120,
        height=32
    )
    load_profile_btn.pack(side="left", padx=5)
    
    add_to_profile_btn = ctk.CTkButton(
        button_container,
        text="Add to Profile",
        command=profile_manager.add_to_profile,
        width=120,
        height=32
    )
    add_to_profile_btn.pack(side="left", padx=5)
    
    # Update Profile button
    update_profile_btn = ctk.CTkButton(
        button_container,
        text="Update Profile",
        command=profile_manager.update_profile,
        width=120,
        height=32
    )
    update_profile_btn.pack(side="left", padx=5)
    
    # Remove from Profile button
    remove_from_profile_btn = ctk.CTkButton(
        button_container,
        text="Remove from Profile",
        command=profile_manager.remove_from_profile,
        width=150,
        height=32
    )
    remove_from_profile_btn.pack(side="left", padx=5)

    # Scan New button
    scan_new_btn = ctk.CTkButton(
        button_container,
        text="Scan New",
        command=profile_manager.scan_new,
        width=120,
        height=32
    )
    scan_new_btn.pack(side="left", padx=5)
    
    
    # Update the device table to be row 3 instead of row 2
    app.table_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
    
    return profile_manager
