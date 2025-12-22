"""
Reusable UI Components.
Separated dialog and widget creation from main application logic.
"""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
from config import (
    COLOR_PRIMARY_BG, COLOR_SECONDARY_BG, COLOR_TEXT_PRIMARY,
    DIALOG_WIDTH, DIALOG_HEIGHT, FONT_DIALOG_TITLE, FONT_LABEL
)


class FaceNamingDialog:
    """Dialog for naming unknown faces one by one."""
    
    def __init__(self, parent, face_images, on_save_callback=None):
        self.parent = parent
        self.face_images = face_images
        self.on_save_callback = on_save_callback
        self.names = []
        self.current_index = 0
        
        self._create_dialog()
        self._create_widgets()
        self._show_current_face()
    
    def _create_dialog(self):
        """Create dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Name Unknown Faces")
        self.dialog.geometry(f"{DIALOG_WIDTH}x{DIALOG_HEIGHT}")
        self.dialog.configure(bg=COLOR_PRIMARY_BG)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
    
    def _create_widgets(self):
        """Create all dialog widgets."""
        self._create_title_label()
        self._create_image_display()
        self._create_name_entry()
        self._create_buttons()
    
    def _create_title_label(self):
        """Create title label."""
        self.title_label = tk.Label(
            self.dialog,
            text="",
            font=FONT_DIALOG_TITLE,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY,
            pady=10
        )
        self.title_label.pack()
    
    def _create_image_display(self):
        """Create image display area."""
        self.image_frame = tk.Frame(
            self.dialog,
            bg=COLOR_SECONDARY_BG,
            relief=tk.SUNKEN,
            bd=2
        )
        self.image_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(
            self.image_frame,
            bg=COLOR_SECONDARY_BG
        )
        self.image_label.pack(expand=True, pady=10)
    
    def _create_name_entry(self):
        """Create name input field."""
        entry_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        entry_frame.pack(pady=10)
        
        tk.Label(
            entry_frame,
            text="Enter Name:",
            font=FONT_LABEL,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_PRIMARY
        ).pack(side=tk.LEFT, padx=5)
        
        self.name_entry = tk.Entry(entry_frame, font=FONT_LABEL, width=20)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        self.name_entry.bind('<Return>', lambda e: self._submit_name())
        self.name_entry.focus()
    
    def _create_buttons(self):
        """Create action buttons."""
        from config import COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR
        
        button_frame = tk.Frame(self.dialog, bg=COLOR_PRIMARY_BG)
        button_frame.pack(pady=10)
        
        self._create_button(button_frame, "Submit", self._submit_name, 
                           COLOR_SUCCESS, 0)
        self._create_button(button_frame, "Skip", self._skip_face, 
                           COLOR_WARNING, 1)
        self._create_button(button_frame, "Cancel All", self._cancel, 
                           COLOR_ERROR, 2)
    
    def _create_button(self, parent, text, command, color, column):
        """Create a styled button."""
        from config import FONT_BUTTON
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=FONT_BUTTON,
            bg=color,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=5
        )
        btn.pack(side=tk.LEFT, padx=5)
    
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
        pil_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=photo)
        self.image_label.image = photo
    
    def _submit_name(self):
        """Submit the current name."""
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter a name", 
                                 parent=self.dialog)
            return
        
        # Save face with callback
        if self.on_save_callback:
            face_img = self.face_images[self.current_index]
            self.on_save_callback(face_img, name)
        
        self.names.append(name)
        self._next_face()
    
    def _skip_face(self):
        """Skip current face."""
        self.names.append("Unknown")
        self._next_face()
    
    def _next_face(self):
        """Move to next face."""
        self.current_index += 1
        self.name_entry.delete(0, tk.END)
        
        if self.current_index < len(self.face_images):
            self._show_current_face()
        else:
            self.dialog.destroy()
    
    def _cancel(self):
        """Cancel naming process."""
        self.names = []
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and wait for completion."""
        self.dialog.wait_window()
        return self.names


class StatusBar:
    """Status bar component for displaying messages."""
    
    def __init__(self, parent):
        from config import FONT_STATUS, COLOR_TEXT_SECONDARY
        
        self.label = tk.Label(
            parent,
            text="Ready",
            font=FONT_STATUS,
            bg=COLOR_PRIMARY_BG,
            fg=COLOR_TEXT_SECONDARY,
            pady=10
        )
        self.label.pack()
    
    def update(self, message, color=None):
        """Update status message."""
        from config import COLOR_TEXT_SECONDARY
        self.label.config(text=message, fg=color or COLOR_TEXT_SECONDARY)
        self.label.update()


class ImageDisplay:
    """Image display component."""
    
    def __init__(self, parent):
        self._create_frame(parent)
        self.photo = None
    
    def _create_frame(self, parent):
        """Create display frame."""
        from config import FONT_SUBTITLE, COLOR_TEXT_SECONDARY
        
        self.frame = tk.Frame(
            parent,
            bg=COLOR_SECONDARY_BG,
            relief=tk.SUNKEN,
            bd=2
        )
        self.frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        self.label = tk.Label(
            self.frame,
            text="No image captured yet",
            font=FONT_SUBTITLE,
            bg=COLOR_SECONDARY_BG,
            fg=COLOR_TEXT_SECONDARY
        )
        self.label.pack(expand=True)
    
    def show_image(self, pil_image, max_width=760, max_height=450):
        """Display PIL image."""
        if pil_image is None:
            return
        
        # Get frame dimensions
        w = max(self.frame.winfo_width(), max_width)
        h = max(self.frame.winfo_height(), max_height)
        
        # Resize to fit
        img_copy = pil_image.copy()
        img_copy.thumbnail((w - 20, h - 20), Image.Resampling.LANCZOS)
        
        # Update display
        self.photo = ImageTk.PhotoImage(img_copy)
        self.label.config(image=self.photo, text="")
    
    def clear(self):
        """Clear the display."""
        self.label.config(image="", text="No image captured yet")
        self.photo = None


class ButtonPanel:
    """Panel of styled buttons."""
    
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=COLOR_PRIMARY_BG)
        self.frame.pack(pady=5)
        self.buttons = {}
    
    def add_button(self, name, text, command, color, column=None, enabled=True):
        """Add a button to the panel."""
        from config import FONT_BUTTON
        
        btn = tk.Button(
            self.frame,
            text=text,
            command=command,
            font=FONT_BUTTON,
            bg=color,
            fg=COLOR_TEXT_PRIMARY,
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor="hand2",
            state=tk.NORMAL if enabled else tk.DISABLED
        )
        
        if column is not None:
            btn.grid(row=0, column=column, padx=10)
        else:
            btn.pack(side=tk.LEFT, padx=10)
        
        self.buttons[name] = btn
        return btn
    
    def enable(self, name):
        """Enable a button."""
        if name in self.buttons:
            self.buttons[name].config(state=tk.NORMAL)
    
    def disable(self, name):
        """Disable a button."""
        if name in self.buttons:
            self.buttons[name].config(state=tk.DISABLED)
    
    def get(self, name):
        """Get button by name."""
        return self.buttons.get(name)