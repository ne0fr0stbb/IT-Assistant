#!/usr/bin/env python3
"""
System Tray functionality for Network Monitor
Adds a system tray icon with menu options
"""

import sys
import os
import threading
from PIL import Image

try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("pystray not available - system tray functionality disabled")


class SystemTrayManager:
    """Manages system tray icon and menu"""
    
    def __init__(self, app):
        self.app = app
        self.icon = None
        self.running = False
        
        if not PYSTRAY_AVAILABLE:
            return
            
        # Load icon image
        self.icon_image = self._load_icon()
        
    def _load_icon(self):
        """Load the icon image for the system tray"""
        try:
            # Handle frozen application
            if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
                # PyInstaller frozen app
                icon_path = os.path.join(sys._MEIPASS, "I.T-Assistant.png")
            elif hasattr(sys, 'frozen'):
                # cx_Freeze frozen app
                icon_path = os.path.join(os.path.dirname(sys.executable), "I.T-Assistant.png")
            else:
                # Regular Python script
                icon_path = os.path.join(os.path.dirname(__file__), "I.T-Assistant.png")
            
            if os.path.exists(icon_path):
                return Image.open(icon_path)
            else:
                # Create a default icon if file not found
                img = Image.new('RGB', (64, 64), color='blue')
                return img
                
        except Exception as e:
            print(f"Error loading tray icon: {e}")
            # Return a default icon
            img = Image.new('RGB', (64, 64), color='blue')
            return img
    
    def create_menu(self):
        """Create the system tray menu"""
        # Dynamically create menu items based on app state
        menu_items = []
        
        # Main window toggle
        menu_items.append(item('Show/Hide Main Window', self.toggle_window, default=True))
        
        # Live Monitor toggle if it's minimized
        if hasattr(self.app, 'minimized_monitor_window') and self.app.minimized_monitor_window:
            menu_items.append(item('Show Live Monitor', self.restore_live_monitor))
        
        menu_items.extend([
            pystray.Menu.SEPARATOR,
            item('Network Scan', self.start_scan),
            item('Live Monitor', self.open_monitor),
            item('Speed Test', self.run_speed_test),
            pystray.Menu.SEPARATOR,
            item('Settings', self.open_settings),
            item('About', self.show_about),
            pystray.Menu.SEPARATOR,
            item('Exit', self.quit_app)
        ])
        
        return pystray.Menu(*menu_items)
    
    def start(self):
        """Start the system tray icon"""
        if not PYSTRAY_AVAILABLE:
            return
            
        def run():
            self.icon = pystray.Icon(
                "I.T Assistant",
                self.icon_image,
                "I.T Assistant - Network Monitor",
                self.create_menu()
            )
            self.running = True
            self.icon.run()
        
        # Run in separate thread to not block the main GUI
        tray_thread = threading.Thread(target=run, daemon=True)
        tray_thread.start()
    
    def stop(self):
        """Stop the system tray icon"""
        if self.icon and self.running:
            self.icon.stop()
            self.running = False
    
    def update_tooltip(self, text):
        """Update the tooltip text"""
        if self.icon:
            self.icon.title = text
    
    # Menu action handlers
    def toggle_window(self, icon, item):
        """Show or hide the main window"""
        def toggle():
            if self.app.root.winfo_viewable():
                self.app.root.withdraw()
            else:
                self.app.root.deiconify()
                self.app.root.lift()
                self.app.root.focus_force()
                
                # Also restore minimized live monitor if exists
                if hasattr(self.app, 'minimized_monitor_window') and self.app.minimized_monitor_window:
                    try:
                        self.app.minimized_monitor_window.deiconify()
                        self.app.minimized_monitor_window.lift()
                    except:
                        pass
        
        # Run on main thread
        self.app.root.after(0, toggle)
    
    def start_scan(self, icon, item):
        """Start network scan from tray"""
        def scan():
            self.app.root.deiconify()
            self.app.root.lift()
            self.app.start_scan()
        
        self.app.root.after(0, scan)
    
    def open_monitor(self, icon, item):
        """Open live monitor from tray"""
        def monitor():
            self.app.root.deiconify()
            self.app.root.lift()
            self.app.open_live_monitor()
        
        self.app.root.after(0, monitor)
    
    def run_speed_test(self, icon, item):
        """Run speed test from tray"""
        def speed_test():
            self.app.root.deiconify()
            self.app.root.lift()
            self.app.run_speed_test()
        
        self.app.root.after(0, speed_test)
    
    def open_settings(self, icon, item):
        """Open settings from tray"""
        def settings():
            self.app.root.deiconify()
            self.app.root.lift()
            try:
                from settings_manager import show_settings_dialog
                show_settings_dialog(self.app.root)
            except:
                pass
        
        self.app.root.after(0, settings)
    
    def show_about(self, icon, item):
        """Show about dialog from tray"""
        def about():
            self.app.root.deiconify()
            self.app.root.lift()
            self.app.show_about()
        
        self.app.root.after(0, about)
    
    def quit_app(self, icon, item):
        """Quit application from tray"""
        # Close any minimized windows
        if hasattr(self.app, 'minimized_monitor_window') and self.app.minimized_monitor_window:
            try:
                self.app.minimized_monitor_window.destroy()
            except:
                pass
        self.stop()
        self.app.root.quit()
    
    def restore_live_monitor(self, icon, item):
        """Restore minimized live monitor window"""
        def restore():
            if hasattr(self.app, 'minimized_monitor_window') and self.app.minimized_monitor_window:
                try:
                    # Store the window reference
                    monitor_window = self.app.minimized_monitor_window
                    
                    # Check if window still exists
                    if monitor_window.winfo_exists():
                        # Restore the window
                        monitor_window.deiconify()
                        monitor_window.lift()
                        monitor_window.focus_force()
                        
                        # Force update to ensure window is visible
                        monitor_window.update_idletasks()
                        
                        # Update the current monitor window reference
                        self.app.current_monitor_window = monitor_window
                        
                        # Clear the minimized reference only after successful restoration
                        self.app.minimized_monitor_window = None
                        
                        # Update the menu to reflect the change
                        self.update_menu()
                    else:
                        # Window doesn't exist anymore, clear the reference
                        self.app.minimized_monitor_window = None
                        self.update_menu()
                except Exception as e:
                    print(f"Error restoring live monitor: {e}")
                    # Reset the reference if restoration failed
                    self.app.minimized_monitor_window = None
                    self.update_menu()
        
        self.app.root.after(0, restore)
    
    def update_menu(self):
        """Update the tray menu to reflect current state"""
        if self.icon and self.running:
            # Recreate the menu with updated items
            self.icon.menu = self.create_menu()
            # Force the icon to update
            try:
                self.icon.update_menu()
            except:
                # If update_menu doesn't exist, try to recreate the icon
                pass


def minimize_to_tray(app):
    """Helper function to minimize window to system tray"""
    if hasattr(app, 'tray_manager') and app.tray_manager:
        app.root.withdraw()
        if app.tray_manager.icon:
            app.tray_manager.icon.notify(
                "I.T Assistant minimized to tray",
                "Double-click to restore"
            )
