"""
People Counter Module
Orchestrates face detection, camera capture, and visualization.
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional

from CameraService import CameraService, FrameStabilizer
from FaceDetector import FaceDetector
from FaceStorage import FaceStorage
from FaceRecognizer import FaceRecognizer


# Public directory for storing face data
FACES_DIR = r"C:\D\programming\ML\TinyExpirements\PersonExists\AttendanceTaker\Faces"


class ImageAnnotator:
    """Handles drawing annotations on images."""
    
    @staticmethod
    def draw_bounding_boxes(
        image: np.ndarray,
        boxes: List[Tuple[int, int, int, int]],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw bounding boxes on image.
        
        Args:
            image: Image to annotate
            boxes: List of bounding boxes (x1, y1, x2, y2)
            color: Box color in BGR
            thickness: Line thickness
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
        
        return annotated
    
    @staticmethod
    def draw_text_with_background(
        image: np.ndarray,
        text: str,
        position: Tuple[int, int],
        font_scale: float = 0.8,
        font_color: Tuple[int, int, int] = (0, 255, 0),
        bg_color: Tuple[int, int, int] = (0, 0, 0),
        thickness: int = 2,
        padding: int = 5
    ) -> np.ndarray:
        """
        Draw text with background rectangle for visibility.
        
        Args:
            image: Image to annotate
            text: Text to draw
            position: (x, y) position for text
            font_scale: Font size scale
            font_color: Text color in BGR
            bg_color: Background color in BGR
            thickness: Text thickness
            padding: Padding around text
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Calculate text size
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        x, y = position
        
        # Draw background rectangle
        cv2.rectangle(
            annotated,
            (x - padding, y - text_size[1] - padding),
            (x + text_size[0] + padding, y + padding),
            bg_color,
            -1
        )
        
        # Draw text
        cv2.putText(annotated, text, (x, y), font, font_scale, font_color, thickness)
        
        return annotated


class FaceLabeler:
    """Handles labeling faces with names."""
    
    def __init__(self, recognizer: Optional[FaceRecognizer] = None):
        """
        Initialize face labeler.
        
        Args:
            recognizer: Face recognizer for getting names
        """
        self.recognizer = recognizer
        self.annotator = ImageAnnotator()
    
    def label_faces_in_image(
        self,
        image: np.ndarray,
        boxes: List[Tuple[int, int, int, int]]
    ) -> np.ndarray:
        """
        Add name labels to faces in image.
        
        Args:
            image: Image with detected faces
            boxes: List of face bounding boxes
            
        Returns:
            Image with name labels
        """
        labeled_image = image.copy()
        
        for box in boxes:
            name, confidence = self._get_face_identity(image, box)
            label_text = self._format_label(name, confidence)
            label_position = self._calculate_label_position(box)
            
            labeled_image = self.annotator.draw_text_with_background(
                labeled_image,
                label_text,
                label_position
            )
        
        return labeled_image
    
    def label_individual_face_image(
        self,
        face_image: np.ndarray
    ) -> np.ndarray:
        """
        Add name label to individual face image.
        
        Args:
            face_image: Cropped face image
            
        Returns:
            Face image with name label
        """
        name = self._get_name_for_face_image(face_image)
        
        return self.annotator.draw_text_with_background(
            face_image,
            name,
            (5, 25),
            font_scale=0.6
        )
    
    def _get_face_identity(
        self,
        image: np.ndarray,
        box: Tuple[int, int, int, int]
    ) -> Tuple[str, float]:
        """Get identity for a face in an image."""
        if self.recognizer and self.recognizer.has_trained_model():
            return self.recognizer.recognize_from_bounding_box(image, box)
        return "Unknown", 0.0
    
    def _get_name_for_face_image(self, face_image: np.ndarray) -> str:
        """Get name for a face image."""
        if self.recognizer and self.recognizer.has_trained_model():
            name, _ = self.recognizer.recognize_face(face_image)
            return name
        return "Unknown"
    
    @staticmethod
    def _format_label(name: str, confidence: float) -> str:
        """Format label text with name and confidence."""
        if confidence > 0:
            return f"{name} ({confidence:.2f})"
        return name
    
    @staticmethod
    def _calculate_label_position(box: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """Calculate appropriate position for label above box."""
        x1, y1, x2, y2 = box
        text_y = y1 - 10 if y1 > 40 else y1 + 30
        return (x1, text_y)


class FaceExtractor:
    """Extracts individual face images from full images."""
    
    def __init__(self, detector: FaceDetector):
        """
        Initialize face extractor.
        
        Args:
            detector: Face detector instance
        """
        self.detector = detector
    
    def extract_faces_from_boxes(
        self,
        image: np.ndarray,
        boxes: List[Tuple[int, int, int, int]]
    ) -> List[np.ndarray]:
        """
        Extract individual face images from an image.
        
        Args:
            image: Full image
            boxes: List of face bounding boxes
            
        Returns:
            List of cropped face images
        """
        faces = []
        
        for box in boxes:
            face = self.detector.extract_face_region(image, box)
            if face is not None and face.size > 0:
                faces.append(face)
        
        return faces


class PeopleCounter:
    """
    Main class for people detection and counting.
    Orchestrates camera, detection, recognition, and storage.
    """
    
    def __init__(
        self,
        camera_index: int = 0,
        num_capture_frames: int = 1,
        face_recognizer: Optional[FaceRecognizer] = None,
    ):
        """
        Initialize people counter.
        
        Args:
            camera_index: Camera device index
            num_capture_frames: Number of frames to capture for stability
            face_recognizer: Optional face recognizer for identification
        """
        self.camera = CameraService(camera_index)
        self.detector = FaceDetector()
        self.storage = FaceStorage(FACES_DIR)
        self.face_recognizer = face_recognizer
        self.num_capture_frames = num_capture_frames
        
        # Helper components
        self.annotator = ImageAnnotator()
        self.labeler = FaceLabeler(face_recognizer)
        self.extractor = FaceExtractor(self.detector)
        self.stabilizer = FrameStabilizer()
    
    def capture_and_count(self) -> Tuple[np.ndarray, int, List[Tuple[int, int, int, int]], None]:
        """
        Capture image and count people.
        
        Returns:
            Tuple of (image, count, boxes, None)
        """
        # Capture frames
        frames = self.camera.capture_multiple_frames(self.num_capture_frames)
        
        # Find stable detection
        stable_frame, count, boxes = self.stabilizer.find_most_consistent_detection(
            frames,
            self._detect_faces_wrapper
        )
        
        return stable_frame, count, boxes, None
    
    def draw_bounding_boxes(
        self,
        image: np.ndarray,
        boxes: List[Tuple[int, int, int, int]]
    ) -> np.ndarray:
        """Draw bounding boxes around detected faces."""
        return self.annotator.draw_bounding_boxes(image, boxes)
    
    def label_faces_in_image(
        self,
        image: np.ndarray,
        boxes: List[Tuple[int, int, int, int]]
    ) -> np.ndarray:
        """Add name labels to faces in image."""
        return self.labeler.label_faces_in_image(image, boxes)
    
    def extract_people_images(
        self,
        image: np.ndarray,
        boxes: List[Tuple[int, int, int, int]]
    ) -> List[np.ndarray]:
        """Extract individual face images."""
        return self.extractor.extract_faces_from_boxes(image, boxes)
    
    def add_names_to_images(
        self,
        face_images: List[np.ndarray]
    ) -> List[np.ndarray]:
        """Add name labels to individual face images."""
        return [
            self.labeler.label_individual_face_image(face)
            for face in face_images
        ]
    
    def save_face_encoding(
        self,
        face_image: np.ndarray,
        person_name: str
    ) -> str:
        """
        Save a face image with person's name.
        
        Args:
            face_image: Face image to save
            person_name: Name of the person
            
        Returns:
            Path where face was saved
        """
        return self.storage.save_face(face_image, person_name)
    
    def get_person_name(self, face_image: np.ndarray) -> str:
        """
        Get person's name from face image.
        
        Args:
            face_image: Face image
            
        Returns:
            Person's name or "Unknown"
        """
        if self.face_recognizer and self.face_recognizer.has_trained_model():
            name, _ = self.face_recognizer.recognize_face(face_image)
            return name
        return "Unknown"
    
    def _detect_faces_wrapper(self, frame: np.ndarray) -> Tuple[int, List]:
        """Wrapper for face detection to match stabilizer interface."""
        boxes = self.detector.detect_faces(frame)
        return len(boxes), boxes
    
    def __del__(self):
        """Cleanup resources."""
        self.camera.release()


# Backward compatibility - maintain old function signature
def url_parameter_exists():
    """Legacy compatibility function."""
    pass


if __name__ == "__main__":
    counter = PeopleCounter()
    
    try:
        stable_image, count, boxes, _ = counter.capture_and_count()
        
        # Draw boxes and labels
        boxed_image = counter.draw_bounding_boxes(stable_image, boxes)
        labeled_image = counter.label_faces_in_image(boxed_image, boxes)
        
        # Extract individual faces
        face_images = counter.extract_people_images(stable_image, boxes)
        labeled_faces = counter.add_names_to_images(face_images)
        
        # Display results
        cv2.putText(
            labeled_image,
            f"Count: {count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        
        cv2.imshow("Detection", labeled_image)
        
        for i, face in enumerate(labeled_faces):
            cv2.imshow(f"Person {i+1}", face)
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {e}")