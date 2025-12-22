import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from PeopleCounter import PeopleCounter, FACES_DIR
from FaceRecognizer import FaceRecognizer, CONFIDENCE_THRESHOLD
import os

URL = 0


class FaceNamingDialog:
    """Dialog for naming unknown faces one by one."""
    
    def __init__(self, parent, face_images):
        self.parent = parent
        self.face_images = face_images
        self.names = []
        self.current_index = 0
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Name Unknown Faces")
        self.dialog.geometry("500x600")
        self.dialog.configure(bg="#2c3e50")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_ui()
        self._show_current_face()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        # Title
        self.title_label = tk.Label(
            self.dialog,
            text="",
            font=("Helvetica", 14, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10
        )
        self.title_label.pack()
        
        # Image display
        self.image_frame = tk.Frame(self.dialog, bg="#34495e", relief=tk.SUNKEN, bd=2)
        self.image_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(
            self.image_frame,
            bg="#34495e"
        )
        self.image_label.pack(expand=True, pady=10)
        
        # Name entry
        entry_frame = tk.Frame(self.dialog, bg="#2c3e50")
        entry_frame.pack(pady=10)
        
        tk.Label(
            entry_frame,
            text="Enter Name:",
            font=("Helvetica", 12),
            bg="#2c3e50",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        self.name_entry = tk.Entry(
            entry_frame,
            font=("Helvetica", 12),
            width=20
        )
        self.name_entry.pack(side=tk.LEFT, padx=5)
        self.name_entry.bind('<Return>', lambda e: self._submit_name())
        self.name_entry.focus()
        
        # Buttons
        button_frame = tk.Frame(self.dialog, bg="#2c3e50")
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="Submit",
            command=self._submit_name,
            font=("Helvetica", 12, "bold"),
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Skip",
            command=self._skip_face,
            font=("Helvetica", 12, "bold"),
            bg="#e67e22",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel All",
            command=self._cancel,
            font=("Helvetica", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
    
    def _show_current_face(self):
        """Display the current face image."""
        if self.current_index >= len(self.face_images):
            self.dialog.destroy()
            return
        
        # Update title
        self.title_label.config(
            text=f"Face {self.current_index + 1} of {len(self.face_images)}"
        )
        
        # Convert and display image
        face_img = self.face_images[self.current_index]
        face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(face_rgb)
        
        # Resize if too large
        pil_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=photo)
        self.image_label.image = photo  # Keep reference
    
    def _submit_name(self):
        """Submit the current name and move to next face."""
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter a name", parent=self.dialog)
            return
        
        # Save the face with the name
        counter = PeopleCounter()
        face_img = self.face_images[self.current_index]
        filepath = counter.save_face_encoding(face_img, name)
        print(f"Saved face to: {filepath}")
        
        self.names.append(name)
        self._next_face()
    
    def _skip_face(self):
        """Skip current face and move to next."""
        self.names.append("Unknown")
        self._next_face()
    
    def _next_face(self):
        """Move to the next face."""
        self.current_index += 1
        self.name_entry.delete(0, tk.END)
        
        if self.current_index < len(self.face_images):
            self._show_current_face()
        else:
            self.dialog.destroy()
    
    def _cancel(self):
        """Cancel the naming process."""
        self.names = []
        self.dialog.destroy()
    
    def get_names(self):
        """Wait for dialog to close and return names."""
        self.dialog.wait_window()
        return self.names


class CameraApp:
    """GUI application for people detection and face recognition."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("People Detection Camera")
        self.root.geometry("900x700")
        self.root.configure(bg="#2c3e50")
        
        # State
        self.current_image = None
        self.display_image = None
        self.people_boxes = None
        self.stable_frame = None
        self.raw_people_images = []
        
        # Face recognizer
        self.face_recognizer = FaceRecognizer()
        self._try_load_existing_model()
        
        self._setup_ui()
    
    def _try_load_existing_model(self):
        """Try to load existing face recognition model."""
        try:
            if self.face_recognizer.load_model():
                print("Existing model loaded successfully")
        except Exception as e:
            print(f"No existing model found: {e}")
    
    def _setup_ui(self):
        """Initialize all UI components."""
        self._create_title()
        self._create_buttons()
        self._create_count_label()
        self._create_image_display()
        self._create_status_label()
    
    def _create_title(self):
        """Create title label."""
        tk.Label(
            self.root,
            text="People Detection System",
            font=("Helvetica", 20, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=20
        ).pack()
    
    def _create_buttons(self):
        """Create control buttons."""
        # Row 1: Main actions
        frame1 = tk.Frame(self.root, bg="#2c3e50")
        frame1.pack(pady=5)
        
        self.capture_btn = self._make_button(
            frame1, "Capture and Detect", 
            self.capture_and_display, "#3498db", 0
        )
        
        self.save_btn = self._make_button(
            frame1, "Save Image", 
            self.save_image, "#27ae60", 1, disabled=True
        )
        
        self.save_faces_btn = self._make_button(
            frame1, "Save Faces", 
            self.save_faces, "#e67e22", 2, disabled=True
        )
        
        # Row 2: Model actions
        frame2 = tk.Frame(self.root, bg="#2c3e50")
        frame2.pack(pady=5)
        
        self.train_btn = self._make_button(
            frame2, "Train Model", 
            self.train_model, "#9b59b6", 0, disabled=True
        )
        
        self.predict_btn = self._make_button(
            frame2, "Predict Faces", 
            self.predict_faces, "#1abc9c", 1
        )
    
    def _make_button(self, parent, text, command, color, column, disabled=False):
        """Create a styled button."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Helvetica", 12, "bold"),
            bg=color,
            fg="white",
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor="hand2",
            state=tk.DISABLED if disabled else tk.NORMAL
        )
        btn.grid(row=0, column=column, padx=10)
        return btn
    
    def _create_count_label(self):
        """Create people count display label."""
        self.count_label = tk.Label(
            self.root,
            text="People Count: 0",
            font=("Helvetica", 16, "bold"),
            bg="#2c3e50",
            fg="#95a5a6",
            pady=10
        )
        self.count_label.pack(pady=10)
    
    def _create_image_display(self):
        """Create image display area."""
        self.image_frame = tk.Frame(self.root, bg="#34495e", relief=tk.SUNKEN, bd=2)
        self.image_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(
            self.image_frame,
            text="No image captured yet",
            font=("Helvetica", 14),
            bg="#34495e",
            fg="#95a5a6"
        )
        self.image_label.pack(expand=True)
    
    def _create_status_label(self):
        """Create status message label."""
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            font=("Helvetica", 10),
            bg="#2c3e50",
            fg="#95a5a6",
            pady=10
        )
        self.status_label.pack()
    
    def _update_status(self, message, color="#95a5a6"):
        """Update status label with message and color."""
        self.status_label.config(text=message, fg=color)
        self.root.update()
    
    def _convert_to_pil(self, cv_image):
        """Convert OpenCV image to PIL Image."""
        if isinstance(cv_image, np.ndarray):
            if len(cv_image.shape) == 3:
                cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(cv_image)
        return cv_image
    
    def _check_for_unknown_faces(self):
        """Check if there are unknown faces and prompt user to name them."""
        if not self.raw_people_images:
            return
        
        counter = PeopleCounter(face_recognizer=self.face_recognizer)
        unknown_faces = []
        
        # Check each face
        for face_img in self.raw_people_images:
            name = counter.get_person_name(face_img)
            if name == "Unknown":
                unknown_faces.append(face_img)
        
        # If unknown faces found, ask user if they want to name them
        if unknown_faces:
            response = messagebox.askyesno(
                "Unknown Faces Detected",
                f"Found {len(unknown_faces)} unknown face(s).\n\nWould you like to name them?",
                parent=self.root
            )
            
            if response:
                # Open naming dialog
                dialog = FaceNamingDialog(self.root, unknown_faces)
                names = dialog.get_names()
                
                if names:
                    named_count = len([n for n in names if n != "Unknown"])
                    if named_count > 0:
                        messagebox.showinfo(
                            "Success",
                            f"Successfully saved {named_count} face(s)!",
                            parent=self.root
                        )
                        # Enable train button
                        self.train_btn.config(state=tk.NORMAL)
    
    def _refresh_labeled_image(self):
        """Re-label and display the image with updated names."""
        if self.stable_frame is not None and self.people_boxes is not None:
            counter = PeopleCounter(face_recognizer=self.face_recognizer)
            
            # Draw boxes and labels
            display_img = counter.draw_bounding_boxes(self.stable_frame, self.people_boxes)
            labeled_img = counter.label_faces_in_image(display_img, self.people_boxes)
            
            self.current_image = self._convert_to_pil(labeled_img)
            self.display_current_image()
    
    def capture_and_display(self):
        """Capture image from camera and detect faces."""
        try:
            self._update_status("Capturing image...", "#3498db")
            
            # Perform detection
            counter = PeopleCounter(url=URL, face_recognizer=self.face_recognizer)
            captured_img, count, boxes, _ = counter.capture_and_count()
            
            if captured_img is None:
                raise RuntimeError("Failed to capture image")
            
            # Store the ORIGINAL frame (no boxes) and boxes
            self.stable_frame = captured_img.copy()
            self.people_boxes = boxes
            
            # Extract raw face images from ORIGINAL frame
            self.raw_people_images = counter.extract_people_images(captured_img, boxes)
            
            # Create display version with boxes and labels
            display_img = counter.draw_bounding_boxes(captured_img, boxes)
            labeled_img = counter.label_faces_in_image(display_img, boxes)
            
            # Convert and display
            self.current_image = self._convert_to_pil(labeled_img)
            
            # Update display
            self.display_current_image()
            self._update_buttons(count)
            self._update_count(count)
            
            self._update_status(
                f"Image captured successfully - {count} people detected", 
                "#27ae60"
            )
            
            # Check for unknown faces and prompt to name them
            self._check_for_unknown_faces()
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self._update_status("Error occurred", "#e74c3c")
    
    def _update_buttons(self, people_count):
        """Enable/disable buttons based on detection results."""
        self.save_btn.config(state=tk.NORMAL)
        self.save_faces_btn.config(
            state=tk.NORMAL if people_count > 0 else tk.DISABLED
        )
    
    def _update_count(self, count):
        """Update people count display."""
        color = "#27ae60" if count > 0 else "#e74c3c"
        self.count_label.config(text=f"People Count: {count}", fg=color)
    
    def display_current_image(self):
        """Display current image in the GUI."""
        if self.current_image is None:
            return
        
        # Get frame dimensions
        w = max(self.image_frame.winfo_width(), 760)
        h = max(self.image_frame.winfo_height(), 450)
        
        # Resize to fit
        img_copy = self.current_image.copy()
        img_copy.thumbnail((w - 20, h - 20), Image.Resampling.LANCZOS)
        
        # Update display
        self.display_image = ImageTk.PhotoImage(img_copy)
        self.image_label.config(image=self.display_image, text="")
    
    def save_image(self):
        """Save captured image to file."""
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image to save")
            return
        
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*")
                ],
                title="Save Image As"
            )
            
            if filepath:
                self.current_image.save(filepath)
                messagebox.showinfo("Success", f"Image saved to:\n{filepath}")
                self._update_status(
                    f"Image saved: {os.path.basename(filepath)}", 
                    "#27ae60"
                )
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")
            self._update_status("Save failed", "#e74c3c")
    
    def save_faces(self):
        """Extract and save individual face images."""
        if self.stable_frame is None or self.people_boxes is None:
            messagebox.showwarning("Warning", "No faces to save. Capture first.")
            return
        
        if len(self.people_boxes) == 0:
            messagebox.showwarning("Warning", "No people detected.")
            return
        
        try:
            directory = filedialog.askdirectory(title="Select Directory to Save Faces")
            if not directory:
                return
            
            self._update_status("Extracting and saving faces...", "#3498db")
            
            # Extract and label faces
            counter = PeopleCounter(face_recognizer=self.face_recognizer)
            people_images = counter.extract_people_images(self.stable_frame, self.people_boxes)
            labeled_images = counter.add_names_to_images(people_images)
            
            # Save each face
            for i, labeled_img in enumerate(labeled_images):
                img_rgb = cv2.cvtColor(labeled_img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)
                filepath = os.path.join(directory, f"person_{i+1}.png")
                pil_img.save(filepath)
            
            messagebox.showinfo(
                "Success", 
                f"Saved {len(labeled_images)} faces to:\n{directory}"
            )
            self._update_status(
                f"Saved {len(labeled_images)} faces", 
                "#27ae60"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save faces: {str(e)}")
            self._update_status("Save faces failed", "#e74c3c")
    
    def train_model(self):
        """Train face recognition model on saved faces."""
        try:
            self._update_status("Training model...", "#9b59b6")
            self.root.update()
            
            # Train the model
            num_faces, num_people = self.face_recognizer.train_from_directory(FACES_DIR)
            
            # Save the trained model
            self.face_recognizer.save_model()
            
            messagebox.showinfo(
                "Training Complete",
                f"Model trained successfully!\n\n"
                f"Total faces: {num_faces}\n"
                f"Total people: {num_people}"
            )
            
            self._update_status(
                f"Model trained on {num_faces} faces from {num_people} people",
                "#27ae60"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Training failed: {str(e)}")
            self._update_status("Training failed", "#e74c3c")
    
    def predict_faces(self):
        """Re-predict all faces in current image using trained model."""
        if self.stable_frame is None or self.people_boxes is None:
            messagebox.showwarning(
                "Warning", 
                "No image to predict. Please capture an image first."
            )
            return
        
        try:
            self._update_status("Predicting faces...", "#1abc9c")
            self.root.update()
            
            # Reload model if needed
            if not self.face_recognizer.has_trained_model():
                loaded = self.face_recognizer.load_model()
                if not loaded:
                    messagebox.showinfo(
                        "No Model Found",
                        "No trained model found. All faces will be marked as 'Unknown'.\n\n"
                        "Please name some faces and train the model first."
                    )
            
            # Refresh the display with predictions
            self._refresh_labeled_image()
            
            self._update_status("Prediction complete", "#27ae60")
            
        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed: {str(e)}")
            self._update_status("Prediction failed", "#e74c3c")


def main():
    root = tk.Tk()
    app = CameraApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()