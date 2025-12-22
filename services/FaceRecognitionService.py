"""
Face Recognition Service - Facade Layer
Provides a simplified interface for face recognition operations.
Hides complexity and coordinates between detection, recognition, and storage.
"""

from services.PeopleCounter import PeopleCounter
from core.FaceRecognizer import FaceRecognizer
from core.FaceImageProcessor import FaceImageProcessor
from config import CONFIDENCE_THRESHOLD

class FaceRecognitionService:
    """
    High-level service for face recognition operations.
    Coordinates multiple components to provide simple API for UI.
    """
    
    def __init__(self, camera_index=0):
        self.counter = PeopleCounter(camera_index)
        self.recognizer = FaceRecognizer()
        self.processor = FaceImageProcessor()
        self._load_existing_model()
    
    def _load_existing_model(self):
        """Try to load existing trained model."""
        try:
            self.recognizer.load_model()
        except Exception:
            pass  # No model exists yet
    
    def capture_and_detect_faces(self):
        """
        Capture image and detect all faces.
        
        Returns:
            dict: {
                'image': original frame,
                'count': number of faces,
                'boxes': bounding boxes,
                'faces': extracted face images
            }
        """
        frame, count, boxes = self.counter.capture_and_detect()
        faces = self.counter.extract_face_images(frame, boxes)
        
        return {
            'image': frame,
            'count': count,
            'boxes': boxes,
            'faces': faces
        }
    
    def recognize_faces(self, image, boxes):
        """
        Recognize all faces in an image.
        
        Args:
            image: Source image
            boxes: Bounding boxes
            
        Returns:
            list: List of (name, confidence) tuples
        """
        if not self.recognizer.has_trained_model():
            return [("Unknown", 0.0) for _ in boxes]
        
        results = []
        for box in boxes:
            name, confidence = self.recognizer.predict_from_box(image, box)
            results.append((name, confidence))
        
        return results
    
    def create_annotated_image(self, image, boxes, show_labels=True):
        """
        Create annotated image with boxes and optional labels.
        
        Args:
            image: Source image
            boxes: Bounding boxes
            show_labels: Whether to add name labels
            
        Returns:
            Annotated image
        """
        if not show_labels:
            return self.processor.draw_bounding_boxes(image, boxes)
        
        # Get predictions
        predictions = self.recognize_faces(image, boxes)
        
        # Create labels with confidence
        labels = []
        for name, confidence in predictions:
            if name == "Unknown":
                labels.append("Unknown")
            else:
                labels.append(f"{name} ({confidence:.2f})")
        
        # Draw boxes
        annotated = self.processor.draw_bounding_boxes(image, boxes)
        
        # Add labels
        annotated = self.processor.add_labels_to_faces(annotated, boxes, labels)
        
        return annotated
    
    def save_faces_with_names(self, faces, names):
        """
        Save multiple faces with their names.
        
        Args:
            faces: List of face images
            names: List of names (same length as faces)
            
        Returns:
            list: List of saved file paths
        """
        saved_paths = []
        for face, name in zip(faces, names):
            if name and name != "Unknown":
                path = self.counter.save_face(face, name)
                saved_paths.append(path)
        
        return saved_paths
    
    def identify_unknown_faces(self, faces):
        """
        Identify which faces are unknown.
        
        Args:
            faces: List of face images
            
        Returns:
            list: List of (index, face_image) for unknown faces
        """
        if not self.recognizer.has_trained_model():
            return list(enumerate(faces))
        
        unknown = []
        for idx, face in enumerate(faces):
            name, _ = self.recognizer.predict_face(face)
            if name == "Unknown":
                unknown.append((idx, face))
        
        return unknown
    
    def train_model(self):
        """
        Train face recognition model on saved faces.
        
        Returns:
            dict: Training results with 'num_faces' and 'num_people'
        """
        num_faces, num_people = self.recognizer.train()
        self.recognizer.save_model()
        
        return {
            'num_faces': num_faces,
            'num_people': num_people
        }
    
    def has_trained_model(self):
        """Check if a trained model exists."""
        return self.recognizer.has_trained_model()
    
    def reload_model(self):
        """Reload the trained model from disk."""
        return self.recognizer.load_model()
    
    def cleanup(self):
        """Release resources."""
        self.counter.cleanup()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()