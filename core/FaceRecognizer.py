"""
core/FaceRecognizer.py
Face Recognition module with FaceNet embeddings.
Handles face recognition using FaceNet embeddings.
Separated concerns: embedding generation, model management, prediction.
Logs training and recognition operations.
"""

import os
import numpy as np
from keras_facenet import FaceNet
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from core.FaceDetector import FaceDetector
from core.FaceImageProcessor import FaceImageProcessor
from storage.FaceStorage import FaceStorage
from logger import log_info, log_error, log_warning, log_section
from config import (
    MODELS_DIR, CONFIDENCE_THRESHOLD,
    DEFAULT_MODEL_NAME, EMBEDDINGS_SUFFIX, LABELS_SUFFIX
)


class EmbeddingGenerator:
    """Generates face embeddings using FaceNet."""
    
    def __init__(self):
        self.embedder = FaceNet()
        log_info("FaceNet embedder initialized")
    
    def generate(self, face_image):
        """
        Generate embedding for a face image.
        
        Args:
            face_image: Face image (160x160)
            
        Returns:
            numpy.ndarray: Embedding vector, or None if failed
        """
        if face_image is None or face_image.size == 0:
            return None
        
        try:
            embedding = self.embedder.embeddings([face_image])[0]
            return embedding
        except Exception as e:
            log_error(f"Failed to generate embedding", e)
            return None


class ModelStorage:
    """Handles saving and loading of trained models."""
    
    def __init__(self, models_dir=MODELS_DIR):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
    
    def save(self, embeddings, labels, model_name=DEFAULT_MODEL_NAME):
        """
        Save embeddings and labels to disk.
        
        Args:
            embeddings: Numpy array of embeddings
            labels: Numpy array of labels
            model_name: Name for the model files
            
        Returns:
            tuple: (embeddings_path, labels_path)
        """
        emb_path = os.path.join(self.models_dir, f"{model_name}{EMBEDDINGS_SUFFIX}")
        lbl_path = os.path.join(self.models_dir, f"{model_name}{LABELS_SUFFIX}")
        
        np.save(emb_path, embeddings)
        np.save(lbl_path, labels)
        
        log_info(f"Model saved: {emb_path}, {lbl_path}")
        
        return emb_path, lbl_path
    
    def load(self, model_name=DEFAULT_MODEL_NAME):
        """
        Load embeddings and labels from disk.
        
        Args:
            model_name: Name of the model files
            
        Returns:
            tuple: (embeddings, labels) or (None, None) if not found
        """
        emb_path = os.path.join(self.models_dir, f"{model_name}{EMBEDDINGS_SUFFIX}")
        lbl_path = os.path.join(self.models_dir, f"{model_name}{LABELS_SUFFIX}")
        
        if not os.path.exists(emb_path) or not os.path.exists(lbl_path):
            log_warning(f"Model files not found: {model_name}")
            return None, None
        
        embeddings = np.load(emb_path)
        labels = np.load(lbl_path)
        
        log_info(f"Model loaded: {len(embeddings)} embeddings, {len(set(labels))} unique students")
        
        return embeddings, labels
    
    def exists(self, model_name=DEFAULT_MODEL_NAME):
        """Check if model files exist."""
        emb_path = os.path.join(self.models_dir, f"{model_name}{EMBEDDINGS_SUFFIX}")
        lbl_path = os.path.join(self.models_dir, f"{model_name}{LABELS_SUFFIX}")
        return os.path.exists(emb_path) and os.path.exists(lbl_path)


class FaceRecognizer:
    """
    Main face recognition class.
    Coordinates embedding generation, training, and prediction.
    """
    
    def __init__(self):
        self.detector = FaceDetector()
        self.processor = FaceImageProcessor()
        self.embedding_gen = EmbeddingGenerator()
        self.model_storage = ModelStorage()
        self.face_storage = FaceStorage()
        
        self.embeddings = None
        self.labels = None
    
    def _process_person_images(self, person_name, progress_callback=None):
        """
        Load and process all images for a person.
        
        Args:
            person_name: Name of the person
            progress_callback: Optional callback(message) for progress updates
            
        Returns:
            list: List of embeddings for this person
        """
        images = self.face_storage.load_person_images(person_name)
        embeddings = []
        
        for img, _ in images:
            # Detect largest face
            face_data = self.detector.get_largest_face(img)
            if not face_data:
                continue
            
            # Crop and resize face
            face = self.processor.crop_face(img, face_data['box'])
            face = self.processor.resize_face(face)
            
            if face is None:
                continue
            
            # Generate embedding
            embedding = self.embedding_gen.generate(face)
            if embedding is not None:
                embeddings.append(embedding)
        
        return embeddings
    
    def train(self, progress_callback=None):
        """
        Train face recognition model from stored faces.
        
        Args:
            progress_callback: Optional callback(message) for progress updates
            
        Returns:
            tuple: (num_faces, num_people)
        """
        people = self.face_storage.list_people()
        
        if not people:
            msg = "No people found in face storage for training"
            log_error(msg)
            if progress_callback:
                progress_callback(f"✗ Error: {msg}")
            raise RuntimeError("No people found in face storage")
        
        embeddings_list = []
        labels_list = []
        
        log_section("TRAINING MODEL")
        if progress_callback:
            progress_callback("="*60)
            progress_callback("TRAINING MODEL")
            progress_callback("="*60)
            progress_callback(f"Training started: {len(people)} students")
        
        log_info(f"Training started: {len(people)} students")
        
        # Process each person
        for idx, person_name in enumerate(people, 1):
            if progress_callback:
                progress_callback(f"Processing student {idx}/{len(people)}: {person_name}")
            
            person_embeddings = self._process_person_images(person_name, progress_callback)
            
            for embedding in person_embeddings:
                embeddings_list.append(embedding)
                labels_list.append(person_name)
            
            if progress_callback:
                progress_callback(f"  → Found {len(person_embeddings)} face(s)")
        
        if not embeddings_list:
            msg = "No valid faces found for training"
            log_error(msg)
            if progress_callback:
                progress_callback(f"✗ Error: {msg}")
            raise RuntimeError("No valid faces found for training")
        
        self.embeddings = np.array(embeddings_list)
        self.labels = np.array(labels_list)
        
        log_info(f"Training complete: {len(self.embeddings)} embeddings from {len(people)} students")
        
        if progress_callback:
            progress_callback("")
            progress_callback(f"✓ Training complete!")
            progress_callback(f"  Total faces: {len(self.embeddings)}")
            progress_callback(f"  Total students: {len(people)}")
        
        return len(self.embeddings), len(people)
    
    def save_model(self, model_name=DEFAULT_MODEL_NAME):
        """Save trained model to disk."""
        if self.embeddings is None or self.labels is None:
            log_error("Cannot save model: No trained model exists")
            raise RuntimeError("No trained model to save")
        
        self.model_storage.save(self.embeddings, self.labels, model_name)
    
    def load_model(self, model_name=DEFAULT_MODEL_NAME):
        """
        Load trained model from disk.
        
        Returns:
            bool: True if loaded successfully
        """
        embeddings, labels = self.model_storage.load(model_name)
        
        if embeddings is None:
            return False
        
        self.embeddings = embeddings
        self.labels = labels
        
        return True
    
    def has_trained_model(self):
        """Check if model is trained or loaded."""
        return self.embeddings is not None and self.labels is not None
    
    def _find_best_match(self, embedding, threshold=CONFIDENCE_THRESHOLD):
        """
        Find best matching person for an embedding.
        
        Args:
            embedding: Face embedding
            threshold: Confidence threshold
            
        Returns:
            tuple: (name, confidence)
        """
        if not self.has_trained_model():
            return "Unknown", 0.0
        
        similarities = cosine_similarity([embedding], self.embeddings)[0]
        best_idx = np.argmax(similarities)
        best_score = float(similarities[best_idx])
        
        if best_score >= threshold:
            recognized_name = str(self.labels[best_idx])
            log_info(f"Face recognized: {recognized_name} (confidence: {best_score:.2f})")
            return recognized_name, best_score
        
        log_warning(f"Unknown face detected (best match: {best_score:.2f}, threshold: {threshold})")
        return "Unknown", best_score
    
    def predict_face(self, face_image, threshold=CONFIDENCE_THRESHOLD):
        """
        Predict name for a face image.
        
        Args:
            face_image: Face image (should be 160x160)
            threshold: Confidence threshold
            
        Returns:
            tuple: (name, confidence)
        """
        embedding = self.embedding_gen.generate(face_image)
        
        if embedding is None:
            return "Unknown", 0.0
        
        return self._find_best_match(embedding, threshold)
    
    def predict_from_box(self, image, box, threshold=CONFIDENCE_THRESHOLD):
        """
        Predict name from image and bounding box.
        
        Args:
            image: Source image
            box: Bounding box (x1, y1, x2, y2)
            threshold: Confidence threshold
            
        Returns:
            tuple: (name, confidence)
        """
        face = self.processor.crop_face(image, box)
        face = self.processor.resize_face(face)
        
        if face is None:
            return "Unknown", 0.0
        
        return self.predict_face(face, threshold)


if __name__ == "__main__":
    # Example usage
    recognizer = FaceRecognizer()
    
    try:
        def progress(msg):
            print(msg)
        
        num_faces, num_people = recognizer.train(progress_callback=progress)
        recognizer.save_model()
        print(f"\nTrained on {num_faces} faces from {num_people} people")
        
    except Exception as e:
        print(f"Error: {e}")