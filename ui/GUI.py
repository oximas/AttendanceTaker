"""
ui/GUI.py
Main GUI application with complete feature set including:
- Automatic training detection on startup
- Image upload with face detection
- Enhanced attendance notifications
- Manual training option
All training workflows properly integrated.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
import threading
import time

from services.FaceRecognitionService import FaceRecognitionService
from services.FaceExtractionPipeline import FaceExtractionPipeline
from services.ImageDownloader import ImageDownloadManager
from ui.UIComponents import FaceNamingDialog, StatusBar, ImageDisplay, ButtonPanel
from ui.DateSelectionDialog import DateSelectionDialog
from ui.SettingsDialog import SettingsDialog
from ui.StudentManagementDialog import StudentManagementDialog
from ui.AttendanceViewerDialog import AttendanceViewerDialog
from ui.HelpDialog import HelpDialog
from ui.WelcomeDialog import WelcomeDialog
from logger import log_info, log_warning, log_error
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_PRIMARY_BG,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_INFO,
    COLOR_PURPLE, COLOR_TEAL, FONT_TITLE, FONT_SUBTITLE,
    CAMERA_URL, DOWNLOADS_DIR, GOOGLE_DRIVE_FOLDER_URL,
    CAPTURE_WINDOW_WIDTH, CAPTURE_WINDOW_HEIGHT, CAPTURE_FRAME_COUNT,
    ATTENDANCE_EXCEL_FILE
)


class ProcessingDialog:
    """Dialog to show processing progress with scrollable text output."""
    
    def __init__(self, parent, title="Processing"):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x400")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        tk.Label(
            self.dialog,
            text=title,
            font=FONT_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg="white",
            pady=10
        ).pack()
        
        self.text_area = scrolledtext.ScrolledText(
            self.dialog,
            wrap=tk.WORD,
            width=70,
            height=20,
            font=("Courier", 9),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.text_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.close_btn = tk.Button(
            self.dialog,
            text="Close",
            command=self.close,
            font=("Helvetica", 12, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            padx=20,
            pady=5,
            state=tk.DISABLED
        )
        self.close_btn.pack(pady=10)
    
    def append(self, text):
        """Append text to the dialog."""
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)
        self.dialog.update()
    
    def enable_close(self):
        """Enable the close button."""
        self.close_btn.config(state=tk.NORMAL)
    
    def close(self):
        """Close the dialog."""
        self.dialog.destroy()


class CaptureWindow:
    """External window to display captured and annotated images."""
    
    def __init__(self, parent, image, title="Captured Image"):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry(f"{CAPTURE_WINDOW_WIDTH}x{CAPTURE_WINDOW_HEIGHT}")
        self.window.configure(bg=COLOR_PRIMARY_BG)
        
        tk.Label(
            self.window,
            text=title,
            font=FONT_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg="white",
            pady=10
        ).pack()
        
        self.image_label = tk.Label(self.window, bg=COLOR_PRIMARY_BG)
        self.image_label.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        self.show_image(image)
    
    def show_image(self, pil_image):
        """Display PIL image in window."""
        if pil_image is None:
            return
        
        img_copy = pil_image.copy()
        img_copy.thumbnail(
            (CAPTURE_WINDOW_WIDTH - 40, CAPTURE_WINDOW_HEIGHT - 80),
            Image.Resampling.LANCZOS
        )
        
        self.photo = ImageTk.PhotoImage(img_copy)
        self.image_label.config(image=self.photo)


class CameraApp:
    """Main application with complete feature set."""
    
    def __init__(self, root, first_run=False):
        self.root = root
        self.first_run = first_run
        self.service = FaceRecognitionService(CAMERA_URL)
        self.current_result = None
        self.current_detected_ids = []
        
        self.live_feed_active = True
        self.live_feed_thread = None
        self.is_training = False
        
        self._setup_window()
        self._create_menu_bar()
        self._create_ui()
        
        if self.first_run:
            self.root.after(500, self._show_welcome)
        
        self._check_initial_state()
        self._check_training_needed()  # NEW: Check if training needed
        self._perform_startup_validation()
        self._start_live_feed()
    
    def _setup_window(self):
        """Configure main window."""
        self.root.title("People Detection Camera")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLOR_PRIMARY_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_menu_bar(self):
        """Create menu bar at top of window."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Upload Image with Faces...", command=self._upload_image)  # NEW
        file_menu.add_separator()
        file_menu.add_command(label="Save Current Capture...", command=self._on_save_image)
        file_menu.add_separator()
        file_menu.add_command(label="Process Downloaded Zip Files", command=self._on_process_zips)
        file_menu.add_separator()
        file_menu.add_command(label="Train Model", command=self._manual_train)  # NEW
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        
        # Students Menu
        students_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Students", menu=students_menu)
        students_menu.add_command(label="Manage Students...", command=self._manage_students)
        students_menu.add_command(label="Take Attendance", command=self._on_take_attendance)
        students_menu.add_separator()
        students_menu.add_command(label="View Attendance Records...", command=self._view_attendance)
        
        # Settings Menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences...", command=self._open_settings)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Start Guide", command=self._show_help)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_ui(self):
        """Create all UI components."""
        self._create_title()
        self._create_button_panels()
        self._create_count_label()
        self._create_model_status_label()
        self.image_display = ImageDisplay(self.root)
        self.status_bar = StatusBar(self.root)
    
    def _create_title(self):
        """Create title label."""
        tk.Label(
            self.root,
            text="People Detection System - Live Feed",
            font=FONT_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg="white",
            pady=20
        ).pack()
    
    def _create_button_panels(self):
        """Create button control panels."""
        self.main_panel = ButtonPanel(self.root)
        self.main_panel.add_button(
            "capture", "Capture and Detect",
            self._on_capture, COLOR_INFO, 0
        )
        
        self.download_panel = ButtonPanel(self.root)
        self.download_panel.add_button(
            "download_process", "Download & Process Images",
            self._on_download_and_process, "#e67e22", 0
        )
        
        self.attendance_panel = ButtonPanel(self.root)
        self.attendance_panel.add_button(
            "take_attendance", "Take Attendance",
            self._on_take_attendance, COLOR_TEAL, 0, enabled=False
        )
    
    def _create_count_label(self):
        """Create people count label."""
        from config import COLOR_TEXT_SECONDARY
        
        self.count_label = tk.Label(
            self.root,
            text="Live Feed - People Count: 0",
            font=FONT_SUBTITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_SECONDARY,
            pady=10
        )
        self.count_label.pack(pady=5)
    
    def _create_model_status_label(self):
        """Create model status indicator label."""
        self.model_status_label = tk.Label(
            self.root,
            text="Model Status: Checking...",
            font=("Helvetica", 11),
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_INFO,
            pady=5
        )
        self.model_status_label.pack(pady=5)
    
    def _update_model_status(self):
        """Update model status label with current information."""
        status = self.service.get_model_status()
        
        if not status['has_model']:
            text = "Model Status: Not Trained"
            color = COLOR_WARNING
        elif status['needs_training']:
            text = f"Model Status: Needs Update ({status['reason']})"
            color = COLOR_WARNING
        else:
            text = f"Model Status: Ready ✓ ({status['trained_students']} students)"
            color = COLOR_SUCCESS
        
        self.model_status_label.config(text=text, fg=color)
        self.root.update_idletasks()
    
    def _check_initial_state(self):
        """Check initial state and update UI."""
        self._update_model_status()
        
        status = self.service.get_model_status()
        if status['has_model'] and not status['needs_training']:
            self.status_bar.update(
                f"Ready - {status['trained_students']} students in database",
                COLOR_SUCCESS
            )
    
    def _check_training_needed(self):
        """Check if model needs training and prompt user - FIXED for threading."""
        status = self.service.get_model_status()
        
        if status['needs_training']:
            response = messagebox.askyesno(
                "Training Needed",
                f"Model needs training:\n{status['reason']}\n\n"
                f"Current students in Faces folder: {status['current_students']}\n"
                f"Students model trained on: {status['trained_students']}\n\n"
                f"Train model now?",
                parent=self.root
            )
            
            if response:
                # Use root.after to schedule training on main thread
                self.root.after(100, self._train_model_with_dialog, "Startup Training")
    
    def _perform_startup_validation(self):
        """Perform startup validation checks."""
        log_info("Performing startup validation...")
        
        issues = []
        
        try:
            self.service.counter.camera.open()
            ret, frame = self.service.counter.camera.cap.read()
            if not ret or frame is None:
                issues.append("⚠️ Camera opened but failed to capture frame")
                log_warning("Camera test failed: No frame captured")
            else:
                log_info("Camera test passed")
        except Exception as e:
            issues.append(f"❌ Camera Error: {str(e)}")
            log_error("Camera test failed", e)
        
        status = self.service.get_model_status()
        if not status['has_model']:
            issues.append("ℹ️ No trained model found - Download images and train")
            log_warning("No trained model found")
        elif status['needs_training']:
            issues.append(f"ℹ️ Model needs update: {status['reason']}")
            log_warning(f"Model needs training: {status['reason']}")
        else:
            log_info(f"Model ready: {status['trained_students']} students")
        
        from services.StudentDatabase import StudentDatabase
        db = StudentDatabase()
        student_count = db.get_student_count()
        if student_count == 0:
            issues.append("ℹ️ No students in database - Add students to get started")
            log_warning("No students in database")
        else:
            log_info(f"Database has {student_count} students")
        
        if issues:
            self.root.after(1000, lambda: self._show_startup_issues(issues))
        else:
            log_info("All startup validations passed")
    
    def _show_startup_issues(self, issues):
        """Show startup validation issues to user."""
        message = "Startup Validation:\n\n" + "\n".join(issues)
        message += "\n\nThe app will continue running."
        message += "\n\nCheck Help → Quick Start for setup instructions."
        
        messagebox.showinfo(
            "Startup Check",
            message,
            parent=self.root
        )
    
    def _show_welcome(self):
        """Show welcome dialog for first-time users."""
        WelcomeDialog(self.root).show()
    
    def _start_live_feed(self):
        """Start live camera feed with face detection."""
        self.detecting = False
        self.latest_boxes = []
        self.latest_count = 0
        self.service.counter.camera.start_stream()
        self.live_feed_active = True
        self.live_feed_thread = threading.Thread(target=self._live_feed_loop, daemon=True)
        self.live_feed_thread.start()
    
    def _stop_live_feed(self):
        """Stop live camera feed."""
        self.live_feed_active = False
        if self.live_feed_thread:
            self.live_feed_thread.join(timeout=2)
        self.service.counter.camera.stop_stream()
    
    def _live_feed_loop(self):
        """Main live feed loop running in background thread."""
        while self.live_feed_active:
            try:
                frame = self.service.counter.camera.get_current_frame()
                if frame is None:
                    continue

                if not self.detecting:
                    self.detecting = True
                    threading.Thread(
                        target=self._run_detection,
                        args=(frame.copy(),),
                        daemon=True
                    ).start()

                annotated = self.service.counter.processor.draw_bounding_boxes(
                    frame, self.latest_boxes
                )

                pil_image = self._convert_to_pil(annotated)
                self.root.after(
                    0,
                    lambda img=pil_image, cnt=self.latest_count:
                    self._update_live_display(img, cnt)
                )

            except Exception as e:
                log_error("Live feed error", e)
    
    def _update_live_display(self, pil_image, count):
        """Update the live feed display."""
        if self.live_feed_active:
            self.image_display.show_image(pil_image)
            color = COLOR_SUCCESS if count > 0 else COLOR_INFO
            self.count_label.config(
                text=f"Live Feed - People Count: {count}",
                fg=color
            )
    
    def _run_detection(self, frame):
        """Run face detection on a frame."""
        try:
            count, boxes = self.service.counter.detector.detect(frame)
            self.latest_boxes = boxes
            self.latest_count = count
        finally:
            self.detecting = False
    
    def _convert_to_pil(self, cv_image):
        """Convert OpenCV image to PIL."""
        if isinstance(cv_image, np.ndarray):
            if len(cv_image.shape) == 3:
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(cv_image)
        return cv_image
    
    def _train_model_with_dialog(self, title="Training Model"):
        """Train model with progress dialog."""
        if self.is_training:
            log_warning("Training already in progress")
            return False
        
        self.is_training = True
        dialog = ProcessingDialog(self.root, title)
        success = False
        
        def train():
            nonlocal success
            try:
                dialog.append("="*60)
                dialog.append("TRAINING MODEL")
                dialog.append("="*60)
                
                train_result = self.service.train_model_now(
                    progress_callback=dialog.append
                )
                
                dialog.append(f"\n✓ Training complete!")
                dialog.append(f"  Total faces: {train_result['num_faces']}")
                dialog.append(f"  Total students: {train_result['num_students']}")
                
                dialog.append("\n" + "="*60)
                dialog.append("You may close this window now")
                dialog.append("="*60)
                dialog.enable_close()
                
                success = True
                
                self.root.after(0, self._update_model_status)
                self.root.after(0, lambda: self.attendance_panel.enable("take_attendance"))
                
            except Exception as e:
                dialog.append(f"\n✗ Error: {str(e)}")
                dialog.append("\n" + "="*60)
                dialog.append("You may close this window now")
                dialog.append("="*60)
                dialog.enable_close()
                log_error("Training failed", e)
            finally:
                self.is_training = False
        
        thread = threading.Thread(target=train, daemon=True)
        thread.start()
        
        return success
    
    def _manual_train(self):
        """Manual training option from File menu."""
        response = messagebox.askyesno(
            "Train Model",
            "This will train the model with all faces in the Faces folder.\n\n"
            "Continue?",
            parent=self.root
        )
        
        if response:
            self._train_model_with_dialog("Manual Training")
    
    def _upload_image(self):
        """Upload and process a single image with multiple faces."""
        filepath = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ],
            parent=self.root
        )
        
        if not filepath:
            return
        
        try:
            # Load image
            image = cv2.imread(filepath)
            if image is None:
                messagebox.showerror("Error", "Failed to load image")
                return
            
            self.status_bar.update("Detecting faces in uploaded image...", COLOR_INFO)
            
            # Detect faces
            count, boxes = self.service.counter.detector.detect(image)
            
            if count == 0:
                messagebox.showinfo(
                    "No Faces",
                    "No faces detected in the image.",
                    parent=self.root
                )
                return
            
            # Extract faces
            faces = self.service.counter.extract_face_images(image, boxes)
            
            # Store result (similar to capture)
            self.current_result = {
                'image': image,
                'count': count,
                'boxes': boxes,
                'faces': faces
            }
            
            # Create annotated image
            annotated = self.service.create_annotated_image(
                image,
                boxes,
                show_labels=True
            )
            
            # Get detected IDs
            predictions = self.service.recognize_faces(image, boxes)
            self.current_detected_ids = [sid for sid, _, _ in predictions]
            
            # Show in window
            pil_image = self._convert_to_pil(annotated)
            self.capture_window = CaptureWindow(
                self.root,
                pil_image,
                f"Uploaded Image - {count} People Detected"
            )
            
            self.status_bar.update(
                f"Detected {count} people in uploaded image",
                COLOR_SUCCESS
            )
            
            # Check for unknown faces
            self._check_unknown_faces(faces)
            
        except Exception as e:
            self._handle_error("Image upload failed", e)
    
    def _on_capture(self):
        """Handle capture button."""
        try:
            self.status_bar.update("Capturing stable frame...", COLOR_INFO)
            
            frames = self.service.counter.camera.capture_frames(CAPTURE_FRAME_COUNT)
            stable_frame, count, boxes = self.service.counter.detector.find_stable_detection(frames)
            faces = self.service.counter.extract_face_images(stable_frame, boxes)
            
            self.current_result = {
                'image': stable_frame,
                'count': count,
                'boxes': boxes,
                'faces': faces
            }
            
            annotated = self.service.create_annotated_image(
                stable_frame,
                boxes,
                show_labels=True
            )
            
            predictions = self.service.recognize_faces(stable_frame, boxes)
            self.current_detected_ids = [sid for sid, _, _ in predictions]
            
            pil_image = self._convert_to_pil(annotated)
            self.capture_window = CaptureWindow(self.root, pil_image, f"Captured - {count} People Detected")
            
            if count > 0 and self.service.has_trained_model():
                self.attendance_panel.enable("take_attendance")
            else:
                self.attendance_panel.disable("take_attendance")
            
            self.status_bar.update(
                f"Captured {count} people - Window opened",
                COLOR_SUCCESS
            )
            
            self._check_unknown_faces(faces)
            
        except Exception as e:
            self._handle_error("Capture failed", e)
    
    def _check_unknown_faces(self, faces):
        """Check for unknown faces and prompt to name them."""
        unknown = self.service.identify_unknown_faces(faces)
        
        if not unknown:
            return
        
        response = messagebox.askyesno(
            "Unknown Faces",
            f"Found {len(unknown)} unknown face(s).\n\nName them?",
            parent=self.root
        )
        
        if response:
            self._name_unknown_faces(unknown)
    
    def _name_unknown_faces(self, unknown_list):
        """Open dialog to name unknown faces and ALWAYS train after."""
        unknown_faces = [face for _, face in unknown_list]
        
        dialog = FaceNamingDialog(
            self.root,
            unknown_faces,
            on_save_callback=self.service.counter.save_face
        )
        
        student_ids, student_names = dialog.show()
        
        if student_ids:
            named_count = len([sid for sid in student_ids if sid != "Unknown"])
            if named_count > 0:
                messagebox.showinfo(
                    "Faces Saved",
                    f"Saved {named_count} face(s)!\n\nNow training model...",
                    parent=self.root
                )
                
                # ALWAYS train after naming (even if not new students)
                self.status_bar.update(
                    f"Training model with {named_count} additional face(s)...",
                    COLOR_INFO
                )
                self._train_model_with_dialog("Training with Additional Faces")
    
    def _on_download_and_process(self):
        """Handle download and process button."""
        dialog = ProcessingDialog(self.root, "Download & Process Images")
        
        def process():
            try:
                dialog.append("="*60)
                dialog.append("STEP 1: DOWNLOADING IMAGES")
                dialog.append("="*60)
                
                downloader = ImageDownloadManager(DOWNLOADS_DIR)
                result = downloader.download_and_extract(GOOGLE_DRIVE_FOLDER_URL)
                
                if not result.get('success'):
                    error_msg = result.get('error', 'Unknown error')
                    dialog.append(f"\n✗ Download failed: {error_msg}")
                    dialog.append("\n" + "="*60)
                    dialog.append("MANUAL DOWNLOAD INSTRUCTIONS")
                    dialog.append("="*60)
                    dialog.append("1. Open Settings → Preferences → Google Drive")
                    dialog.append("2. Copy the Google Drive folder URL")
                    dialog.append("3. Open the URL in your browser")
                    dialog.append("4. Download all zip files manually")
                    dialog.append("5. Place them in 'Downloaded_Faces' folder")
                    dialog.append("6. Zip file format: StudentName_StudentID.zip")
                    dialog.append("   Example: Ahmed-Hassan_12345.zip")
                    dialog.append("7. Use File → Process Downloaded Zip Files")
                    dialog.append("\n" + "="*60)
                    dialog.append("You may close this window now")
                    dialog.append("="*60)
                    dialog.enable_close()
                    return
                
                dialog.append(f"\n✓ Extracted {result.get('extracted', 0)} student zip files")
                if result.get('invalid_format', 0) > 0:
                    dialog.append(f"⚠  {result['invalid_format']} files had invalid format (logged)")
                
                dialog.append("\n" + "="*60)
                dialog.append("STEP 2: EXTRACTING FACES")
                dialog.append("="*60)
                
                pipeline = FaceExtractionPipeline()
                stats = pipeline.run_pipeline()
                
                if stats['faces_extracted'] > 0:
                    dialog.append("\n" + "="*60)
                    dialog.append("STEP 3: TRAINING MODEL")
                    dialog.append("="*60)
                    
                    train_result = self.service.train_model_now(
                        progress_callback=dialog.append
                    )
                    
                    dialog.append(f"\n✓ Model trained successfully!")
                    dialog.append(f"  Total faces: {train_result['num_faces']}")
                    dialog.append(f"  Total students: {train_result['num_students']}")
                    
                    self.root.after(0, lambda: self.attendance_panel.enable("take_attendance"))
                    self.root.after(0, lambda: self._update_model_status())
                    self.root.after(0, lambda: self.status_bar.update(
                        f"Ready - Model trained on {train_result['num_students']} students", 
                        COLOR_SUCCESS
                    ))
                else:
                    dialog.append("\n⚠ No faces extracted - cannot train model")
                
                dialog.append("\n✓ Processing complete!")
                dialog.append("\n" + "="*60)
                dialog.append("You may close this window now")
                dialog.append("="*60)
                dialog.enable_close()
                
            except Exception as e:
                dialog.append(f"\n✗ Error: {str(e)}")
                log_error("Download and process failed", e)
                dialog.append("\n" + "="*60)
                dialog.append("You may close this window now")
                dialog.append("="*60)
                dialog.enable_close()
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _on_process_zips(self):
        """Process zip files already in Downloaded_Faces folder."""
        dialog = ProcessingDialog(self.root, "Process Downloaded Zip Files")
        
        def process():
            try:
                dialog.append("="*60)
                dialog.append("PROCESSING DOWNLOADED ZIP FILES")
                dialog.append("="*60)
                
                downloader = ImageDownloadManager(DOWNLOADS_DIR)
                stats = downloader._extract_all_zips()
                
                if stats['extracted'] == 0:
                    dialog.append("\n⚠ No zip files found in Downloaded_Faces folder")
                    dialog.append("\nPlace zip files in 'Downloaded_Faces' folder")
                    dialog.append("Format: StudentName_StudentID.zip")
                    dialog.append("Example: Ahmed-Hassan_12345.zip")
                else:
                    dialog.append(f"\n✓ Extracted {stats['extracted']} zip files")
                    if stats['invalid_format'] > 0:
                        dialog.append(f"⚠  {stats['invalid_format']} invalid format")
                    
                    dialog.append("\n" + "="*60)
                    dialog.append("EXTRACTING FACES")
                    dialog.append("="*60)
                    
                    pipeline = FaceExtractionPipeline()
                    face_stats = pipeline.run_pipeline()
                    
                    if face_stats['faces_extracted'] > 0:
                        dialog.append("\n" + "="*60)
                        dialog.append("TRAINING MODEL")
                        dialog.append("="*60)
                        
                        train_result = self.service.train_model_now(
                            progress_callback=dialog.append
                        )
                        
                        dialog.append(f"\n✓ Training complete!")
                        dialog.append(f"  Faces: {train_result['num_faces']}")
                        dialog.append(f"  Students: {train_result['num_students']}")
                        
                        self.root.after(0, self._update_model_status)
                        self.root.after(0, lambda: self.attendance_panel.enable("take_attendance"))
                
                dialog.append("\n" + "="*60)
                dialog.append("You may close this window now")
                dialog.append("="*60)
                dialog.enable_close()
                
            except Exception as e:
                dialog.append(f"\n✗ Error: {str(e)}")
                log_error("Process zips failed", e)
                dialog.append("\n" + "="*60)
                dialog.append("You may close this window now")
                dialog.append("="*60)
                dialog.enable_close()
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _on_save_image(self):
        """Handle save image from File menu."""
        if not self.current_result:
            messagebox.showwarning("Warning", "No captured image to save")
            return
        
        try:
            filepath = self._get_save_filepath()
            if not filepath:
                return
            
            annotated = self.service.create_annotated_image(
                self.current_result['image'],
                self.current_result['boxes'],
                show_labels=True
            )
            
            pil_img = self._convert_to_pil(annotated)
            pil_img.save(filepath)
            
            messagebox.showinfo("Success", f"Saved to:\n{filepath}")
            self.status_bar.update(
                f"Saved: {os.path.basename(filepath)}",
                COLOR_SUCCESS
            )
            
        except Exception as e:
            self._handle_error("Save failed", e)
    
    def _get_save_filepath(self):
        """Get filepath from user for saving."""
        return filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ],
            title="Save Image As"
        )
    
    def _on_take_attendance(self):
        """Handle take attendance button with enhanced notification."""
        if not self.current_result or not self.current_detected_ids:
            messagebox.showwarning(
                "Warning",
                "No capture available. Please capture an image first.",
                parent=self.root
            )
            return
        
        try:
            # Show date selection dialog
            date_dialog = DateSelectionDialog(self.root)
            selected_date = date_dialog.show()
            
            if not selected_date:
                return
            
            self.status_bar.update("Taking attendance...", COLOR_TEAL)
            self.root.update()
            
            # Take attendance
            result = self.service.take_attendance(
                self.current_detected_ids,
                selected_date
            )
            
            # Enhanced results message with file location
            message = f"Attendance taken for {selected_date}\n\n"
            message += f"Marked present: {result['marked']} students\n"
            
            if result['not_found']:
                message += f"\nWarning: {len(result['not_found'])} detected IDs not found in database:\n"
                message += ", ".join(result['not_found'][:5])
                if len(result['not_found']) > 5:
                    message += f"\n...and {len(result['not_found']) - 5} more"
            
            # Add file location info
            message += f"\n\n📊 Attendance spreadsheet location:\n{ATTENDANCE_EXCEL_FILE}"
            message += f"\n\nYou can also view records from:\nStudents → View Attendance Records"
            
            messagebox.showinfo(
                "Attendance Taken",
                message,
                parent=self.root
            )
            
            self.status_bar.update(
                f"Attendance: {result['marked']} present on {selected_date}",
                COLOR_SUCCESS
            )
            
        except Exception as e:
            self._handle_error("Attendance failed", e)
    
    def _open_settings(self):
        """Open settings dialog."""
        SettingsDialog(self.root).show()
        self._update_model_status()
    
    def _manage_students(self):
        """Open student management dialog."""
        StudentManagementDialog(self.root).show()
        # Check if training needed after managing students
        self._check_training_needed()
    
    def _view_attendance(self):
        """Open attendance viewer dialog."""
        AttendanceViewerDialog(self.root).show()
    
    def _show_help(self):
        """Open help dialog."""
        HelpDialog(self.root).show()
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About AttendanceTracker",
            "AttendanceTracker v0.9-beta\n\n"
            "Face Recognition Attendance System\n\n"
            "Developed for automated student attendance tracking\n"
            "using real-time face recognition technology.\n\n"
            "Contact: oximas2004@gmail.com",
            parent=self.root
        )
    
    def _handle_error(self, title, error):
        """Handle errors consistently."""
        messagebox.showerror("Error", f"{title}: {str(error)}")
        self.status_bar.update(title, COLOR_ERROR)
    
    def _on_close(self):
        """Handle window close event."""
        self._stop_live_feed()
        self.service.cleanup()
        self.root.destroy()
    
    def run(self):
        """Start the application."""
        self.root.mainloop()
    
    def cleanup(self):
        """Cleanup resources."""
        self._stop_live_feed()
        self.service.cleanup()


def main(first_run=False):
    root = tk.Tk()
    app = CameraApp(root, first_run=first_run)
    
    try:
        app.run()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()