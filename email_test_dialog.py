#!/usr/bin/env python3
"""
Email Test Results Dialog for Network Monitor
Displays email configuration test results in a user-friendly format
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List
from datetime import datetime


class EmailTestDialog:
    """Dialog for displaying email test results"""
    
    def __init__(self, parent, test_results: Dict):
        self.parent = parent
        self.test_results = test_results
        self.dialog = None
        
        self.create_dialog()
        self.display_results()
    
    def create_dialog(self):
        """Create the test results dialog"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Email Configuration Test Results")
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
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Header frame
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Overall status
        overall_status = self.test_results.get("overall_status", "Unknown")
        status_color = self._get_status_color(self.test_results.get("success", False))
        
        ctk.CTkLabel(
            header_frame,
            text="Test Status:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        ctk.CTkLabel(
            header_frame,
            text=overall_status,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=status_color
        ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Timestamps
        start_time = self.test_results.get("start_time", "Unknown")
        end_time = self.test_results.get("end_time", "Unknown")
        
        if start_time != "Unknown":
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_time = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        if end_time != "Unknown":
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        ctk.CTkLabel(
            header_frame,
            text=f"Started: {start_time}",
            font=ctk.CTkFont(size=10)
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        ctk.CTkLabel(
            header_frame,
            text=f"Completed: {end_time}",
            font=ctk.CTkFont(size=10)
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Test results scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(main_frame, label_text="Test Results")
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.results_frame = scroll_frame
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.close_dialog,
            width=100
        )
        close_btn.pack(side="right", padx=5, pady=10)
        
        # Copy results button
        copy_btn = ctk.CTkButton(
            button_frame,
            text="Copy Results",
            command=self.copy_results,
            width=120
        )
        copy_btn.pack(side="right", padx=5, pady=10)
    
    def display_results(self):
        """Display the test results in the dialog"""
        tests = self.test_results.get("tests", [])
        
        for i, test in enumerate(tests):
            self.create_test_result_section(self.results_frame, i, test)
    
    def create_test_result_section(self, parent, row, test_data: Dict):
        """Create a section for a single test result"""
        # Test frame
        test_frame = ctk.CTkFrame(parent)
        test_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        test_frame.grid_columnconfigure(0, weight=1)
        
        # Test header
        header_frame = ctk.CTkFrame(test_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)
        
        test_name = test_data.get("test_name", "Unknown Test")
        test_success = test_data.get("success", False)
        
        # Test name and status
        ctk.CTkLabel(
            header_frame,
            text=test_name,
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        status_text = "✓ PASS" if test_success else "✗ FAIL"
        status_color = self._get_status_color(test_success)
        
        ctk.CTkLabel(
            header_frame,
            text=status_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=status_color
        ).grid(row=0, column=1, sticky="e", padx=5, pady=2)
        
        # Error message (if any)
        if not test_success and "error" in test_data:
            error_frame = ctk.CTkFrame(test_frame)
            error_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
            error_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                error_frame,
                text="Error:",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="red"
            ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
            
            error_text = ctk.CTkTextbox(error_frame, height=40)
            error_text.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
            error_text.insert("1.0", test_data["error"])
            error_text.configure(state="disabled")
        
        # Details (if any)
        details = test_data.get("details", [])
        if details:
            details_frame = ctk.CTkFrame(test_frame)
            details_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
            details_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                details_frame,
                text="Details:",
                font=ctk.CTkFont(size=10, weight="bold")
            ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
            
            details_text = "\\n".join(f"• {detail}" for detail in details)
            details_textbox = ctk.CTkTextbox(details_frame, height=60)
            details_textbox.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
            details_textbox.insert("1.0", details_text)
            details_textbox.configure(state="disabled")
        
        # Warnings (if any)
        warnings = test_data.get("warnings", [])
        if warnings:
            warnings_frame = ctk.CTkFrame(test_frame)
            warnings_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
            warnings_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(
                warnings_frame,
                text="Warnings:",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="orange"
            ).grid(row=0, column=0, sticky="w", padx=5, pady=2)
            
            warnings_text = "\\n".join(f"⚠ {warning}" for warning in warnings)
            warnings_textbox = ctk.CTkTextbox(warnings_frame, height=40)
            warnings_textbox.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
            warnings_textbox.insert("1.0", warnings_text)
            warnings_textbox.configure(state="disabled")
        
        # Configure column weights for parent
        parent.grid_columnconfigure(0, weight=1)
    
    def _get_status_color(self, success: bool) -> str:
        """Get color for status text based on success"""
        return "green" if success else "red"
    
    def copy_results(self):
        """Copy test results to clipboard"""
        try:
            results_text = self._format_results_for_copy()
            
            # Copy to clipboard
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(results_text)
            
            messagebox.showinfo("Copied", "Test results copied to clipboard!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy results: {str(e)}")
    
    def _format_results_for_copy(self) -> str:
        """Format test results for clipboard"""
        lines = []
        lines.append("Network Monitor - Email Configuration Test Results")
        lines.append("=" * 50)
        lines.append("")
        
        # Overall status
        overall_status = self.test_results.get("overall_status", "Unknown")
        lines.append(f"Overall Status: {overall_status}")
        
        # Timestamps
        start_time = self.test_results.get("start_time", "Unknown")
        end_time = self.test_results.get("end_time", "Unknown")
        
        if start_time != "Unknown":
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_time = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        if end_time != "Unknown":
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                end_time = end_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        lines.append(f"Start Time: {start_time}")
        lines.append(f"End Time: {end_time}")
        lines.append("")
        
        # Individual test results
        tests = self.test_results.get("tests", [])
        for i, test in enumerate(tests):
            lines.append(f"{i+1}. {test.get('test_name', 'Unknown Test')}")
            lines.append(f"   Status: {'PASS' if test.get('success', False) else 'FAIL'}")
            
            if not test.get("success", False) and "error" in test:
                lines.append(f"   Error: {test['error']}")
            
            details = test.get("details", [])
            if details:
                lines.append("   Details:")
                for detail in details:
                    lines.append(f"     • {detail}")
            
            warnings = test.get("warnings", [])
            if warnings:
                lines.append("   Warnings:")
                for warning in warnings:
                    lines.append(f"     ⚠ {warning}")
            
            lines.append("")
        
        return "\\n".join(lines)
    
    def close_dialog(self):
        """Close the dialog"""
        self.dialog.destroy()


class EmailTestProgressDialog:
    """Dialog for showing email test progress"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        self.progress_label = None
        self.cancel_callback = None
        
        self.create_dialog()
    
    def create_dialog(self):
        """Create the progress dialog"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Testing Email Configuration")
        self.dialog.geometry("400x200")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (200 // 2)
        self.dialog.geometry(f"400x200+{x}+{y}")
        
        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Create main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Testing Email Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=10)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame, width=300)
        self.progress_bar.grid(row=1, column=0, pady=10)
        self.progress_bar.set(0)
        
        # Status label
        self.progress_label = ctk.CTkLabel(
            main_frame,
            text="Preparing test...",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.grid(row=2, column=0, pady=5)
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            main_frame,
            text="Cancel",
            command=self.cancel_test,
            width=100
        )
        self.cancel_button.grid(row=3, column=0, pady=15)
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_test)
    
    def update_progress(self, message: str, progress: float = None):
        """Update progress message and bar"""
        if self.progress_label:
            self.progress_label.configure(text=message)
        
        if progress is not None and self.progress_bar:
            self.progress_bar.set(progress)
        
        if self.dialog:
            self.dialog.update()
    
    def set_cancel_callback(self, callback):
        """Set callback for cancel button"""
        self.cancel_callback = callback
    
    def cancel_test(self):
        """Cancel the test"""
        if self.cancel_callback:
            self.cancel_callback()
        self.close_dialog()
    
    def close_dialog(self):
        """Close the dialog"""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None


def show_email_test_results(parent, test_results: Dict):
    """Convenience function to show email test results"""
    return EmailTestDialog(parent, test_results)


def show_email_test_progress(parent):
    """Convenience function to show email test progress"""
    return EmailTestProgressDialog(parent)
