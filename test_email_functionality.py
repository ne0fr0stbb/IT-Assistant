#!/usr/bin/env python3
"""
Test script to demonstrate email testing functionality
"""

import customtkinter as ctk
from settings_manager import show_settings_dialog

def main():
    """Main function to test email functionality"""
    # Set appearance mode and color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create main window
    root = ctk.CTk()
    root.title("Network Monitor - Email Test Demo")
    root.geometry("400x300")
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (400 // 2)
    y = (root.winfo_screenheight() // 2) - (300 // 2)
    root.geometry(f"400x300+{x}+{y}")
    
    # Create main frame
    main_frame = ctk.CTkFrame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = ctk.CTkLabel(
        main_frame,
        text="Network Monitor Email Test",
        font=ctk.CTkFont(size=20, weight="bold")
    )
    title_label.pack(pady=20)
    
    # Description
    desc_text = """
This demo shows the email testing functionality.

Click "Open Settings" to access the email configuration 
and test your SMTP settings.

Features:
• Complete email configuration validation
• DNS and connectivity testing
• SMTP connection and authentication testing
• Test email sending
• Detailed test results with error reporting
"""
    
    desc_label = ctk.CTkLabel(
        main_frame,
        text=desc_text,
        font=ctk.CTkFont(size=12),
        justify="left"
    )
    desc_label.pack(pady=10)
    
    # Button frame
    button_frame = ctk.CTkFrame(main_frame)
    button_frame.pack(pady=20)
    
    # Settings button
    def open_settings():
        show_settings_dialog(root)
    
    settings_btn = ctk.CTkButton(
        button_frame,
        text="Open Settings",
        command=open_settings,
        width=150,
        height=40
    )
    settings_btn.pack(side="left", padx=10)
    
    # Exit button
    exit_btn = ctk.CTkButton(
        button_frame,
        text="Exit",
        command=root.quit,
        width=150,
        height=40
    )
    exit_btn.pack(side="left", padx=10)
    
    # Instructions
    instructions = """
To test email functionality:
1. Click "Open Settings"
2. Go to "Alerts" tab
3. Configure your email settings:
   - SMTP server (e.g., smtp.gmail.com)
   - Port (587 for TLS, 465 for SSL)
   - Username and password
   - From address
   - Recipients
4. Click "Test Email Configuration"
5. Review the detailed test results
"""
    
    instructions_label = ctk.CTkLabel(
        main_frame,
        text=instructions,
        font=ctk.CTkFont(size=10),
        justify="left"
    )
    instructions_label.pack(pady=10)
    
    # Run the application
    root.mainloop()

if __name__ == "__main__":
    main()
