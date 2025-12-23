"""
GUI.py
Main GUI application with live camera feed and face detection.
Shows live video stream with real-time bounding boxes in main window.
Captured images with recognition results open in external windows.
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
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_PRIMARY_BG,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_INFO,
    COLOR_PURPLE, COLOR_TEAL, FONT_TITLE, FONT_SUBTITLE,
    CAMERA_URL, DOWNLOADS_DIR, GOOGLE_DRIVE_FOLDER_URL,
    CAPTURE_WINDOW_WIDTH, CAPTURE_WINDOW_HEIGHT, CAPTURE_FRAME_COUNT
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
        
        # Title
        tk.Label(
            self.dialog,
            text=title,
            font=FONT_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg="white",
            pady=10
        ).pack()
        
        # Scrolled text area
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
        
        # Close button (initially disabled)
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
        
        # Title
        tk.Label(
            self.window,
            text=title,
            font=FONT_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg="white",
            pady=10
        ).pack()
        
        # Image display
        self.image_label = tk.Label(self.window, bg=COLOR_PRIMARY_BG)
        self.image_label.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Display image
        self.show_image(image)
    
    def show_image(self, pil_image):
        """Display PIL image in window."""
        if pil_image is None:
            print("image is none")
            return
        
        # Resize to fit window
        img_copy = pil_image.copy()
        img_copy.thumbnail(
            (CAPTURE_WINDOW_WIDTH - 40, CAPTURE_WINDOW_HEIGHT - 80),
            Image.Resampling.LANCZOS
        )
        
        self.photo = ImageTk.PhotoImage(img_copy)
        self.image_label.config(image=self.photo)


class CameraApp:
    """Main application with live camera feed and face detection."""
    
    def __init__(self, root):
        self.root = root
        self.service = FaceRecognitionService(CAMERA_URL)
        self.current_result = None
        
        self.live_feed_active = True
        self.live_feed_thread = None
        
        self._setup_window()
        self._create_ui()
        self._check_initial_state()
        self._start_live_feed()
    
    def _setup_window(self):
        """Configure main window."""
        self.root.title("People Detection Camera")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLOR_PRIMARY_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_ui(self):
        """Create all UI components."""
        self._create_title()
        self._create_button_panels()
        self._create_count_label()
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
        # Main actions panel
        self.main_panel = ButtonPanel(self.root)
        self.main_panel.add_button(
            "capture", "Capture and Detect",
            self._on_capture, COLOR_INFO, 0
        )
        self.main_panel.add_button(
            "save_image", "Save Current Capture",
            self._on_save_image, COLOR_SUCCESS, 1, enabled=False
        )
        self.main_panel.add_button(
            "save_faces", "Save Faces",
            self._on_save_faces, COLOR_WARNING, 2, enabled=False
        )
        
        # Download and process panel
        self.download_panel = ButtonPanel(self.root)
        self.download_panel.add_button(
            "download_process", "Download & Process Images",
            self._on_download_and_process, "#e67e22", 0
        )
        
        # Model actions panel
        self.model_panel = ButtonPanel(self.root)
        self.model_panel.add_button(
            "train", "Train Model",
            self._on_train_model, COLOR_PURPLE, 0, enabled=False
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
        self.count_label.pack(pady=10)
    
    def _check_initial_state(self):
        """Check if faces exist and enable train button if so."""
        people = self.service.recognizer.face_storage.list_people()
        if people:
            self.model_panel.enable("train")
            self.status_bar.update(
                f"Ready - {len(people)} people in database",
                COLOR_SUCCESS
            )
    
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
        while self.live_feed_active:
            try:
                frame = self.service.counter.camera.get_current_frame()
                if frame is None:
                    continue

                # Launch detection IF not already running
                if not self.detecting:
                    self.detecting = True
                    threading.Thread(
                        target=self._run_detection,
                        args=(frame.copy(),),
                        daemon=True
                    ).start()

                # Always draw last known boxes
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
                print(f"Live feed error: {e}")
    
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
    
    def _on_capture(self):
        """Handle capture button - freeze frame and run recognition."""
        try:
            self.status_bar.update("Capturing stable frame...", COLOR_INFO)
            
            # Capture multiple frames for stable detection
            frames = self.service.counter.camera.capture_frames(CAPTURE_FRAME_COUNT)
            
            # Find stable detection
            stable_frame, count, boxes = self.service.counter.detector.find_stable_detection(frames)
            
            # Extract faces
            faces = self.service.counter.extract_face_images(stable_frame, boxes)
            
            # Store result
            self.current_result = {
                'image': stable_frame,
                'count': count,
                'boxes': boxes,
                'faces': faces
            }
            
            # Run face recognition and create annotated image
            annotated = self.service.create_annotated_image(
                stable_frame,
                boxes,
                show_labels=True
            )
            # Open external window with recognized faces
            pil_image = self._convert_to_pil(annotated)
            self.capture_window = CaptureWindow(self.root, pil_image, f"Captured - {count} People Detected")
            
            # Enable buttons
            self.main_panel.enable("save_image")
            if count > 0:
                self.main_panel.enable("save_faces")
            else:
                self.main_panel.disable("save_faces")
            
            self.status_bar.update(
                f"Captured {count} people - Window opened",
                COLOR_SUCCESS
            )
            
            # Check for unknown faces
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
        """Open dialog to name unknown faces."""
        unknown_faces = [face for _, face in unknown_list]
        
        dialog = FaceNamingDialog(
            self.root,
            unknown_faces,
            on_save_callback=self.service.counter.save_face
        )
        
        names = dialog.show()
        
        if names:
            named_count = len([n for n in names if n != "Unknown"])
            if named_count > 0:
                messagebox.showinfo(
                    "Success",
                    f"Saved {named_count} face(s)!",
                    parent=self.root
                )
                self.model_panel.enable("train")
    
    def _on_download_and_process(self):
        """Handle download and process button."""
        dialog = ProcessingDialog(self.root, "Download & Process Images")
        
        def process():
            try:
                import sys
                
                old_stdout = sys.stdout
                sys.stdout = StringBuffer(dialog)
                
                dialog.append("=" * 60)
                dialog.append("STEP 1: DOWNLOADING IMAGES")
                dialog.append("=" * 60)
                
                downloader = ImageDownloadManager(DOWNLOADS_DIR)
                success = downloader.download_and_extract(GOOGLE_DRIVE_FOLDER_URL)
                
                if not success:
                    dialog.append("\n✗ Download failed!")
                    dialog.enable_close()
                    sys.stdout = old_stdout
                    return
                
                dialog.append("\n" + "=" * 60)
                dialog.append("STEP 2: EXTRACTING FACES")
                dialog.append("=" * 60)
                
                pipeline = FaceExtractionPipeline()
                stats = pipeline.run_pipeline()
                
                sys.stdout = old_stdout
                
                if stats['faces_extracted'] > 0:
                    self.root.after(0, lambda: self.model_panel.enable("train"))
                    self.root.after(0, lambda: self.status_bar.update(
                        f"Extracted {stats['faces_extracted']} faces", 
                        COLOR_SUCCESS
                    ))
                
                dialog.append("\n✓ Processing complete!")
                dialog.enable_close()
                
            except Exception as e:
                dialog.append(f"\n✗ Error: {str(e)}")
                dialog.enable_close()
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _on_save_image(self):
        """Handle save image button."""
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
    
    def _on_save_faces(self):
        """Handle save faces button."""
        if not self.current_result or not self.current_result['faces']:
            messagebox.showwarning("Warning", "No faces to save")
            return
        
        try:
            directory = filedialog.askdirectory(
                title="Select Directory to Save Faces"
            )
            if not directory:
                return
            
            self.status_bar.update("Saving faces...", COLOR_INFO)
            
            predictions = self.service.recognize_faces(
                self.current_result['image'],
                self.current_result['boxes']
            )
            
            saved_count = self._save_individual_faces(
                directory,
                self.current_result['faces'],
                predictions
            )
            
            messagebox.showinfo(
                "Success",
                f"Saved {saved_count} faces to:\n{directory}"
            )
            self.status_bar.update(f"Saved {saved_count} faces", COLOR_SUCCESS)
            
        except Exception as e:
            self._handle_error("Save faces failed", e)
    
    def _save_individual_faces(self, directory, faces, predictions):
        """Save individual face images to directory."""
        from core.FaceImageProcessor import FaceImageProcessor
        processor = FaceImageProcessor()
        
        for i, (face, (name, conf)) in enumerate(zip(faces, predictions)):
            label = name if name != "Unknown" else "Unknown"
            labeled = processor.add_label_to_face_image(face, label)
            
            face_rgb = cv2.cvtColor(labeled, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(face_rgb)
            filepath = os.path.join(directory, f"person_{i+1}_{label}.png")
            pil_img.save(filepath)
        
        return len(faces)
    
    def _on_train_model(self):
        """Handle train model button."""
        try:
            self.status_bar.update("Training model...", COLOR_PURPLE)
            self.root.update()
            
            result = self.service.train_model()
            
            messagebox.showinfo(
                "Training Complete",
                f"Model trained successfully!\n\n"
                f"Total faces: {result['num_faces']}\n"
                f"Total people: {result['num_people']}"
            )
            
            self.status_bar.update(
                f"Trained on {result['num_faces']} faces from {result['num_people']} people",
                COLOR_SUCCESS
            )
            
        except Exception as e:
            self._handle_error("Training failed", e)
    
    
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


class StringBuffer:
    """Buffer to redirect print statements to dialog."""
    
    def __init__(self, dialog):
        self.dialog = dialog
    
    def write(self, text):
        if text.strip():
            self.dialog.append(text.rstrip())
    
    def flush(self):
        pass


def main():
    root = tk.Tk()
    app = CameraApp(root)
    
    try:
        app.run()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()