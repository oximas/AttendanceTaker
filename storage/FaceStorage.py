"""
Face storage module.
Handles saving and loading face images from disk.
"""

import os
import cv2
from config import FACES_DIR


class FaceStorage:
    """Manages face image storage on disk."""
    
    def __init__(self, base_dir=FACES_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    def save_face(self, face_image, person_name):
        """
        Save a face image with the given person name.
        
        Args:
            face_image: Face image to save
            person_name: Name of the person
            
        Returns:
            str: Path to saved file
        """
        person_dir = os.path.join(self.base_dir, person_name)
        os.makedirs(person_dir, exist_ok=True)
        
        # Count existing images
        existing_files = [f for f in os.listdir(person_dir) if f.endswith('.png')]
        next_number = len(existing_files) + 1
        
        # Save image
        filename = f"{person_name}_{next_number}.png"
        filepath = os.path.join(person_dir, filename)
        cv2.imwrite(filepath, face_image)
        
        return filepath
    
    def get_person_directory(self, person_name):
        """
        Get directory path for a person.
        
        Args:
            person_name: Name of the person
            
        Returns:
            str: Directory path
        """
        return os.path.join(self.base_dir, person_name)
    
    def list_people(self):
        """
        Get list of all people with saved faces.
        
        Returns:
            list: List of person names (directory names)
        """
        if not os.path.exists(self.base_dir):
            return []
        
        return [d for d in os.listdir(self.base_dir) 
                if os.path.isdir(os.path.join(self.base_dir, d))]
    
    def load_person_images(self, person_name):
        """
        Load all face images for a person.
        
        Args:
            person_name: Name of the person
            
        Returns:
            list: List of (image, filepath) tuples
        """
        person_dir = self.get_person_directory(person_name)
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
    
    def count_faces(self, person_name=None):
        """
        Count total face images.
        
        Args:
            person_name: Specific person, or None for all
            
        Returns:
            int: Number of face images
        """
        if person_name:
            images = self.load_person_images(person_name)
            return len(images)
        
        total = 0
        for person in self.list_people():
            total += len(self.load_person_images(person))
        return total