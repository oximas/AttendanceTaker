"""
storage/FaceStorage.py
Handles saving and loading face images from disk.
Uses student ID as folder and file naming convention.
"""

import os
import cv2
from config import FACES_DIR


class FaceStorage:
    """Manages face image storage on disk using student IDs."""
    
    def __init__(self, base_dir=FACES_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    def save_face(self, face_image, student_id):
        """
        Save a face image with the given student ID.
        
        Args:
            face_image: Face image to save
            student_id: Student ID (used as folder and file prefix)
            
        Returns:
            str: Path to saved file
        """
        person_dir = os.path.join(self.base_dir, student_id)
        os.makedirs(person_dir, exist_ok=True)
        
        # Count existing images
        existing_files = [f for f in os.listdir(person_dir) if f.endswith('.png')]
        next_number = len(existing_files) + 1
        
        # Save image with ID as filename
        filename = f"{student_id}_{next_number}.png"
        filepath = os.path.join(person_dir, filename)
        cv2.imwrite(filepath, face_image)
        
        return filepath
    
    def get_person_directory(self, student_id):
        """
        Get directory path for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            str: Directory path
        """
        return os.path.join(self.base_dir, student_id)
    
    def list_people(self):
        """
        Get list of all student IDs with saved faces.
        
        Returns:
            list: List of student IDs (directory names)
        """
        if not os.path.exists(self.base_dir):
            return []
        
        return [d for d in os.listdir(self.base_dir) 
                if os.path.isdir(os.path.join(self.base_dir, d))]
    
    def load_person_images(self, student_id):
        """
        Load all face images for a student.
        
        Args:
            student_id: Student ID
            
        Returns:
            list: List of (image, filepath) tuples
        """
        person_dir = self.get_person_directory(student_id)
        if not os.path.exists(person_dir):
            return []
        
        images = []
        for img_name in os.listdir(person_dir):
            if not img_name.endswith(('.png', '.jpg', '.jpeg')):
                continue
            
            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)
            if img is not None:
                images.append((img, img_path))
        
        return images
    
    def count_faces(self, student_id=None):
        """
        Count total face images.
        
        Args:
            student_id: Specific student ID, or None for all
            
        Returns:
            int: Number of face images
        """
        if student_id:
            images = self.load_person_images(student_id)
            return len(images)
        
        total = 0
        for person_id in self.list_people():
            total += len(self.load_person_images(person_id))
        return total