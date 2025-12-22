"""
Face Recognition Module
High-level face recognition system combining detection, embedding, and matching.
"""
import os
import numpy as np
from pathlib import Path
from tqdm import tqdm
from typing import Optional, Tuple, List

from FaceDetector import FaceDetector
from FaceEmbedder import FaceEmbedder, EmbeddingMatcher
from FaceStorage import FaceStorage, ImageLoader


# Configuration
MODELS_DIR = r"C:\D\programming\ML\TinyExpirements\PersonExists\AttendanceTaker\Models"
FACES_DIR = r"C:\D\programming\ML\TinyExpirements\PersonExists\AttendanceTaker\Faces"
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


class FaceRecognitionModel:
    """Stores and manages trained face recognition data."""
    
    def __init__(self):
        """Initialize empty model."""
        self.embeddings: Optional[np.ndarray] = None
        self.labels: Optional[np.ndarray] = None
    
    def add_training_data(
        self, 
        embeddings: List[np.ndarray], 
        labels: List[str]
    ):
        """
        Add training data to the model.
        
        Args:
            embeddings: List of face embeddings
            labels: List of corresponding person names
        """
        if not embeddings or not labels:
            raise ValueError("Embeddings and labels cannot be empty")
        
        if len(embeddings) != len(labels):
            raise ValueError("Number of embeddings must match number of labels")
        
        self.embeddings = np.array(embeddings)
        self.labels = np.array(labels)
    
    def save(self, directory: str, model_name: str = "face_model"):
        """
        Save model to disk.
        
        Args:
            directory: Directory to save model files
            model_name: Base name for model files
        """
        if not self.is_trained():
            raise RuntimeError("Cannot save untrained model")
        
        os.makedirs(directory, exist_ok=True)
        
        embeddings_path = Path(directory) / f"{model_name}_embeddings.npy"
        labels_path = Path(directory) / f"{model_name}_labels.npy"
        
        np.save(str(embeddings_path), self.embeddings)
        np.save(str(labels_path), self.labels)
    
    def load(self, directory: str, model_name: str = "face_model") -> bool:
        """
        Load model from disk.
        
        Args:
            directory: Directory containing model files
            model_name: Base name of model files
            
        Returns:
            True if successful, False otherwise
        """
        embeddings_path = Path(directory) / f"{model_name}_embeddings.npy"
        labels_path = Path(directory) / f"{model_name}_labels.npy"
        
        if not embeddings_path.exists() or not labels_path.exists():
            return False
        
        self.embeddings = np.load(str(embeddings_path))
        self.labels = np.load(str(labels_path))
        
        return True
    
    def is_trained(self) -> bool:
        """Check if model has been trained or loaded."""
        return self.embeddings is not None and self.labels is not None
    
    def get_training_stats(self) -> dict:
        """Get statistics about training data."""
        if not self.is_trained():
            return {"total_faces": 0, "total_people": 0}
        
        return {
            "total_faces": len(self.embeddings),
            "total_people": len(np.unique(self.labels))
        }


class FaceRecognizer:
    """Main face recognition system."""
    
    def __init__(
        self, 
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ):
        """
        Initialize face recognizer.
        
        Args:
            confidence_threshold: Minimum confidence for recognition
        """
        self.detector = FaceDetector()
        self.embedder = FaceEmbedder()
        self.matcher = EmbeddingMatcher()
        self.model = FaceRecognitionModel()
        self.confidence_threshold = confidence_threshold
    
    def train_from_directory(
        self, 
        faces_directory: str
    ) -> Tuple[int, int]:
        """
        Train the recognizer on a directory of labeled faces.
        
        Args:
            faces_directory: Directory with person subdirectories
            
        Returns:
            Tuple of (total_faces, total_people)
        """
        trainer = FaceRecognitionTrainer(
            faces_directory=faces_directory,
            detector=self.detector,
            embedder=self.embedder
        )
        
        embeddings, labels = trainer.train()
        self.model.add_training_data(embeddings, labels)
        
        stats = self.model.get_training_stats()
        return stats["total_faces"], stats["total_people"]
    
    def save_model(self, directory: str = MODELS_DIR):
        """Save trained model to disk."""
        self.model.save(directory)
    
    def load_model(self, directory: str = MODELS_DIR) -> bool:
        """Load trained model from disk."""
        return self.model.load(directory)
    
    def has_trained_model(self) -> bool:
        """Check if model is trained."""
        return self.model.is_trained()
    
    def recognize_face(
        self, 
        face_image: np.ndarray
    ) -> Tuple[str, float]:
        """
        Recognize a person from their face image.
        
        Args:
            face_image: Face image as numpy array
            
        Returns:
            Tuple of (person_name, confidence_score)
        """
        if not self.model.is_trained():
            return "Unknown", 0.0
        
        # Generate embedding
        embedding = self.embedder.generate_embedding(face_image)
        
        if embedding is None:
            return "Unknown", 0.0
        
        # Find best match
        best_idx, similarity = self.matcher.find_best_match(
            embedding,
            self.model.embeddings,
            self.confidence_threshold
        )
        
        if best_idx == -1:
            return "Unknown", similarity
        
        return str(self.model.labels[best_idx]), similarity
    
    def recognize_from_bounding_box(
        self,
        image: np.ndarray,
        box: Tuple[int, int, int, int]
    ) -> Tuple[str, float]:
        """
        Recognize person from image and bounding box.
        
        Args:
            image: Full image
            box: Face bounding box (x1, y1, x2, y2)
            
        Returns:
            Tuple of (person_name, confidence_score)
        """
        face = self.detector.extract_face_region(
            image, 
            box, 
            target_size=FaceEmbedder.FACENET_INPUT_SIZE
        )
        
        if face is None:
            return "Unknown", 0.0
        
        return self.recognize_face(face)


class FaceRecognitionTrainer:
    """Handles the training process for face recognition."""
    
    def __init__(
        self,
        faces_directory: str,
        detector: FaceDetector,
        embedder: FaceEmbedder
    ):
        """
        Initialize trainer.
        
        Args:
            faces_directory: Directory containing person subdirectories
            detector: Face detector instance
            embedder: Face embedder instance
        """
        self.faces_directory = Path(faces_directory)
        self.detector = detector
        self.embedder = embedder
        self.image_loader = ImageLoader()
    
    def train(self) -> Tuple[List[np.ndarray], List[str]]:
        """
        Train on all faces in the directory.
        
        Returns:
            Tuple of (embeddings_list, labels_list)
        """
        if not self.faces_directory.exists():
            raise RuntimeError(f"Directory does not exist: {self.faces_directory}")
        
        person_folders = self._get_person_folders()
        
        if not person_folders:
            raise RuntimeError(f"No person folders found in {self.faces_directory}")
        
        print(f"\n=== Training on {len(person_folders)} people ===")
        
        all_embeddings = []
        all_labels = []
        
        for person_name in tqdm(person_folders, desc="Processing people"):
            embeddings = self._process_person_folder(person_name)
            
            for embedding in embeddings:
                all_embeddings.append(embedding)
                all_labels.append(person_name)
        
        if not all_embeddings:
            raise RuntimeError("No valid face embeddings generated")
        
        print(f"Training complete: {len(all_embeddings)} embeddings from {len(person_folders)} people")
        
        return all_embeddings, all_labels
    
    def _get_person_folders(self) -> List[str]:
        """Get list of person folder names."""
        return [
            d.name for d in self.faces_directory.iterdir()
            if d.is_dir()
        ]
    
    def _process_person_folder(self, person_name: str) -> List[np.ndarray]:
        """
        Process all images in a person's folder.
        
        Args:
            person_name: Name of the person
            
        Returns:
            List of embeddings for this person
        """
        person_dir = self.faces_directory / person_name
        embeddings = []
        
        # Load all images
        images = self.image_loader.load_all_images_from_directory(str(person_dir))
        
        for filepath, image in images:
            # Detect face
            boxes = self.detector.detect_faces(image)
            
            if not boxes:
                continue
            
            # Use largest face if multiple detected
            box = self.detector._get_largest_box(boxes)
            face = self.detector.extract_face_region(
                image, 
                box,
                target_size=FaceEmbedder.FACENET_INPUT_SIZE
            )
            
            if face is None:
                continue
            
            # Generate embedding
            embedding = self.embedder.generate_embedding(face)
            
            if embedding is not None:
                embeddings.append(embedding)
        
        return embeddings


# Maintain backward compatibility
CONFIDENCE_THRESHOLD = DEFAULT_CONFIDENCE_THRESHOLD