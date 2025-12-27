"""
services/ImageDownloader.py
Downloads and processes student images from Google Drive.
Handles zip file extraction, student database updates, and file organization.
Fixed for PyInstaller: Suppresses gdown progress output to prevent stdout errors.
"""

import os
import sys
import zipfile
import gdown
import re
from pathlib import Path
from config import DOWNLOADS_DIR, WRONG_FORMAT_LOG_FILE
from services.StudentDatabase import StudentDatabase
from logger import log_info, log_warning, log_error, log_section


class GoogleDriveDownloader:
    """Handles downloading files from Google Drive with stdout suppression."""
    
    @staticmethod
    def extract_folder_id(folder_url):
        """
        Extract folder ID from Google Drive URL.
        
        Args:
            folder_url: Google Drive folder URL or ID
            
        Returns:
            str: Folder ID
        """
        if "folders/" in folder_url:
            return folder_url.split("folders/")[1].split("?")[0]
        return folder_url
    
    @staticmethod
    def download_folder(folder_url, output_dir):
        """
        Download all files from a Google Drive folder with suppressed output.
        
        Args:
            folder_url: Google Drive folder URL
            output_dir: Directory to save files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            folder_id = GoogleDriveDownloader.extract_folder_id(folder_url)
            
            log_info(f"Starting download from Google Drive folder: {folder_id}")
            
            # Suppress gdown progress output for PyInstaller
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = open(os.devnull, 'w')
                sys.stderr = open(os.devnull, 'w')
                
                gdown.download_folder(
                    id=folder_id,
                    output=output_dir,
                    quiet=True,  # Suppress output
                    use_cookies=False
                )
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
            log_info("Download completed successfully")
            return True
            
        except Exception as e:
            log_error("Google Drive download failed", e)
            return False


class StudentInfoExtractor:
    """Extracts student ID and name from zip filenames with name sanitization."""
    
    @staticmethod
    def sanitize_name(raw_name):
        """
        Sanitize student name by removing non-alphabetic characters and numbers.
        
        Args:
            raw_name: Raw name from zip file
            
        Returns:
            str: Sanitized name
        """
        # Replace all non-alphabetic characters (except spaces) with space
        sanitized = re.sub(r'[^a-zA-Z\s]', ' ', raw_name)
        
        # Normalize multiple spaces to single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Strip leading/trailing spaces
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def extract_id_and_name(zip_filename):
        """
        Extract student ID and name from zip filename.
        Expected format: Name_ID.zip
        
        Args:
            zip_filename: Zip file name
            
        Returns:
            tuple: (student_id, student_name) or (None, None) if invalid format
        """
        # Remove .zip extension
        name_without_ext = zip_filename.replace('.zip', '')
        
        # Split by underscore from right
        parts = name_without_ext.rsplit('_', 1)
        
        if len(parts) != 2:
            log_warning(f"Invalid filename format: {zip_filename} (expected Name_ID.zip)")
            return None, None
        
        raw_name, student_id = parts
        
        # Validate ID is numeric
        if not student_id.isdigit():
            log_warning(f"Invalid student ID in {zip_filename}: {student_id} is not numeric")
            return None, None
        
        # Sanitize the name
        student_name = StudentInfoExtractor.sanitize_name(raw_name)
        
        if not student_name:
            log_warning(f"Invalid name in {zip_filename}: name became empty after sanitization")
            return None, None
        
        return student_id, student_name
    
    @staticmethod
    def log_invalid_format(zip_filename, log_file):
        """
        Log invalid zip filename to error file.
        
        Args:
            zip_filename: Invalid zip filename
            log_file: Path to log file
        """
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{zip_filename}\n")


class ZipExtractor:
    """Handles zip file extraction and cleanup."""
    
    def __init__(self, student_db):
        self.student_db = student_db
    
    def find_zip_files(self, directory):
        """
        Find all zip files in directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            list: List of Path objects for zip files
        """
        zip_files = list(Path(directory).rglob("*.zip"))
        log_info(f"Found {len(zip_files)} zip files in {directory}")
        return zip_files
    
    def get_extraction_path(self, zip_path, base_output_dir):
        """
        Determine extraction path using student ID.
        
        Args:
            zip_path: Path to zip file
            base_output_dir: Base output directory
            
        Returns:
            tuple: (Path object, student_id, student_name) or (None, None, None) if invalid
        """
        zip_filename = zip_path.name
        
        # Extract ID and name
        student_id, student_name = StudentInfoExtractor.extract_id_and_name(zip_filename)
        
        if not student_id:
            # Log invalid format
            StudentInfoExtractor.log_invalid_format(zip_filename, WRONG_FORMAT_LOG_FILE)
            return None, None, None
        
        # Add student to database
        self.student_db.add_student(student_id, student_name)
        
        # Use ID as folder name
        extract_path = Path(base_output_dir) / student_id
        
        return extract_path, student_id, student_name
    
    def extract_zip(self, zip_path, extract_path):
        """
        Extract a zip file to target directory.
        
        Args:
            zip_path: Path to zip file
            extract_path: Directory to extract to
            
        Returns:
            int: Number of files extracted
        """
        extract_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            return len(zip_ref.namelist())
    
    def cleanup_after_extraction(self, zip_path, base_output_dir):
        """
        Remove zip file and empty parent folders.
        
        Args:
            zip_path: Path to zip file to remove
            base_output_dir: Base output directory
        """
        # Remove zip file
        zip_path.unlink()
        
        # Remove empty parent folder if not base directory
        parent = zip_path.parent
        if parent != Path(base_output_dir) and not any(parent.iterdir()):
            parent.rmdir()


class ImageDownloadManager:
    """Main manager for downloading and extracting images."""
    
    def __init__(self, output_dir=DOWNLOADS_DIR):
        self.output_dir = output_dir
        self.downloader = GoogleDriveDownloader()
        self.student_db = StudentDatabase()
        self.extractor = ZipExtractor(self.student_db)
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def download_and_extract(self, folder_url):
        """
        Download and extract all zip files from Google Drive folder.
        
        Args:
            folder_url: Google Drive folder URL
            
        Returns:
            dict: Statistics about the process
        """
        try:
            log_section("DOWNLOADING FROM GOOGLE DRIVE")
            
            # Download files
            success = self.downloader.download_folder(folder_url, self.output_dir)
            if not success:
                return {'success': False, 'error': 'Download failed'}
            
            # Extract zips and update database
            log_section("EXTRACTING ZIP FILES")
            stats = self._extract_all_zips()
            
            log_info("Download and extraction complete!")
            
            stats['success'] = True
            return stats
            
        except Exception as e:
            log_error("Download and extraction failed", e)
            return {'success': False, 'error': str(e)}
    
    def _extract_all_zips(self):
        """
        Extract all zip files in output directory.
        
        Returns:
            dict: Extraction statistics
        """
        zip_files = self.extractor.find_zip_files(self.output_dir)
        
        stats = {
            'total_zips': len(zip_files),
            'extracted': 0,
            'invalid_format': 0,
            'errors': 0
        }
        
        if not zip_files:
            log_warning("No zip files found to extract")
            return stats
        
        for zip_path in zip_files:
            result = self._extract_single_zip(zip_path)
            if result == 'extracted':
                stats['extracted'] += 1
            elif result == 'invalid':
                stats['invalid_format'] += 1
            elif result == 'error':
                stats['errors'] += 1
        
        log_info(f"Extraction summary: {stats['extracted']} extracted, {stats['invalid_format']} invalid, {stats['errors']} errors")
        
        return stats
    
    def _extract_single_zip(self, zip_path):
        """
        Extract a single zip file with logging.
        
        Returns:
            str: 'extracted', 'invalid', or 'error'
        """
        log_info(f"Processing: {zip_path.name}")
        
        try:
            # Get extraction path and student info
            extract_path, student_id, student_name = self.extractor.get_extraction_path(
                zip_path,
                self.output_dir
            )
            
            if not extract_path:
                log_warning(f"Invalid format: {zip_path.name} (logged to error file)")
                return 'invalid'
            
            log_info(f"  Student ID: {student_id}, Name: {student_name}")
            
            # Extract
            num_files = self.extractor.extract_zip(zip_path, extract_path)
            log_info(f"  Extracted {num_files} files to {extract_path}")
            
            # Cleanup
            self.extractor.cleanup_after_extraction(zip_path, self.output_dir)
            
            return 'extracted'
            
        except zipfile.BadZipFile:
            log_error(f"Invalid zip file: {zip_path.name}")
            return 'error'
        except Exception as e:
            log_error(f"Error processing {zip_path.name}", e)
            return 'error'