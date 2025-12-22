"""
Face Embedding Module
Generates face embeddings using FaceNet model.
"""
import cv2
import numpy as np
from keras_facenet import FaceNet
from typing import Optional, List


class FaceEmbedder:
    """Generates embeddings for face images using FaceNet."""
    
    EMBEDDING_SIZE = 512  # FaceNet output dimension
    FACENET_INPUT_SIZE = (160, 160)
    
    def __init__(self):
        """Initialize FaceNet model."""
        self.model = FaceNet()
    
    def generate_embedding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate embedding for a single face image.
        
        Args:
            face_image: Face image as numpy array
            
        Returns:
            Embedding vector or None if generation fails
        """
        if face_image is None or face_image.size == 0:
            return None
        
        try:
            preprocessed_face = self._preprocess_face(face_image)
            embedding = self.model.embeddings([preprocessed_face])[0]
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(
        self, 
        face_images: List[np.ndarray]
    ) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple face images.
        
        Args:
            face_images: List of face images
            
        Returns:
            List of embedding vectors (None for failed generations)
        """
        embeddings = []
        
        for face in face_images:
            embedding = self.generate_embedding(face)
            embeddings.append(embedding)
        
        return embeddings
    
    def _preprocess_face(self, face_image: np.ndarray) -> np.ndarray:
        """
        Preprocess face image for FaceNet input.
        
        Args:
            face_image: Raw face image
            
        Returns:
            Preprocessed face image
        """
        # Resize to FaceNet input size
        if face_image.shape[:2] != self.FACENET_INPUT_SIZE:
            face_image = cv2.resize(face_image, self.FACENET_INPUT_SIZE)
        
        return face_image


class EmbeddingMatcher:
    """Matches face embeddings using cosine similarity."""
    
    @staticmethod
    def calculate_similarity(
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        similarity = cosine_similarity([embedding1], [embedding2])[0][0]
        return float(similarity)
    
    @staticmethod
    def find_best_match(
        query_embedding: np.ndarray,
        reference_embeddings: np.ndarray,
        threshold: float = 0.5
    ) -> tuple:
        """
        Find best matching embedding from reference set.
        
        Args:
            query_embedding: Embedding to match
            reference_embeddings: Array of reference embeddings
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (best_index, similarity_score)
            Returns (-1, 0.0) if no match above threshold
        """
        from sklearn.metrics.pairwise import cosine_similarity
        
        if len(reference_embeddings) == 0:
            return -1, 0.0
        
        similarities = cosine_similarity([query_embedding], reference_embeddings)[0]
        best_index = int(np.argmax(similarities))
        best_score = float(similarities[best_index])
        
        if best_score >= threshold:
            return best_index, best_score
        else:
            return -1, best_score