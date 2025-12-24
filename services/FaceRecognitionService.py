"""
services/FaceRecognitionService.py
Provides a simplified interface for face recognition operations.
Hides complexity and coordinates between detection, recognition, storage, and attendance.
"""

from services.PeopleCounter import PeopleCounter
from core.FaceRecognizer import FaceRecognizer
from core.FaceImageProcessor import FaceImageProcessor
from services.StudentDatabase import StudentDatabase
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
        self.student_db = StudentDatabase()
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
        Returns student IDs and their names.
        
        Args:
            image: Source image
            boxes: Bounding boxes
            
        Returns:
            list: List of (student_id, student_name, confidence) tuples
        """
        if not self.recognizer.has_trained_model():
            return [("Unknown", "Unknown", 0.0) for _ in boxes]
        
        results = []
        for box in boxes:
            student_id, confidence = self.recognizer.predict_from_box(image, box)
            
            # Look up student name from database
            if student_id != "Unknown":
                student_name = self.student_db.get_student_name(student_id)
                if not student_name:
                    student_name = "Unknown"
            else:
                student_name = "Unknown"
            
            results.append((student_id, student_name, confidence))
        
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
        
        # Create labels with student name and confidence
        labels = []
        for student_id, student_name, confidence in predictions:
            if student_id == "Unknown":
                labels.append("Unknown")
            else:
                labels.append(f"{student_name} ({confidence:.2f})")
        
        # Draw boxes
        annotated = self.processor.draw_bounding_boxes(image, boxes)
        
        # Add labels
        annotated = self.processor.add_labels_to_faces(annotated, boxes, labels)
        
        return annotated
    
    def save_faces_with_ids(self, faces, student_ids):
        """
        Save multiple faces with their student IDs.
        
        Args:
            faces: List of face images
            student_ids: List of student IDs (same length as faces)
            
        Returns:
            list: List of saved file paths
        """
        saved_paths = []
        for face, student_id in zip(faces, student_ids):
            if student_id and student_id != "Unknown":
                path = self.counter.save_face(face, student_id)
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
            student_id, _ = self.recognizer.predict_face(face)
            if student_id == "Unknown":
                unknown.append((idx, face))
        
        return unknown
    
    def train_model(self):
        """
        Train face recognition model on saved faces.
        
        Returns:
            dict: Training results with 'num_faces' and 'num_students'
        """
        num_faces, num_students = self.recognizer.train()
        self.recognizer.save_model()
        
        return {
            'num_faces': num_faces,
            'num_students': num_students
        }
    
    def has_trained_model(self):
        """Check if a trained model exists."""
        return self.recognizer.has_trained_model()
    
    def reload_model(self):
        """Reload the trained model from disk."""
        return self.recognizer.load_model()
    
    def take_attendance(self, detected_student_ids, date_str):
        """
        Mark attendance for detected students on a specific date.
        
        Args:
            detected_student_ids: List of student IDs detected in image
            date_str: Date string (YYYY-MM-DD)
            
        Returns:
            dict: {'marked': count, 'not_found': [ids], 'date': date_str}
        """
        # Remove duplicates while preserving order
        unique_ids = []
        seen = set()
        for student_id in detected_student_ids:
            if student_id != "Unknown" and student_id not in seen:
                unique_ids.append(student_id)
                seen.add(student_id)
        
        # Mark attendance in database
        result = self.student_db.mark_multiple_attendance(unique_ids, date_str)
        result['date'] = date_str
        
        return result
    
    def cleanup(self):
        """Release resources."""
        self.counter.cleanup()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()