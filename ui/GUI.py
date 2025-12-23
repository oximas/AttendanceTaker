"""
GUI.py
Main GUI application for face detection, recognition, and training.
Provides buttons for capturing images, downloading/processing student photos, and training the model.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
import cv2
import numpy as np
import os
import threading

from services.FaceRecognitionService import FaceRecognitionService
from services.FaceExtractionPipeline import FaceExtractionPipeline
from services.ImageDownloader import ImageDownloadManager
from ui.UIComponents import FaceNamingDialog, StatusBar, ImageDisplay, ButtonPanel
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_PRIMARY_BG,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_INFO,
    COLOR_PURPLE, COLOR_TEAL, FONT_TITLE, FONT_SUBTITLE,
    DEFAULT_CAMERA_INDEX, DOWNLOADS_DIR, GOOGLE_DRIVE_FOLDER_URL
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


class CameraApp:
    """Main application for face detection and recognition."""
    
    def __init__(self, root):
        self.root = root
        self.service = FaceRecognitionService(DEFAULT_CAMERA_INDEX)
        self.current_result = None  # Stores latest detection result
        
        self._setup_window()
        self._create_ui()
        self._check_initial_state()
    
    def _setup_window(self):
        """Configure main window."""
        self.root.title("People Detection Camera")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLOR_PRIMARY_BG)
    
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
            text="People Detection System",
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
            "save_image", "Save Image",
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
        self.model_panel.add_button(
            "predict", "Predict Faces",
            self._on_predict_faces, COLOR_TEAL, 1
        )
    
    def _create_count_label(self):
        """Create people count label."""
        from config import COLOR_TEXT_SECONDARY
        
        self.count_label = tk.Label(
            self.root,
            text="People Count: 0",
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
    
    def _convert_to_pil(self, cv_image):
        """Convert OpenCV image to PIL."""
        if isinstance(cv_image, np.ndarray):
            if len(cv_image.shape) == 3:
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(cv_image)
        return cv_image
    
    def _update_count_display(self, count):
        """Update people count label."""
        color = COLOR_SUCCESS if count > 0 else COLOR_ERROR
        self.count_label.config(text=f"People Count: {count}", fg=color)
    
    def _enable_buttons_after_capture(self, has_faces):
        """Enable relevant buttons after capture."""
        self.main_panel.enable("save_image")
        if has_faces:
            self.main_panel.enable("save_faces")
        else:
            self.main_panel.disable("save_faces")
    
    def _on_capture(self):
        """Handle capture button click."""
        try:
            self.status_bar.update("Capturing image...", COLOR_INFO)
            
            # Capture and detect
            result = self.service.capture_and_detect_faces()
            self.current_result = result
            
            # Create annotated image
            annotated = self.service.create_annotated_image(
                result['image'],
                result['boxes'],
                show_labels=True
            )
            
            # Display
            pil_image = self._convert_to_pil(annotated)
            self.image_display.show_image(pil_image)
            
            # Update UI
            self._update_count_display(result['count'])
            self._enable_buttons_after_capture(result['count'] > 0)
            
            self.status_bar.update(
                f"Detected {result['count']} people",
                COLOR_SUCCESS
            )
            
            # Check for unknown faces
            self._check_unknown_faces(result['faces'])
            
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
        # Create processing dialog
        dialog = ProcessingDialog(self.root, "Download & Process Images")
        
        # Run in thread to not freeze UI
        def process():
            try:
                # Redirect print to dialog
                import sys
                
                old_stdout = sys.stdout
                sys.stdout = StringBuffer(dialog)
                
                # Download images
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
                
                # Extract faces
                dialog.append("\n" + "=" * 60)
                dialog.append("STEP 2: EXTRACTING FACES")
                dialog.append("=" * 60)
                
                pipeline = FaceExtractionPipeline()
                stats = pipeline.run_pipeline()
                
                # Restore stdout
                sys.stdout = old_stdout
                
                # Enable train button if faces were extracted
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
        
        # Start processing thread
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def _on_save_image(self):
        """Handle save image button."""
        if not self.current_result:
            messagebox.showwarning("Warning", "No image to save")
            return
        
        try:
            filepath = self._get_save_filepath()
            if not filepath:
                return
            
            # Save annotated version
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
            
            # Get predictions for labels
            predictions = self.service.recognize_faces(
                self.current_result['image'],
                self.current_result['boxes']
            )
            
            # Save each face with label
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
            # Add label to face
            label = name if name != "Unknown" else "Unknown"
            labeled = processor.add_label_to_face_image(face, label)
            
            # Convert and save
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
    
    def _on_predict_faces(self):
        """Handle predict faces button."""
        if not self.current_result:
            messagebox.showwarning(
                "Warning",
                "No image to predict. Capture first."
            )
            return
        
        try:
            self.status_bar.update("Predicting faces...", COLOR_TEAL)
            self.root.update()
            
            # Check if model exists
            if not self.service.has_trained_model():
                self.service.reload_model()
                if not self.service.has_trained_model():
                    messagebox.showinfo(
                        "No Model",
                        "No trained model found.\n"
                        "All faces will be marked as 'Unknown'.\n\n"
                        "Please name faces and train the model."
                    )
            
            # Re-annotate image with predictions
            annotated = self.service.create_annotated_image(
                self.current_result['image'],
                self.current_result['boxes'],
                show_labels=True
            )
            
            pil_image = self._convert_to_pil(annotated)
            self.image_display.show_image(pil_image)
            
            self.status_bar.update("Prediction complete", COLOR_SUCCESS)
            
        except Exception as e:
            self._handle_error("Prediction failed", e)
    
    def _handle_error(self, title, error):
        """Handle errors consistently."""
        messagebox.showerror("Error", f"{title}: {str(error)}")
        self.status_bar.update(title, COLOR_ERROR)
    
    def run(self):
        """Start the application."""
        self.root.mainloop()
    
    def cleanup(self):
        """Cleanup resources."""
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