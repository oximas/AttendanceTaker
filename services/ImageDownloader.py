"""
ImageDownloader.py
Downloads images from Google Drive and extracts zip files.
Handles folder downloading, zip extraction, and cleanup operations.
"""

import os
import zipfile
import gdown
from pathlib import Path
from config import DOWNLOADS_DIR, FACES_DIR


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


class ZipExtractor:
    """Handles zip file extraction and cleanup."""
    
    @staticmethod
    def find_zip_files(directory):
        """
        Find all zip files in directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            list: List of Path objects for zip files
        """
        return list(Path(directory).rglob("*.zip"))
    
    @staticmethod
    def get_extraction_path(zip_path, base_output_dir):
        """
        Determine extraction path based on parent folder.
        
        Args:
            zip_path: Path to zip file
            base_output_dir: Base output directory
            
        Returns:
            Path: Extraction directory path
        """
        parent_folder_name = zip_path.parent.name
        
        # If zip is directly in output_dir, use zip name
        if zip_path.parent == Path(base_output_dir):
            parent_folder_name = zip_path.stem
        
        return Path(base_output_dir) / parent_folder_name
    
    @staticmethod
    def extract_zip(zip_path, extract_path):
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
    
    @staticmethod
    def cleanup_after_extraction(zip_path, base_output_dir):
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
        self.extractor = ZipExtractor()
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def download_and_extract(self, folder_url):
        """
        Download and extract all zip files from Google Drive folder.
        
        Args:
            folder_url: Google Drive folder URL
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Download files
            success = self.downloader.download_folder(folder_url, self.output_dir)
            if not success:
                return False
            
            # Extract zips
            self._extract_all_zips()
            
            print("\n" + "="*50)
            print("Download and extraction complete!")
            print("="*50)
            return True
            
        except Exception as e:
            print(f"Error in download_and_extract: {str(e)}")
            return False
    
    def _extract_all_zips(self):
        """Extract all zip files in output directory."""
        print("\n" + "="*50)
        print("Extracting zip files...")
        print("="*50 + "\n")
        
        zip_files = self.extractor.find_zip_files(self.output_dir)
        
        if not zip_files:
            print("No zip files found.")
            return
        
        for zip_path in zip_files:
            self._extract_single_zip(zip_path)
    
    def _extract_single_zip(self, zip_path):
        """Extract a single zip file with logging."""
        extract_path = self.extractor.get_extraction_path(
            zip_path,
            self.output_dir
        )
        
        print(f"Extracting: {zip_path.name}")
        print(f"   From folder: {zip_path.parent.name}")
        print(f"   -> To: {extract_path}")
        
        try:
            num_files = self.extractor.extract_zip(zip_path, extract_path)
            print(f"   ✓ Extracted {num_files} files")
            
            self.extractor.cleanup_after_extraction(
                zip_path,
                self.output_dir
            )
            print(f"   ✓ Deleted zip file")
            
            # Check if parent folder was removed
            if not zip_path.parent.exists():
                print(f"   ✓ Removed empty folder: {zip_path.parent.name}")
            
        except zipfile.BadZipFile:
            print(f"   ✗ Error: Not a valid zip file")
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
        
        print()


def main():
    """Main entry point."""
    # Google Drive folder URL
    url = "https://drive.google.com/drive/folders/1pZBcKW5CpQORjYXAnPZrHHeV0MtWNTHx"
    
    # Download and extract
    manager = ImageDownloadManager(output_dir=DOWNLOADS_DIR)
    success = manager.download_and_extract(url)
    
    if success:
        print(f"\nAll files extracted to '{DOWNLOADS_DIR}' folder.")
    else:
        print("\nDownload/extraction failed.")


if __name__ == "__main__":
    main()