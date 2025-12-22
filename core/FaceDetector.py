"""
Face detection module using MTCNN.
Handles face detection in images.
"""

import cv2
from mtcnn import MTCNN
from collections import Counter


class FaceDetector:
    """Detects faces in images using MTCNN."""
    
    def __init__(self):
        self.detector = MTCNN()
    
    def detect(self, image):
        """
        Detect faces in an image.
        
        Args:
            image: BGR image (numpy array)
            
        Returns:
            tuple: (face_count, bounding_boxes)
                   bounding_boxes format: list of (x1, y1, x2, y2) tuples
        """
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.detector.detect_faces(image_rgb)
        
        boxes = []
        for res in results:
            x, y, w, h = res['box']
            # Convert to (x1, y1, x2, y2) format
            boxes.append((x, y, x + w, y + h))
        
        return len(boxes), boxes
    
    def find_stable_detection(self, frames):
        """
        Find the most consistent face count across multiple frames.
        
        Args:
            frames: List of images
            
        Returns:
            tuple: (best_frame, face_count, bounding_boxes)
        """
        detections = [self.detect(frame) for frame in frames]
        counts = [count for count, _ in detections]
        
        # Get most common count
        stable_count = Counter(counts).most_common(1)[0][0]
        
        # Find first frame matching stable count
        for frame, (count, boxes) in zip(frames, detections):
            if count == stable_count:
                return frame.copy(), stable_count, boxes
        
        raise RuntimeError("No stable detection found")
    
    def get_largest_face(self, image):
        """
        Detect and return the largest face in an image.
        
        Args:
            image: BGR or RGB image
            
        Returns:
            dict: Face detection result with 'box' key, or None if no face found
        """
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
        results = self.detector.detect_faces(image_rgb)
        
        if not results:
            return None
        
        # Return largest face by area
        largest = max(results, key=lambda r: r['box'][2] * r['box'][3])
        return largest