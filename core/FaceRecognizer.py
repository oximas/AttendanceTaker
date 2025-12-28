"""
core/FaceRecognizer.py
Face recognition engine using FaceNet embeddings and cosine similarity.
Handles training from stored face images and prediction for new faces.
Fixed for PyInstaller: Suppresses FaceNet progress output to prevent stdout errors.
"""

import os
import sys
import numpy as np
from keras_facenet import FaceNet
from sklearn.metrics.pairwise import cosine_similarity

from core.FaceDetector import FaceDetector
from core.FaceImageProcessor import FaceImageProcessor
from storage.FaceStorage import FaceStorage
from logger import log_info, log_error, log_warning, log_debug
from config import (
    MODELS_DIR, CONFIDENCE_THRESHOLD,
    DEFAULT_MODEL_NAME, EMBEDDINGS_SUFFIX, LABELS_SUFFIX
)


class EmbeddingGenerator:
    """Generates face embeddings using FaceNet with stdout suppression."""
    
    def __init__(self):
        # Suppress FaceNet verbose output for PyInstaller
        import warnings
        warnings.filterwarnings('ignore')
        
        # Temporarily redirect stdout during FaceNet init
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')
            self.embedder = FaceNet()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        log_info("FaceNet embedder initialized")
    
    def generate(self, face_image):
        """
        Generate embedding for a face image with suppressed output.
        
        Args:
            face_image: Face image (160x160)
            
        Returns:
            numpy.ndarray: Embedding vector, or None if failed
        """
        if face_image is None or face_image.size == 0:
            return None
        
        try:
            # Suppress FaceNet progress output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = open(os.devnull, 'w')
                sys.stderr = open(os.devnull, 'w')
                embedding = self.embedder.embeddings([face_image])[0]
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
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
    Face recognition coordinator.
    Handles training from stored faces and prediction for new faces.
    """
    
    def __init__(self):
        self.detector = FaceDetector()
        self.processor = FaceImageProcessor()
        self.embedding_gen = EmbeddingGenerator()
        self.model_storage = ModelStorage()
        self.face_storage = FaceStorage()
        
        self.embeddings = None
        self.labels = None
    
    def _process_person_images(self, person_id, progress_callback=None):
        """
        Load and process all saved images for a person.
        FIXED: Skip detection since saved images are already cropped faces.
        
        Args:
            person_id: Student ID
            progress_callback: Optional callback for progress updates
            
        Returns:
            list: List of embeddings for this person
        """
        images = self.face_storage.load_person_images(person_id)
        
        if not images:
            log_warning(f"No images found for student ID: {person_id}")
            return []
        
        embeddings = []
        
        for img, img_path in images:
            try:
                # CRITICAL FIX: Don't re-detect faces!
                # These images are already cropped faces from Faces/ folder
                # Just resize and generate embedding directly
                
                # Resize to FaceNet input size (160x160)
                face = self.processor.resize_face(img)
                if face is None:
                    log_debug(f"Failed to resize face from {img_path}")
                    continue
                
                # Generate embedding directly
                embedding = self.embedding_gen.generate(face)
                if embedding is not None:
                    embeddings.append(embedding)
                    log_debug(f"Processed face from {img_path}")
                else:
                    log_debug(f"Failed to generate embedding from {img_path}")
                    
            except Exception as e:
                log_error(f"Error processing {img_path}", e)
                continue
        
        if embeddings:
            log_info(f"Student {person_id}: Processed {len(embeddings)}/{len(images)} images")
        else:
            log_warning(f"Student {person_id}: Failed to process any of {len(images)} images")
        
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
            msg = "No students found in Faces folder"
            log_error(msg)
            if progress_callback:
                progress_callback(f"✗ Error: {msg}")
            raise RuntimeError(msg)
        
        embeddings_list = []
        labels_list = []
        
        if progress_callback:
            progress_callback(f"Training started: {len(people)} students")
        
        log_info(f"Training started: {len(people)} students")
        
        # Process each person
        for idx, person_id in enumerate(people, 1):
            if progress_callback:
                progress_callback(f"Processing student {idx}/{len(people)}: {person_id}")
            
            person_embeddings = self._process_person_images(person_id, progress_callback)
            
            if not person_embeddings:
                if progress_callback:
                    progress_callback(f"  ⚠ No valid faces found for student {person_id}")
                continue
            
            for embedding in person_embeddings:
                embeddings_list.append(embedding)
                labels_list.append(person_id)
            
            if progress_callback:
                progress_callback(f"  → Found {len(person_embeddings)} face(s)")
        
        if not embeddings_list:
            msg = "No valid faces found for training"
            log_error(msg)
            if progress_callback:
                progress_callback(f"✗ Error: {msg}")
            raise RuntimeError(msg)
        
        self.embeddings = np.array(embeddings_list)
        self.labels = np.array(labels_list)
        
        unique_students = len(set(labels_list))
        log_info(f"Training complete: {len(self.embeddings)} embeddings from {unique_students} students")
        
        if progress_callback:
            progress_callback("")
            progress_callback(f"✓ Training complete!")
            progress_callback(f"  Total faces: {len(self.embeddings)}")
            progress_callback(f"  Total students: {unique_students}")
        
        return len(self.embeddings), unique_students
    
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
            tuple: (student_id, confidence)
        """
        if not self.has_trained_model():
            return "Unknown", 0.0
        
        similarities = cosine_similarity([embedding], self.embeddings)[0]
        best_idx = np.argmax(similarities)
        best_score = float(similarities[best_idx])
        
        if best_score >= threshold:
            recognized_id = str(self.labels[best_idx])
            log_info(f"Face recognized: ID {recognized_id} (confidence: {best_score:.2f})")
            return recognized_id, best_score
        
        log_debug(f"Unknown face (best match: {best_score:.2f}, threshold: {threshold})")
        return "Unknown", best_score
    
    def predict_face(self, face_image, threshold=CONFIDENCE_THRESHOLD):
        """
        Predict student ID for a face image.
        
        Args:
            face_image: Face image (should be 160x160)
            threshold: Confidence threshold
            
        Returns:
            tuple: (student_id, confidence)
        """
        embedding = self.embedding_gen.generate(face_image)
        
        if embedding is None:
            return "Unknown", 0.0
        
        return self._find_best_match(embedding, threshold)
    
    def predict_from_box(self, image, box, threshold=CONFIDENCE_THRESHOLD):
        """
        Predict student ID from image and bounding box.
        
        Args:
            image: Source image
            box: Bounding box (x1, y1, x2, y2)
            threshold: Confidence threshold
            
        Returns:
            tuple: (student_id, confidence)
        """
        face = self.processor.crop_face(image, box)
        face = self.processor.resize_face(face)
        
        if face is None:
            return "Unknown", 0.0
        
        return self.predict_face(face, threshold)