"""
ui/SettingsDialog.py
Settings dialog for configuring application parameters.
Provides tabbed interface for Camera, Google Drive, Recognition, and General settings.
Saves settings to settings.json via SettingsManager.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from SettingsManager import get_settings_manager
from config import (
    COLOR_PRIMARY_BG, COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_INFO,
    FONT_DIALOG_TITLE, FONT_LABEL, FONT_BUTTON
)


class SettingsDialog:
    """
    Settings dialog with tabbed interface.
    Allows user to configure camera, recognition, and other parameters.
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.settings_manager = get_settings_manager()
        
        self._create_dialog()
        self._create_tabs()
        self._load_current_settings()
    
    def _create_dialog(self):
        """Create main dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x550")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Title
        tk.Label(
            self.dialog,
            text="Application Settings",
            font=FONT_DIALOG_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=15
        ).pack()
    
    def _create_tabs(self):
        """Create tabbed notebook interface."""
        # Notebook (tabbed interface) with better styling
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure tab colors for better readability
        style.configure('TNotebook', 
                       background=COLOR_PRIMARY_BG,
                       borderwidth=0)
        
        style.configure('TNotebook.Tab', 
                       background=COLOR_SECONDARY_BG,
                       foreground='white',  # White text for better contrast
                       padding=[15, 8],
                       font=('Helvetica', 10, 'bold'))
        
        style.map('TNotebook.Tab',
                 background=[('selected', COLOR_INFO)],  # Highlighted when selected
                 foreground=[('selected', 'white')])
        
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create tabs
        self._create_camera_tab()
        self._create_drive_tab()
        self._create_recognition_tab()
        self._create_general_tab()
        
        # Buttons at bottom
        self._create_buttons()
    
    def _create_camera_tab(self):
        """Create Camera settings tab."""
        tab = tk.Frame(self.notebook, bg=COLOR_SECONDARY_BG)
        self.notebook.add(tab, text="Camera")
        
        # Camera URL/Index
        self._create_label(tab, "Camera Source:", 0)
        
        url_frame = tk.Frame(tab, bg=COLOR_SECONDARY_BG)
        url_frame.grid(row=1, column=0, columnspan=2, pady=5, padx=20, sticky='ew')
        
        self.camera_url_var = tk.StringVar()
        self.camera_entry = tk.Entry(
            url_frame,
            textvariable=self.camera_url_var,
            font=FONT_LABEL,
            width=30
        )
        self.camera_entry.pack(side=tk.LEFT, padx=5)
        
        # Preset dropdown
        tk.Label(
            url_frame,
            text="Preset:",
            font=FONT_LABEL,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        self.camera_preset = ttk.Combobox(
            url_frame,
            values=["0 (Webcam)", "1 (External)", "Custom URL"],
            state="readonly",
            width=15
        )
        self.camera_preset.pack(side=tk.LEFT, padx=5)
        self.camera_preset.bind('<<ComboboxSelected>>', self._on_preset_change)
        
        # Help text
        help_text = "Use 0 for default webcam, 1 for external camera,\nor enter full IP camera URL (e.g., rtsp://...)"
        self._create_help_text(tab, help_text, 2)
        
        # Test Camera button
        tk.Button(
            tab,
            text="Test Camera",
            command=self._test_camera,
            font=FONT_BUTTON,
            bg=COLOR_INFO,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=5
        ).grid(row=3, column=0, columnspan=2, pady=20)
        
        # Flip Horizontal
        self._create_label(tab, "Flip Camera Horizontally (Mirror Mode):", 4)
        
        self.flip_var = tk.BooleanVar()
        tk.Checkbutton(
            tab,
            text="Enable flip (recommended for webcams)",
            variable=self.flip_var,
            font=FONT_LABEL,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            selectcolor=COLOR_PRIMARY_BG,
            activebackground=COLOR_SECONDARY_BG,
            activeforeground=COLOR_TEXT_PRIMARY
        ).grid(row=5, column=0, columnspan=2, pady=5, padx=20, sticky='w')
        
        # Capture Frame Count
        self._create_label(tab, "Capture Frame Count:", 6)
        self._create_help_text(tab, "Number of frames to capture for stable detection (1-10)", 7)
        
        frame_frame = tk.Frame(tab, bg=COLOR_SECONDARY_BG)
        frame_frame.grid(row=8, column=0, columnspan=2, pady=5, padx=20)
        
        self.frame_count_var = tk.IntVar()
        tk.Spinbox(
            frame_frame,
            from_=1,
            to=10,
            textvariable=self.frame_count_var,
            font=FONT_LABEL,
            width=10
        ).pack()
    
    def _create_drive_tab(self):
        """Create Google Drive settings tab."""
        tab = tk.Frame(self.notebook, bg=COLOR_SECONDARY_BG)
        self.notebook.add(tab, text="Google Drive")
        
        # Google Drive URL
        self._create_label(tab, "Google Drive Folder URL:", 0)
        
        self.drive_url_var = tk.StringVar()
        tk.Entry(
            tab,
            textvariable=self.drive_url_var,
            font=FONT_LABEL,
            width=50
        ).grid(row=1, column=0, pady=5, padx=20, sticky='ew')
        
        # Help text
        help_text = (
            "Enter the full Google Drive folder URL containing student zip files.\n"
            "Example: https://drive.google.com/drive/folders/xxxxxxxxxxxxx\n\n"
            "IMPORTANT: The folder must be set to 'Anyone with the link can view'"
        )
        self._create_help_text(tab, help_text, 2)
        
        # Test Connection button (placeholder for now)
        tk.Button(
            tab,
            text="Test Connection",
            command=self._test_drive_connection,
            font=FONT_BUTTON,
            bg=COLOR_INFO,
            fg=COLOR_TEXT_PRIMARY,
            padx=15,
            pady=5
        ).grid(row=3, column=0, pady=20)
        
        tab.grid_columnconfigure(0, weight=1)
    
    def _create_recognition_tab(self):
        """Create Recognition settings tab."""
        tab = tk.Frame(self.notebook, bg=COLOR_SECONDARY_BG)
        self.notebook.add(tab, text="Recognition")
        
        # Confidence Threshold
        self._create_label(tab, "Confidence Threshold:", 0)
        self._create_help_text(
            tab,
            "Higher = stricter matching, fewer false positives. Recommended: 0.4 - 0.6",
            1
        )
        
        threshold_frame = tk.Frame(tab, bg=COLOR_SECONDARY_BG)
        threshold_frame.grid(row=2, column=0, pady=10, padx=20)
        
        self.confidence_var = tk.DoubleVar()
        self.confidence_scale = tk.Scale(
            threshold_frame,
            from_=0.3,
            to=0.9,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            variable=self.confidence_var,
            font=FONT_LABEL,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            highlightthickness=0,
            length=300
        )
        self.confidence_scale.pack(side=tk.LEFT, padx=10)
        
        self.confidence_label = tk.Label(
            threshold_frame,
            text="0.50",
            font=FONT_LABEL,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            width=5
        )
        self.confidence_label.pack(side=tk.LEFT, padx=5)
        
        self.confidence_scale.config(command=self._update_confidence_label)
        
        # Minimum Face Size
        self._create_label(tab, "Minimum Face Size (pixels):", 3)
        self._create_help_text(
            tab,
            "Smaller = detect distant faces but slower. Recommended: 20-40",
            4
        )
        
        size_frame = tk.Frame(tab, bg=COLOR_SECONDARY_BG)
        size_frame.grid(row=5, column=0, pady=10, padx=20)
        
        self.min_face_size_var = tk.IntVar()
        tk.Spinbox(
            size_frame,
            from_=10,
            to=100,
            textvariable=self.min_face_size_var,
            font=FONT_LABEL,
            width=10
        ).pack()
        
        # Live Detection Frame Skip
        self._create_label(tab, "Live Feed Frame Skip:", 6)
        self._create_help_text(
            tab,
            "Higher = less CPU usage but less responsive. Recommended: 50-150",
            7
        )
        
        skip_frame = tk.Frame(tab, bg=COLOR_SECONDARY_BG)
        skip_frame.grid(row=8, column=0, pady=10, padx=20)
        
        self.frame_skip_var = tk.IntVar()
        tk.Spinbox(
            skip_frame,
            from_=10,
            to=200,
            increment=10,
            textvariable=self.frame_skip_var,
            font=FONT_LABEL,
            width=10
        ).pack()
        
        tab.grid_columnconfigure(0, weight=1)
    
    def _create_general_tab(self):
        """Create General settings tab."""
        tab = tk.Frame(self.notebook, bg=COLOR_SECONDARY_BG)
        self.notebook.add(tab, text="General")
        
        # Attendance Mark
        self._create_label(tab, "Attendance Mark Symbol:", 0)
        self._create_help_text(
            tab,
            "Symbol used in Excel to mark attendance (e.g., ✓, P, X)",
            1
        )
        
        mark_frame = tk.Frame(tab, bg=COLOR_SECONDARY_BG)
        mark_frame.grid(row=2, column=0, pady=10, padx=20)
        
        self.attendance_mark_var = tk.StringVar()
        tk.Entry(
            mark_frame,
            textvariable=self.attendance_mark_var,
            font=FONT_LABEL,
            width=10
        ).pack()
        
        # Window Size
        self._create_label(tab, "Main Window Size:", 3)
        
        size_frame = tk.Frame(tab, bg=COLOR_SECONDARY_BG)
        size_frame.grid(row=4, column=0, pady=10, padx=20)
        
        tk.Label(
            size_frame,
            text="Width:",
            font=FONT_LABEL,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=5)
        
        self.window_width_var = tk.IntVar()
        tk.Spinbox(
            size_frame,
            from_=800,
            to=1920,
            increment=50,
            textvariable=self.window_width_var,
            font=FONT_LABEL,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            size_frame,
            text="Height:",
            font=FONT_LABEL,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=(20, 5))
        
        self.window_height_var = tk.IntVar()
        tk.Spinbox(
            size_frame,
            from_=600,
            to=1080,
            increment=50,
            textvariable=self.window_height_var,
            font=FONT_LABEL,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        tab.grid_columnconfigure(0, weight=1)
    
    def _create_buttons(self):
        """Create bottom action buttons."""
        button_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        button_frame.pack(pady=15)
        
        tk.Button(
            button_frame,
            text="Save Settings",
            command=self._save_settings,
            font=FONT_BUTTON,
            bg=COLOR_SUCCESS,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
            font=FONT_BUTTON,
            bg=COLOR_WARNING,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            font=FONT_BUTTON,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=10)
    
    def _create_label(self, parent, text, row):
        """Helper to create consistent labels."""
        tk.Label(
            parent,
            text=text,
            font=FONT_LABEL,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            anchor='w'
        ).grid(row=row, column=0, pady=(15, 5), padx=20, sticky='w')
    
    def _create_help_text(self, parent, text, row):
        """Helper to create help text labels."""
        tk.Label(
            parent,
            text=text,
            font=("Helvetica", 9),
            bg=COLOR_SECONDARY_BG,
            fg="#95a5a6",
            anchor='w',
            justify=tk.LEFT,
            wraplength=520
        ).grid(row=row, column=0, pady=2, padx=20, sticky='w')
    
    def _load_current_settings(self):
        """Load current settings into the UI."""
        # Camera settings
        camera_url = self.settings_manager.get("CAMERA_URL", 0)
        self.camera_url_var.set(str(camera_url))
        
        # Set preset based on current value
        if camera_url == 0:
            self.camera_preset.set("0 (Webcam)")
        elif camera_url == 1:
            self.camera_preset.set("1 (External)")
        else:
            self.camera_preset.set("Custom URL")
        
        self.flip_var.set(self.settings_manager.get("FLIP_HORIZONTAL", 1) == 1)
        self.frame_count_var.set(self.settings_manager.get("CAPTURE_FRAME_COUNT", 3))
        
        # Drive settings
        self.drive_url_var.set(
            self.settings_manager.get("GOOGLE_DRIVE_FOLDER_URL", "")
        )
        
        # Recognition settings
        confidence = self.settings_manager.get("CONFIDENCE_THRESHOLD", 0.5)
        self.confidence_var.set(confidence)
        self.confidence_label.config(text=f"{confidence:.2f}")
        
        self.min_face_size_var.set(self.settings_manager.get("MIN_FACE_SIZE", 20))
        self.frame_skip_var.set(self.settings_manager.get("LIVE_DETECTION_FRAME_SKIP", 100))
        
        # General settings
        self.attendance_mark_var.set(self.settings_manager.get("ATTENDANCE_MARK", "✓"))
        self.window_width_var.set(self.settings_manager.get("WINDOW_WIDTH", 900))
        self.window_height_var.set(self.settings_manager.get("WINDOW_HEIGHT", 700))
    
    def _on_preset_change(self, event):
        """Handle camera preset selection."""
        preset = self.camera_preset.get()
        if preset == "0 (Webcam)":
            self.camera_url_var.set("0")
        elif preset == "1 (External)":
            self.camera_url_var.set("1")
        # For "Custom URL", leave entry as-is
    
    def _update_confidence_label(self, value):
        """Update confidence threshold label."""
        self.confidence_label.config(text=f"{float(value):.2f}")
    
    def _test_camera(self):
        """Test camera connection."""
        camera_url = self.camera_url_var.get()
        
        # Try to parse as integer (for index)
        try:
            camera_source = int(camera_url)
        except ValueError:
            camera_source = camera_url
        
        try:
            cap = cv2.VideoCapture(camera_source)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    messagebox.showinfo(
                        "Success",
                        f"Camera '{camera_source}' connected successfully!",
                        parent=self.dialog
                    )
                else:
                    messagebox.showwarning(
                        "Warning",
                        f"Camera opened but failed to capture frame.",
                        parent=self.dialog
                    )
            else:
                messagebox.showerror(
                    "Error",
                    f"Failed to open camera '{camera_source}'.\n\nCheck camera index/URL and try again.",
                    parent=self.dialog
                )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Camera test failed:\n{str(e)}",
                parent=self.dialog
            )
    
    def _test_drive_connection(self):
        """Test Google Drive connection (basic URL validation)."""
        url = self.drive_url_var.get()
        
        if not url:
            messagebox.showwarning(
                "Warning",
                "Please enter a Google Drive folder URL.",
                parent=self.dialog
            )
            return
        
        if "drive.google.com" not in url:
            messagebox.showwarning(
                "Warning",
                "URL doesn't appear to be a Google Drive link.",
                parent=self.dialog
            )
            return
        
        messagebox.showinfo(
            "Info",
            "URL format looks correct!\n\n"
            "Note: Actual connection will be tested when downloading.\n"
            "Make sure the folder is set to 'Anyone with the link can view'.",
            parent=self.dialog
        )
    
    def _save_settings(self):
        """Save all settings to file."""
        try:
            # Parse camera URL
            camera_url = self.camera_url_var.get()
            try:
                camera_url = int(camera_url)
            except ValueError:
                pass  # Keep as string (URL)
            
            # Update all settings
            settings = {
                "CAMERA_URL": camera_url,
                "FLIP_HORIZONTAL": 1 if self.flip_var.get() else 0,
                "CAPTURE_FRAME_COUNT": self.frame_count_var.get(),
                "GOOGLE_DRIVE_FOLDER_URL": self.drive_url_var.get(),
                "CONFIDENCE_THRESHOLD": self.confidence_var.get(),
                "MIN_FACE_SIZE": self.min_face_size_var.get(),
                "MTCNN_MIN_FACE_SIZE": self.min_face_size_var.get(),
                "LIVE_DETECTION_FRAME_SKIP": self.frame_skip_var.get(),
                "ATTENDANCE_MARK": self.attendance_mark_var.get(),
                "WINDOW_WIDTH": self.window_width_var.get(),
                "WINDOW_HEIGHT": self.window_height_var.get(),
            }
            
            self.settings_manager.update_multiple(settings)
            success = self.settings_manager.save()
            
            if success:
                messagebox.showinfo(
                    "Settings Saved",
                    "Settings saved successfully!\n\n"
                    "⚠️ IMPORTANT: You must restart the application\n"
                    "for most settings to take effect.\n\n"
                    "Close and reopen the app now.",
                    parent=self.dialog
                )
                self.dialog.destroy()
            else:
                messagebox.showerror(
                    "Error",
                    "Failed to save settings to file.",
                    parent=self.dialog
                )
        
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to save settings:\n{str(e)}",
                parent=self.dialog
            )
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        response = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset all settings to defaults?\n\n"
            "This cannot be undone.",
            parent=self.dialog
        )
        
        if response:
            self.settings_manager.reset_to_defaults()
            self.settings_manager.save()
            self._load_current_settings()
            
            messagebox.showinfo(
                "Success",
                "Settings reset to defaults!\n\n"
                "⚠️ Restart the application for changes to take effect.",
                parent=self.dialog
            )
    
    def _cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog."""
        self.dialog.wait_window()