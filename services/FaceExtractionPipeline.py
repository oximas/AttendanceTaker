"""
FaceExtractionPipeline.py
Processes downloaded images from DOWNLOADS_DIR, detects faces, and extracts them to FACES_DIR.
Handles single-face validation and organizes faces by person name extracted from folder structure.
"""

import os
import cv2
from pathlib import Path
from config import DOWNLOADS_DIR, FACES_DIR
from core.FaceDetector import FaceDetector
from core.FaceImageProcessor import FaceImageProcessor
from storage.FaceStorage import FaceStorage


class FaceExtractionPipeline:
    """
    Extracts faces from downloaded images and organizes them for training.
    Processes folder structure: DOWNLOADS_DIR/PersonName_ID/images -> FACES_DIR/PersonName_ID/faces
    """
    
    def __init__(self, downloads_dir=DOWNLOADS_DIR, faces_dir=FACES_DIR):
        self.downloads_dir = downloads_dir
        self.faces_dir = faces_dir
        self.detector = FaceDetector()
        self.processor = FaceImageProcessor()
        self.storage = FaceStorage(faces_dir)
        
        # Statistics
        self.stats = {
            'total_folders': 0,
            'total_images': 0,
            'faces_extracted': 0,
            'skipped_no_face': 0,
            'skipped_multiple_faces': 0,
            'errors': 0
        }
    
    def scan_person_folders(self):
        """
        Scan DOWNLOADS_DIR for person folders.
        
        Returns:
            list: List of (folder_path, person_name) tuples
        """
        if not os.path.exists(self.downloads_dir):
            return []
        
        person_folders = []
        for item in os.listdir(self.downloads_dir):
            folder_path = os.path.join(self.downloads_dir, item)
            if os.path.isdir(folder_path):
                person_folders.append((folder_path, item))
        
        return person_folders
    
    def get_image_files(self, folder_path):
        """
        Get all image files from a folder.
        
        Args:
            folder_path: Path to folder
            
        Returns:
            list: List of image file paths
        """
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        image_files = []
        
        for file in os.listdir(folder_path):
            if file.lower().endswith(image_extensions):
                image_files.append(os.path.join(folder_path, file))
        
        return image_files
    
    def extract_single_face(self, image_path):
        """
        Extract face from image if exactly one face is present.
        
        Args:
            image_path: Path to image file
            
        Returns:
            numpy.ndarray: Face image if single face found, None otherwise
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Detect faces
            count, boxes = self.detector.detect(image)
            
            # Only process if exactly one face
            if count != 1:
                if count == 0:
                    self.stats['skipped_no_face'] += 1
                else:
                    self.stats['skipped_multiple_faces'] += 1
                return None
            
            # Extract and resize face
            face = self.processor.crop_face(image, boxes[0])
            if face is None:
                return None
            
            face = self.processor.resize_face(face)
            return face
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"Error processing {image_path}: {str(e)}")
            return None
    
    def process_person_folder(self, folder_path, person_name):
        """
        Process all images in a person's folder.
        
        Args:
            folder_path: Path to person's folder
            person_name: Name of the person (folder name)
            
        Returns:
            int: Number of faces successfully extracted
        """
        image_files = self.get_image_files(folder_path)
        extracted_count = 0
        
        print(f"\nProcessing: {person_name}")
        print(f"  Found {len(image_files)} images")
        
        for image_path in image_files:
            self.stats['total_images'] += 1
            
            # Extract face
            face = self.extract_single_face(image_path)
            
            if face is not None:
                # Save to FACES_DIR
                self.storage.save_face(face, person_name)
                extracted_count += 1
                self.stats['faces_extracted'] += 1
        
        print(f"  Extracted {extracted_count} faces")
        return extracted_count
    
    def run_pipeline(self):
        """
        Run the complete extraction pipeline.
        
        Returns:
            dict: Statistics about the extraction process
        """
        print("="*60)
        print("FACE EXTRACTION PIPELINE")
        print("="*60)
        
        # Reset statistics
        self.stats = {
            'total_folders': 0,
            'total_images': 0,
            'faces_extracted': 0,
            'skipped_no_face': 0,
            'skipped_multiple_faces': 0,
            'errors': 0
        }
        
        # Scan for person folders
        person_folders = self.scan_person_folders()
        
        if not person_folders:
            print(f"\nNo person folders found in: {self.downloads_dir}")
            return self.stats
        
        self.stats['total_folders'] = len(person_folders)
        print(f"\nFound {len(person_folders)} person folders")
        
        # Process each person folder
        for folder_path, person_name in person_folders:
            self.process_person_folder(folder_path, person_name)
        
        # Print summary
        self._print_summary()
        
        return self.stats
    
    def _print_summary(self):
        """Print extraction summary."""
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Total person folders processed: {self.stats['total_folders']}")
        print(f"Total images scanned: {self.stats['total_images']}")
        print(f"Faces extracted: {self.stats['faces_extracted']}")
        print(f"Skipped (no face): {self.stats['skipped_no_face']}")
        print(f"Skipped (multiple faces): {self.stats['skipped_multiple_faces']}")
        print(f"Errors: {self.stats['errors']}")
        print("="*60)


if __name__ == "__main__":
    pipeline = FaceExtractionPipeline()
    pipeline.run_pipeline()