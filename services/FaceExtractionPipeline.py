"""
services/FaceExtractionPipeline.py
Processes downloaded images from DOWNLOADS_DIR, detects faces, and extracts them to FACES_DIR.
Handles single-face validation and organizes faces by student ID extracted from folder structure.
Logs all extraction operations for tracking progress and troubleshooting.
"""

import os
import cv2
from pathlib import Path
from config import DOWNLOADS_DIR, FACES_DIR
from core.FaceDetector import FaceDetector
from core.FaceImageProcessor import FaceImageProcessor
from storage.FaceStorage import FaceStorage
from logger import log_info, log_warning, log_error, log_section


class FaceExtractionPipeline:
    """
    Extracts faces from downloaded images and organizes them for training.
    Processes folder structure: DOWNLOADS_DIR/StudentID/images -> FACES_DIR/StudentID/faces
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
    
    def scan_student_folders(self):
        """
        Scan DOWNLOADS_DIR for student ID folders.
        
        Returns:
            list: List of (folder_path, student_id) tuples
        """
        if not os.path.exists(self.downloads_dir):
            log_warning(f"Downloads directory not found: {self.downloads_dir}")
            return []
        
        student_folders = []
        for item in os.listdir(self.downloads_dir):
            folder_path = os.path.join(self.downloads_dir, item)
            if os.path.isdir(folder_path):
                # Item is the student ID
                student_folders.append((folder_path, item))
        
        log_info(f"Found {len(student_folders)} student folders")
        return student_folders
    
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
                self.stats['errors'] += 1
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
            log_error(f"Error processing {image_path}", e)
            return None
    
    def process_student_folder(self, folder_path, student_id):
        """
        Process all images in a student's folder.
        
        Args:
            folder_path: Path to student's folder
            student_id: Student ID (folder name)
            
        Returns:
            int: Number of faces successfully extracted
        """
        image_files = self.get_image_files(folder_path)
        extracted_count = 0
        
        log_info(f"Processing Student ID: {student_id} ({len(image_files)} images)")
        
        for image_path in image_files:
            self.stats['total_images'] += 1
            
            # Extract face
            face = self.extract_single_face(image_path)
            
            if face is not None:
                # Save to FACES_DIR using student ID
                self.storage.save_face(face, student_id)
                extracted_count += 1
                self.stats['faces_extracted'] += 1
        
        log_info(f"  Extracted {extracted_count} faces for student {student_id}")
        return extracted_count
    
    def run_pipeline(self):
        """
        Run the complete extraction pipeline.
        
        Returns:
            dict: Statistics about the extraction process
        """
        log_section("FACE EXTRACTION PIPELINE")
        
        # Reset statistics
        self.stats = {
            'total_folders': 0,
            'total_images': 0,
            'faces_extracted': 0,
            'skipped_no_face': 0,
            'skipped_multiple_faces': 0,
            'errors': 0
        }
        
        # Scan for student folders
        student_folders = self.scan_student_folders()
        
        if not student_folders:
            log_warning(f"No student folders found in: {self.downloads_dir}")
            return self.stats
        
        self.stats['total_folders'] = len(student_folders)
        
        # Process each student folder
        for folder_path, student_id in student_folders:
            self.process_student_folder(folder_path, student_id)
        
        # Print summary
        self._print_summary()
        
        return self.stats
    
    def _print_summary(self):
        """Print extraction summary."""
        log_section("EXTRACTION SUMMARY")
        log_info(f"Total student folders processed: {self.stats['total_folders']}")
        log_info(f"Total images scanned: {self.stats['total_images']}")
        log_info(f"Faces extracted: {self.stats['faces_extracted']}")
        log_info(f"Skipped (no face): {self.stats['skipped_no_face']}")
        log_info(f"Skipped (multiple faces): {self.stats['skipped_multiple_faces']}")
        log_info(f"Errors: {self.stats['errors']}")


if __name__ == "__main__":
    pipeline = FaceExtractionPipeline()
    pipeline.run_pipeline()