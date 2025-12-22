"""
Face Preprocessing Module
Extracts faces from downloaded images and organizes them for training.
"""
from pathlib import Path
from typing import List, Dict, Tuple
from tqdm import tqdm

from FaceDetector import FaceDetector
from FaceStorage import FaceStorage, ImageLoader


# Default directories
DEFAULT_SOURCE_DIR = "Downloaded_Faces"
DEFAULT_TARGET_DIR = r"C:\D\programming\ML\TinyExpirements\PersonExists\AttendanceTaker\Faces"


class PreprocessingStatistics:
    """Tracks statistics during preprocessing."""
    
    def __init__(self):
        """Initialize statistics."""
        self.total_people = 0
        self.total_images = 0
        self.total_faces = 0
        self.people_data: List[Dict] = []
    
    def add_person_data(self, person_name: str, images_count: int, faces_count: int):
        """Add data for a processed person."""
        self.total_images += images_count
        self.total_faces += faces_count
        self.people_data.append({
            'name': person_name,
            'images': images_count,
            'faces': faces_count
        })
    
    def increment_people_count(self):
        """Increment total people counter."""
        self.total_people += 1
    
    def get_summary(self) -> Dict:
        """Get summary of statistics."""
        return {
            'total_people': self.total_people,
            'total_images': self.total_images,
            'total_faces': self.total_faces,
            'people_processed': self.people_data
        }


class FacePreprocessor:
    """
    Preprocesses downloaded images by extracting faces.
    Organizes faces into person-specific directories for training.
    """
    
    def __init__(self, source_directory: str, target_directory: str):
        """
        Initialize the face preprocessor.
        
        Args:
            source_directory: Directory containing person folders with images
            target_directory: Directory where extracted faces will be saved
        """
        self.source_directory = Path(source_directory)
        self.target_directory = Path(target_directory)
        
        # Initialize components
        self.detector = FaceDetector()
        self.storage = FaceStorage(target_directory)
        self.image_loader = ImageLoader()
        self.stats = PreprocessingStatistics()
    
    def process_all_people(self) -> Dict:
        """
        Process all person folders in source directory.
        
        Returns:
            Dictionary with processing statistics
            
        Raises:
            RuntimeError: If source directory doesn't exist or has no person folders
        """
        self._validate_source_directory()
        
        person_folders = self._get_person_folders()
        
        if not person_folders:
            raise RuntimeError(f"No person folders found in: {self.source_directory}")
        
        self._print_processing_header(person_folders)
        
        # Process each person
        for person_name in person_folders:
            self._process_single_person(person_name)
        
        self._print_processing_summary()
        
        return self.stats.get_summary()
    
    def process_single_person(self, person_name: str) -> Tuple[int, int]:
        """
        Process all images for a single person.
        
        Args:
            person_name: Name of the person (folder name)
            
        Returns:
            Tuple of (images_processed, faces_extracted)
        """
        return self._process_single_person(person_name)
    
    def process_single_image(
        self, 
        image_path: str, 
        person_name: str
    ) -> int:
        """
        Process a single image and save extracted faces.
        
        Args:
            image_path: Path to the image
            person_name: Name to associate with faces
            
        Returns:
            Number of faces extracted
        """
        image_path = Path(image_path)
        
        # Load image
        image = self.image_loader.load_image(str(image_path))
        if image is None:
            print(f"✗ Failed to load: {image_path}")
            return 0
        
        # Detect and extract faces
        boxes = self.detector.detect_faces(image)
        
        if not boxes:
            print(f"⚠ No faces detected in: {image_path.name}")
            return 0
        
        # Determine starting face number
        existing_count = self.storage.count_faces_for_person(person_name)
        face_number = existing_count + 1
        
        # Save each detected face
        saved_count = 0
        for box in boxes:
            face = self.detector.extract_face_region(image, box)
            
            if face is not None and face.size > 0:
                self.storage.save_face(face, person_name)
                face_number += 1
                saved_count += 1
        
        return saved_count
    
    def _validate_source_directory(self):
        """Validate that source directory exists."""
        if not self.source_directory.exists():
            raise RuntimeError(f"Source directory does not exist: {self.source_directory}")
    
    def _get_person_folders(self) -> List[str]:
        """Get list of person folder names in source directory."""
        return [
            d.name for d in self.source_directory.iterdir()
            if d.is_dir()
        ]
    
    def _process_single_person(self, person_name: str) -> Tuple[int, int]:
        """
        Process all images for a person.
        
        Returns:
            Tuple of (images_processed, faces_extracted)
        """
        person_source_dir = self.source_directory / person_name
        
        if not person_source_dir.is_dir():
            print(f"✗ Not a directory: {person_source_dir}")
            return 0, 0
        
        # Get all image files
        image_files = self.image_loader.find_image_files(str(person_source_dir))
        
        if not image_files:
            print(f"⚠ No images found for: {person_name}")
            return 0, 0
        
        print(f"\nProcessing: {person_name} ({len(image_files)} images)")
        
        # Process each image
        total_faces = 0
        existing_count = self.storage.count_faces_for_person(person_name)
        face_counter = existing_count + 1
        
        for image_path in tqdm(image_files, desc="  Extracting faces"):
            faces_from_image = self._extract_faces_from_image(
                image_path,
                person_name,
                face_counter
            )
            face_counter += faces_from_image
            total_faces += faces_from_image
        
        print(f"  ✓ Extracted {total_faces} faces from {len(image_files)} images")
        
        # Update statistics
        self.stats.add_person_data(person_name, len(image_files), total_faces)
        self.stats.increment_people_count()
        
        return len(image_files), total_faces
    
    def _extract_faces_from_image(
        self,
        image_path: Path,
        person_name: str,
        starting_face_number: int
    ) -> int:
        """
        Extract all faces from a single image.
        
        Returns:
            Number of faces extracted and saved
        """
        # Load image
        image = self.image_loader.load_image(str(image_path))
        
        if image is None:
            print(f"   ✗ Failed to read: {image_path.name}")
            return 0
        
        # Detect faces
        boxes = self.detector.detect_faces(image)
        
        if not boxes:
            print(f"   ⚠ No faces in: {image_path.name}")
            return 0
        
        # Extract and save each face
        saved_count = 0
        for box in boxes:
            face = self.detector.extract_face_region(image, box)
            
            if face is not None and face.size > 0:
                self.storage.save_face(face, person_name)
                saved_count += 1
        
        return saved_count
    
    def _print_processing_header(self, person_folders: List[str]):
        """Print header information before processing."""
        print("=" * 60)
        print("Face Extraction Started")
        print(f"Source: {self.source_directory}")
        print(f"Target: {self.target_directory}")
        print(f"People: {len(person_folders)}")
        print("=" * 60)
    
    def _print_processing_summary(self):
        """Print summary after processing completes."""
        stats = self.stats.get_summary()
        
        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETE")
        print("=" * 60)
        print(f"Total People:  {stats['total_people']}")
        print(f"Total Images:  {stats['total_images']}")
        print(f"Total Faces:   {stats['total_faces']}")
        print(f"Saved to:      {self.target_directory}")
        print("=" * 60)


def preprocess_downloaded_faces(
    source_directory: str = DEFAULT_SOURCE_DIR,
    target_directory: str = DEFAULT_TARGET_DIR
) -> Dict:
    """
    Convenience function to preprocess downloaded faces.
    
    Args:
        source_directory: Directory containing downloaded person folders
        target_directory: Directory where faces will be saved
        
    Returns:
        Statistics dictionary
    """
    preprocessor = FacePreprocessor(source_directory, target_directory)
    return preprocessor.process_all_people()


if __name__ == "__main__":
    try:
        # Process all downloaded faces
        stats = preprocess_downloaded_faces()
        
        print("\n✓ Preprocessing complete!")
        print(f"\nYou can now train the model with {stats['total_faces']} faces")
        print("from the Faces directory.")
        
    except Exception as e:
        print(f"✗ Error during preprocessing: {e}")