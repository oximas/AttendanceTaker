"""
Face Storage Module
Handles saving and organizing face data to disk.
"""
import os
import cv2
import numpy as np
from pathlib import Path
from typing import Optional


class FaceStorage:
    """Manages storage of face images in an organized directory structure."""
    
    def __init__(self, base_directory: str):
        """
        Initialize face storage.
        
        Args:
            base_directory: Base directory for storing face data
        """
        self.base_directory = Path(base_directory)
        self._ensure_directory_exists(self.base_directory)
    
    def save_face(self, face_image: np.ndarray, person_name: str) -> str:
        """
        Save a face image for a specific person.
        
        Args:
            face_image: Face image as numpy array
            person_name: Name of the person
            
        Returns:
            Full path where the face was saved
        """
        person_directory = self._get_person_directory(person_name)
        self._ensure_directory_exists(person_directory)
        
        next_index = self._get_next_face_index(person_directory, person_name)
        filename = self._generate_filename(person_name, next_index)
        filepath = person_directory / filename
        
        cv2.imwrite(str(filepath), face_image)
        
        return str(filepath)
    
    def get_person_directory(self, person_name: str) -> str:
        """Get the directory path for a specific person."""
        return str(self._get_person_directory(person_name))
    
    def list_all_people(self) -> list:
        """
        Get list of all people with saved faces.
        
        Returns:
            List of person names
        """
        if not self.base_directory.exists():
            return []
        
        return [
            d.name for d in self.base_directory.iterdir()
            if d.is_dir()
        ]
    
    def count_faces_for_person(self, person_name: str) -> int:
        """
        Count number of saved faces for a person.
        
        Args:
            person_name: Name of the person
            
        Returns:
            Number of saved face images
        """
        person_dir = self._get_person_directory(person_name)
        
        if not person_dir.exists():
            return 0
        
        return len(self._get_existing_face_files(person_dir))
    
    def _get_person_directory(self, person_name: str) -> Path:
        """Get Path object for person's directory."""
        return self.base_directory / person_name
    
    @staticmethod
    def _ensure_directory_exists(directory: Path):
        """Create directory if it doesn't exist."""
        directory.mkdir(parents=True, exist_ok=True)
    
    def _get_next_face_index(self, person_directory: Path, person_name: str) -> int:
        """Determine the next available index for face filename."""
        existing_files = self._get_existing_face_files(person_directory)
        return len(existing_files) + 1
    
    @staticmethod
    def _get_existing_face_files(directory: Path) -> list:
        """Get list of existing face image files in directory."""
        if not directory.exists():
            return []
        
        return [f for f in directory.iterdir() if f.suffix.lower() == '.png']
    
    @staticmethod
    def _generate_filename(person_name: str, index: int) -> str:
        """Generate filename for face image."""
        return f"{person_name}_{index}.png"


class ImageLoader:
    """Handles loading images from disk."""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    
    @staticmethod
    def load_image(filepath: str) -> Optional[np.ndarray]:
        """
        Load an image from file.
        
        Args:
            filepath: Path to image file
            
        Returns:
            Image as numpy array or None if loading fails
        """
        image = cv2.imread(filepath)
        return image if image is not None else None
    
    @classmethod
    def find_image_files(cls, directory: str) -> list:
        """
        Find all image files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of Path objects for image files
        """
        dir_path = Path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return []
        
        return [
            f for f in dir_path.iterdir()
            if f.suffix.lower() in cls.SUPPORTED_EXTENSIONS
        ]
    
    @classmethod
    def load_all_images_from_directory(cls, directory: str) -> list:
        """
        Load all images from a directory.
        
        Args:
            directory: Directory containing images
            
        Returns:
            List of tuples (filepath, image)
        """
        image_files = cls.find_image_files(directory)
        
        loaded_images = []
        for filepath in image_files:
            image = cls.load_image(str(filepath))
            if image is not None:
                loaded_images.append((str(filepath), image))
        
        return loaded_images