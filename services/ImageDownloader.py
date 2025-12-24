"""
services/ImageDownloader.py
Downloads images from Google Drive and extracts zip files.
Handles folder downloading, zip extraction, student ID/name extraction, and cleanup operations.
Updates student database with extracted information.
NOW WITH NAME SANITIZATION: Removes non-alphabetic characters and numbers from names.
"""

import os
import zipfile
import gdown
import re
from pathlib import Path
from config import DOWNLOADS_DIR, WRONG_FORMAT_LOG_FILE
from services.StudentDatabase import StudentDatabase


class GoogleDriveDownloader:
    """Handles downloading files from Google Drive."""
    
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
        Download all files from a Google Drive folder.
        
        Args:
            folder_url: Google Drive folder URL
            output_dir: Directory to save files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            folder_id = GoogleDriveDownloader.extract_folder_id(folder_url)
            
            print(f"Downloading from folder: {folder_id}")
            
            gdown.download_folder(
                id=folder_id,
                output=output_dir,
                quiet=False,
                use_cookies=False
            )
            return True
            
        except Exception as e:
            print(f"Download error: {str(e)}")
            return False


class StudentInfoExtractor:
    """Extracts student ID and name from zip filenames with name sanitization."""
    
    @staticmethod
    def sanitize_name(raw_name):
        """
        Sanitize student name by removing non-alphabetic characters and numbers.
        
        Args:
            raw_name: Raw name from zip file (e.g., "Omar-Ashraf-Shokry123")
            
        Returns:
            str: Sanitized name (e.g., "Omar Ashraf Shokry")
        """
        # Replace all non-alphabetic characters (except spaces) with space
        # This handles: - _ . , ; : etc.
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
            zip_filename: Zip file name (e.g., "Omar-Ashraf-Shokry_22010951.zip")
            
        Returns:
            tuple: (student_id, student_name) or (None, None) if invalid format
        """
        # Remove .zip extension
        name_without_ext = zip_filename.replace('.zip', '')
        
        # Split by underscore from right (to handle names with underscores)
        parts = name_without_ext.rsplit('_', 1)
        
        if len(parts) != 2:
            print(f"Invalid format: Expected Name_ID.zip, got {zip_filename}")
            return None, None
        
        raw_name, student_id = parts
        
        # Validate ID is numeric
        if not student_id.isdigit():
            print(f"Invalid ID: {student_id} is not numeric")
            return None, None
        
        # Sanitize the name
        student_name = StudentInfoExtractor.sanitize_name(raw_name)
        
        if not student_name:
            print(f"Invalid name: Name became empty after sanitization")
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
        return list(Path(directory).rglob("*.zip"))
    
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
        
        # Extract ID and name (with sanitization)
        student_id, student_name = StudentInfoExtractor.extract_id_and_name(zip_filename)
        
        if not student_id:
            # Log invalid format
            StudentInfoExtractor.log_invalid_format(zip_filename, WRONG_FORMAT_LOG_FILE)
            return None, None, None
        
        # Add student to database with sanitized name
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
            # Download files
            success = self.downloader.download_folder(folder_url, self.output_dir)
            if not success:
                return {'success': False}
            
            # Extract zips and update database
            stats = self._extract_all_zips()
            
            print("\n" + "="*50)
            print("Download and extraction complete!")
            print("="*50)
            
            stats['success'] = True
            return stats
            
        except Exception as e:
            print(f"Error in download_and_extract: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_all_zips(self):
        """
        Extract all zip files in output directory.
        
        Returns:
            dict: Extraction statistics
        """
        print("\n" + "="*50)
        print("Extracting zip files and updating database...")
        print("="*50 + "\n")
        
        zip_files = self.extractor.find_zip_files(self.output_dir)
        
        stats = {
            'total_zips': len(zip_files),
            'extracted': 0,
            'invalid_format': 0,
            'errors': 0
        }
        
        if not zip_files:
            print("No zip files found.")
            return stats
        
        for zip_path in zip_files:
            result = self._extract_single_zip(zip_path)
            if result == 'extracted':
                stats['extracted'] += 1
            elif result == 'invalid':
                stats['invalid_format'] += 1
            elif result == 'error':
                stats['errors'] += 1
        
        # Print summary
        print(f"\nTotal zip files: {stats['total_zips']}")
        print(f"Successfully extracted: {stats['extracted']}")
        print(f"Invalid format (logged): {stats['invalid_format']}")
        print(f"Errors: {stats['errors']}")
        
        return stats
    
    def _extract_single_zip(self, zip_path):
        """
        Extract a single zip file with logging.
        
        Returns:
            str: 'extracted', 'invalid', or 'error'
        """
        print(f"Processing: {zip_path.name}")
        
        try:
            # Get extraction path and student info
            extract_path, student_id, student_name = self.extractor.get_extraction_path(
                zip_path,
                self.output_dir
            )
            
            if not extract_path:
                print(f"   ✗ Invalid format - logged to error file")
                return 'invalid'
            
            print(f"   Student ID: {student_id}")
            print(f"   Student Name: {student_name}")
            print(f"   -> Extracting to: {extract_path}")
            
            # Extract
            num_files = self.extractor.extract_zip(zip_path, extract_path)
            print(f"   ✓ Extracted {num_files} files")
            
            # Cleanup
            self.extractor.cleanup_after_extraction(zip_path, self.output_dir)
            print(f"   ✓ Deleted zip file")
            
            # Check if parent folder was removed
            if not zip_path.parent.exists():
                print(f"   ✓ Removed empty folder: {zip_path.parent.name}")
            
            print()
            return 'extracted'
            
        except zipfile.BadZipFile:
            print(f"   ✗ Error: Not a valid zip file")
            print()
            return 'error'
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
            print()
            return 'error'


def main():
    """Main entry point."""
    # Google Drive folder URL
    url = "https://drive.google.com/drive/folders/1pZBcKW5CpQORjYXAnPZrHHeV0MtWNTHx"
    
    # Download and extract
    manager = ImageDownloadManager(output_dir=DOWNLOADS_DIR)
    result = manager.download_and_extract(url)
    
    if result.get('success'):
        print(f"\nAll files extracted to '{DOWNLOADS_DIR}' folder.")
        print(f"Student database updated with {result.get('extracted', 0)} students.")
    else:
        print("\nDownload/extraction failed.")


if __name__ == "__main__":
    main()