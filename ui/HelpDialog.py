"""
ui/HelpDialog.py
Help dialog with Quick Start guide and Troubleshooting section.
Provides user-friendly documentation and common issue solutions.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from config import (
    COLOR_PRIMARY_BG, COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY,
    FONT_DIALOG_TITLE, FONT_LABEL
)


class HelpDialog:
    """Help dialog with tabbed interface."""
    
    def __init__(self, parent):
        self.parent = parent
        self._create_dialog()
        self._create_tabs()
    
    def _create_dialog(self):
        """Create main dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Help")
        self.dialog.geometry("700x600")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _create_tabs(self):
        """Create tabbed help interface."""
        # Title
        tk.Label(
            self.dialog,
            text="AttendanceTracker Help",
            font=FONT_DIALOG_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=15
        ).pack()
        
        # Notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=COLOR_PRIMARY_BG, borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=COLOR_SECONDARY_BG,
                       foreground='white',
                       padding=[15, 8],
                       font=('Helvetica', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', '#3498db')],
                 foreground=[('selected', 'white')])
        
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create tabs
        self._create_quick_start_tab(notebook)
        self._create_troubleshooting_tab(notebook)
        self._create_about_tab(notebook)
        
        # Close button
        tk.Button(
            self.dialog,
            text="Close",
            command=self.dialog.destroy,
            font=("Helvetica", 12, "bold"),
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=30,
            pady=8
        ).pack(pady=10)
    
    def _create_quick_start_tab(self, notebook):
        """Create Quick Start guide tab."""
        tab = tk.Frame(notebook, bg=COLOR_SECONDARY_BG)
        notebook.add(tab, text="Quick Start")
        
        text_area = scrolledtext.ScrolledText(
            tab,
            wrap=tk.WORD,
            font=("Helvetica", 10),
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=15
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        quick_start_text = """
QUICK START GUIDE

═══════════════════════════════════════════════════════════

1. FIRST TIME SETUP

   a) Configure Settings:
      • Go to Settings → Preferences
      • Set your camera (0 for webcam, 1 for external, link for IP camera in your Phone)
      • Set Google Drive folder URL (must be public)
      • Adjust confidence threshold (0.4-0.6 recommended)
      • Click Save and restart app

   b) Add Students to Database:
      • Go to Students → Manage Students
      • Click "Add Student"
      • Enter Student ID (numeric) and Name
      • Or use "Import from CSV" for bulk upload

═══════════════════════════════════════════════════════════

2. DOWNLOAD STUDENT IMAGES

   • Collect student images in Google Drive (usually done through this form by the students "https://forms.gle/zuRh9mFjisL9mnR7A"):
     - send this form to the students to fill "https://forms.gle/zuRh9mFjisL9mnR7A" or do it Manually
     - NOTE: if you do use the Form given use the default given google drive (dont change unless you know what you are doing)
     - Create one ZIP file per student
     - Name format: StudentName_StudentID.zip
     - Example: Ahmed-Mohamed_12345.zip
     - Each ZIP contains 3-10 photos of the student
     - Make folder PUBLIC ("Anyone with link can view")

   • In the app, click "Download & Process Images"
   • Wait for download and face extraction
   • Model trains automatically

═══════════════════════════════════════════════════════════

3. TAKE ATTENDANCE

   a) Make sure model is trained (check status bar)
   
   b) Click "Capture and Detect"
      • Students stand in front of camera
      • App captures and recognizes faces
      • Opens window showing recognized students
   
   c) Click Students → Take Attendance
      • Select date
      • Confirm attendance marking
      • Check Students → View Attendance Records

═══════════════════════════════════════════════════════════

4. VIEW ATTENDANCE

   • Go to Students → View Attendance Records
   • Select a date or view multiple dates
   • Export reports as CSV or Excel

═══════════════════════════════════════════════════════════

5. TIPS FOR BEST RESULTS

   • Good lighting is essential
   • Students should face camera directly
   • One face per photo in training images
   • 5-10 photos per student recommended
   • Avoid sunglasses, masks in training photos
   • Set confidence to 0.5 (adjust if needed)

═══════════════════════════════════════════════════════════
"""
        
        text_area.insert('1.0', quick_start_text)
        text_area.config(state=tk.DISABLED)
    
    def _create_troubleshooting_tab(self, notebook):
        """Create Troubleshooting tab."""
        tab = tk.Frame(notebook, bg=COLOR_SECONDARY_BG)
        notebook.add(tab, text="Troubleshooting")
        
        text_area = scrolledtext.ScrolledText(
            tab,
            wrap=tk.WORD,
            font=("Helvetica", 10),
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=15
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        troubleshooting_text = """
TROUBLESHOOTING GUIDE

═══════════════════════════════════════════════════════════

PROBLEM: Camera doesn't work / "Failed to open camera"

SOLUTIONS:
✓ Check camera is plugged in and working in other apps
✓ Go to Settings → Preferences → Camera
✓ Try different camera index (0, 1, 2)
✓ Click "Test Camera" button to verify
✓ Close other apps using the camera
✓ Restart the application
✓ Check app.log file for detailed error

═══════════════════════════════════════════════════════════

PROBLEM: Download from Google Drive fails

SOLUTIONS:
✓ Make sure folder is set to PUBLIC
  (Right-click folder → Share → Anyone with link can view)
✓ Check folder URL is correct in Settings
✓ Check internet connection
✓ Try copying folder URL again from browser
✓ Make sure ZIP files follow naming: Name_ID.zip
✓ Check wrong_student_name_format.txt for errors

═══════════════════════════════════════════════════════════

PROBLEM: Face recognition not working / "Unknown" faces

SOLUTIONS:
✓ Check if model is trained (status bar shows green)
✓ Make sure students are in database (Manage Students)
✓ Training images should be clear, well-lit
✓ One face per training image
✓ 5-10 images per student recommended
✓ Try adjusting confidence threshold:
  - Lower (0.4): More lenient, might have false positives
  - Higher (0.6): Stricter, might miss some faces
✓ Retrain model after adding new students

═══════════════════════════════════════════════════════════

PROBLEM: Faces not detected in live feed

SOLUTIONS:
✓ Check lighting - need good, even lighting
✓ Face camera directly, avoid angles
✓ Move closer to camera
✓ Remove sunglasses, hats, masks
✓ Try adjusting "Min Face Size" in Settings
✓ Check if bounding boxes appear (green rectangles)

═══════════════════════════════════════════════════════════

PROBLEM: App is slow / laggy

SOLUTIONS:
✓ Go to Settings → Recognition
✓ Increase "Live Feed Frame Skip" (50-150)
✓ Close other programs
✓ Use lower resolution camera if possible
✓ Check CPU usage in Task Manager

═══════════════════════════════════════════════════════════

PROBLEM: Model says "Needs Training"

SOLUTIONS:
✓ Download student images first
✓ Run "Download & Process Images"
✓ Wait for automatic training to complete
✓ If already downloaded, model trains automatically
✓ Check app.log for training errors

═══════════════════════════════════════════════════════════

PROBLEM: Student ID format errors during import

SOLUTIONS:
✓ ZIP filename must be: Name_ID.zip
✓ ID must be numeric only (no letters)
✓ Use underscore (_) to separate name and ID
✓ Example: Ahmed-Hassan_12345.zip ✓
✓ Example: Ahmed Hassan 12345.zip ✗ (wrong)
✓ Check wrong_student_name_format.txt for failed files

═══════════════════════════════════════════════════════════

PROBLEM: Attendance not saving to Excel

SOLUTIONS:
✓ Check Excel file is not open in another program
✓ Make sure students exist in database first
✓ Check file permissions in Attendance_Data folder
✓ Verify student IDs match database
✓ Check app.log for errors

═══════════════════════════════════════════════════════════

STILL HAVING ISSUES?

1. Check the app.log file in program folder
2. Look for error messages (lines with [ERROR])
3. Contact support: oximas2004@gmail.com
4. Include app.log file in your email

═══════════════════════════════════════════════════════════
"""
        
        text_area.insert('1.0', troubleshooting_text)
        text_area.config(state=tk.DISABLED)
    
    def _create_about_tab(self, notebook):
        """Create About tab."""
        tab = tk.Frame(notebook, bg=COLOR_SECONDARY_BG)
        notebook.add(tab, text="About")
        
        about_frame = tk.Frame(tab, bg=COLOR_SECONDARY_BG)
        about_frame.pack(expand=True, pady=50)
        
        tk.Label(
            about_frame,
            text="AttendanceTracker",
            font=("Helvetica", 24, "bold"),
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(pady=10)
        
        tk.Label(
            about_frame,
            text="Version 0.9-beta",
            font=("Helvetica", 14),
            bg=COLOR_SECONDARY_BG,
            fg="#95a5a6"
        ).pack(pady=5)
        
        tk.Label(
            about_frame,
            text="Face Recognition Attendance System",
            font=("Helvetica", 12),
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(pady=15)
        
        tk.Label(
            about_frame,
            text="Automated student attendance tracking\nusing real-time face recognition",
            font=("Helvetica", 11),
            bg=COLOR_SECONDARY_BG,
            fg="#95a5a6",
            justify=tk.CENTER
        ).pack(pady=10)
        
        tk.Label(
            about_frame,
            text="━━━━━━━━━━━━━━━━━━━━━━━━",
            font=("Helvetica", 10),
            bg=COLOR_SECONDARY_BG,
            fg="#95a5a6"
        ).pack(pady=15)
        
        tk.Label(
            about_frame,
            text="Support: oximas2004@gmail.com",
            font=("Helvetica", 11),
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(pady=5)
        
        tk.Label(
            about_frame,
            text="Powered by FaceNet, MTCNN, OpenCV",
            font=("Helvetica", 9),
            bg=COLOR_SECONDARY_BG,
            fg="#95a5a6"
        ).pack(pady=10)
    
    def show(self):
        """Show the dialog."""
        self.dialog.wait_window()