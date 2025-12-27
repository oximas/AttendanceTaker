"""
ui/WelcomeDialog.py
Welcome dialog shown on first run.
Guides users through initial setup and configuration.
"""

import tkinter as tk
from config import (
    COLOR_PRIMARY_BG, COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY,
    COLOR_SUCCESS, FONT_DIALOG_TITLE, FONT_LABEL
)


class WelcomeDialog:
    """Welcome dialog for first-time users."""
    
    def __init__(self, parent):
        self.parent = parent
        self._create_dialog()
        self._create_widgets()
    
    def _create_dialog(self):
        """Create welcome dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Welcome to AttendanceTracker")
        self.dialog.geometry("600x550")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _create_widgets(self):
        """Create welcome screen widgets."""
        # Title
        tk.Label(
            self.dialog,
            text="🎓 Welcome to AttendanceTracker!",
            font=("Helvetica", 22, "bold"),
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=20
        ).pack()
        
        # Subtitle
        tk.Label(
            self.dialog,
            text="Face Recognition Attendance System",
            font=("Helvetica", 12),
            bg=COLOR_PRIMARY_BG,
            fg="#95a5a6",
            pady=5
        ).pack()
        
        # Main content frame
        content_frame = tk.Frame(
            self.dialog,
            bg=COLOR_SECONDARY_BG,
            relief=tk.SOLID,
            bd=1
        )
        content_frame.pack(pady=20, padx=30, fill=tk.BOTH, expand=True)
        
        # Welcome message
        welcome_text = tk.Text(
            content_frame,
            wrap=tk.WORD,
            font=("Helvetica", 11),
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            height=15,
            relief=tk.FLAT,
            padx=20,
            pady=20
        )
        welcome_text.pack(fill=tk.BOTH, expand=True)
        
        message = """
Thank you for using AttendanceTracker!

This is your first time running the application. Here's what you need to do to get started:


📷 STEP 1: Configure Camera
   • Go to Settings → Preferences → Camera tab
   • Select your camera (0 for webcam, 1 for external, or a link for an IP camera)
   • Click "Test Camera" to verify it works


📁 STEP 2: Set Google Drive Folder
   • Go to Settings → Preferences → Google Drive tab
   • Paste your Google Drive folder URL (this should aready be done so don't change it)
   • Make sure folder is PUBLIC (Anyone with link can view)


👥 STEP 3: Add Students
   • Go to Students → Manage Students
   • Add students manually, or
   • Import from CSV file


📥 STEP 4: Download Training Images
   • Prepare ZIP files: StudentName_StudentID.zip
   • Upload to your Google Drive folder (usually done by students through form in the next step)
   • IMPORTANT: Give this form to the students to fill "https://forms.gle/zuRh9mFjisL9mnR7A"
   • after you get the student data, Click "Download & Process Images" button
   • Wait for automatic training (this step will take a couple of minutes depending on internet and computer speed, fist time is usually slower)


✅ You're Ready!
   • Click "Capture and Detect" to recognize faces
   • Click Students → Take Attendance to mark present
   • View records anytime in Attendance Records


Need help? Click Help → Quick Start or Troubleshooting
"""
        
        welcome_text.insert('1.0', message)
        welcome_text.config(state=tk.DISABLED)
        
        # Button
        tk.Button(
            self.dialog,
            text="Got It! Let's Start",
            command=self.dialog.destroy,
            font=("Helvetica", 12, "bold"),
            bg=COLOR_SUCCESS,
            fg=COLOR_TEXT_PRIMARY,
            padx=30,
            pady=12
        ).pack(pady=20)
    
    def show(self):
        """Show the welcome dialog."""
        self.dialog.wait_window()