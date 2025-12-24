"""
ui/DateSelectionDialog.py
Date selection dialog for attendance taking.
Provides calendar-style date picker with "Use Today's Date" quick option.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from config import (
    COLOR_PRIMARY_BG, COLOR_SUCCESS, COLOR_INFO,
    FONT_DIALOG_TITLE, FONT_BUTTON, COLOR_TEXT_PRIMARY
)


class DateSelectionDialog:
    """Dialog for selecting attendance date."""
    
    def __init__(self, parent):
        self.parent = parent
        self.selected_date = None
        
        self._create_dialog()
        self._create_widgets()
    
    def _create_dialog(self):
        """Create dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Select Attendance Date")
        self.dialog.geometry("400x300")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _create_widgets(self):
        """Create dialog widgets."""
        # Title
        tk.Label(
            self.dialog,
            text="Select Attendance Date",
            font=FONT_DIALOG_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=20
        ).pack()
        
        # Date entry frame
        date_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        date_frame.pack(pady=20)
        
        tk.Label(
            date_frame,
            text="Date (YYYY-MM-DD):",
            font=("Helvetica", 12),
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=5)
        
        # Date entry
        self.date_entry = tk.Entry(
            date_frame,
            font=("Helvetica", 12),
            width=15
        )
        self.date_entry.pack(side=tk.LEFT, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.focus()
        
        # Use today button
        tk.Button(
            self.dialog,
            text="Use Today's Date",
            command=self._use_today,
            font=FONT_BUTTON,
            bg=COLOR_INFO,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=10
        ).pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        button_frame.pack(pady=20)
        
        # Confirm button
        tk.Button(
            button_frame,
            text="Confirm",
            command=self._confirm,
            font=FONT_BUTTON,
            bg=COLOR_SUCCESS,
            fg=COLOR_TEXT_PRIMARY,
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        # Cancel button
        tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            font=FONT_BUTTON,
            bg="#e74c3c",
            fg=COLOR_TEXT_PRIMARY,
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=10)
        
        # Bind Enter key
        self.date_entry.bind('<Return>', lambda e: self._confirm())
    
    def _use_today(self):
        """Set today's date in entry."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, today)
    
    def _confirm(self):
        """Confirm date selection."""
        date_str = self.date_entry.get().strip()
        
        # Validate date format
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            self.selected_date = date_str
            self.dialog.destroy()
        except ValueError:
            tk.messagebox.showerror(
                "Invalid Date",
                "Please enter date in YYYY-MM-DD format",
                parent=self.dialog
            )
    
    def _cancel(self):
        """Cancel date selection."""
        self.selected_date = None
        self.dialog.destroy()
    
    def show(self):
        """
        Show dialog and wait for user input.
        
        Returns:
            str: Selected date in YYYY-MM-DD format, or None if cancelled
        """
        self.dialog.wait_window()
        return self.selected_date