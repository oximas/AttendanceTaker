"""
Face Detection Module
Handles face detection using MTCNN detector.
"""
import cv2
import numpy as np
from mtcnn import MTCNN
from typing import List, Tuple, Optional


class FaceDetector:
    """Encapsulates face detection functionality using MTCNN."""
    
    def __init__(self):
        """Initialize the MTCNN face detector."""
        self.detector = MTCNN()
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect all faces in an image.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            List of bounding boxes in format [(x1, y1, x2, y2), ...]
        """
        image_rgb = self._convert_to_rgb(image)
        detections = self.detector.detect_faces(image_rgb)
        return self._extract_bounding_boxes(detections)
    
    def detect_largest_face(self, image: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect only the largest face in an image.
        
        Args:
            image: BGR image as numpy array
            
        Returns:
            Bounding box (x1, y1, x2, y2) or None if no face found
        """
        boxes = self.detect_faces(image)
        if not boxes:
            return None
        return self._get_largest_box(boxes)
    
    def extract_face_region(
        self, 
        image: np.ndarray, 
        box: Tuple[int, int, int, int],
        target_size: Optional[Tuple[int, int]] = None
    ) -> Optional[np.ndarray]:
        """
        Extract face region from image using bounding box.
        
        Args:
            image: Source image
            box: Bounding box (x1, y1, x2, y2)
            target_size: Optional (width, height) to resize face to
            
        Returns:
            Cropped face image or None if extraction fails
        """
        x1, y1, x2, y2 = self._clip_box_to_image(box, image.shape)
        
        face = image[y1:y2, x1:x2]
        
        if face.size == 0:
            return None
        
        if target_size:
            face = cv2.resize(face, target_size)
        
        return face
    
    @staticmethod
    def _convert_to_rgb(image: np.ndarray) -> np.ndarray:
        """Convert BGR image to RGB."""
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def _extract_bounding_boxes(detections: List[dict]) -> List[Tuple[int, int, int, int]]:
        """Convert MTCNN detection format to standard bounding boxes."""
        boxes = []
        for detection in detections:
            x, y, w, h = detection['box']
            boxes.append((x, y, x + w, y + h))
        return boxes
    
    @staticmethod
    def _get_largest_box(boxes: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
        """Find the largest bounding box by area."""
        return max(boxes, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]))
    
    @staticmethod
    def _clip_box_to_image(
        box: Tuple[int, int, int, int], 
        image_shape: Tuple[int, ...]
    ) -> Tuple[int, int, int, int]:
        """Ensure bounding box coordinates are within image bounds."""
        height, width = image_shape[:2]
        x1, y1, x2, y2 = box
        
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)
        
        return x1, y1, x2, y2