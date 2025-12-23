"""
FaceImageProcessor.py
Face image processing module.
Handles cropping, resizing, and visual annotations for face images.
"""

import cv2
import numpy as np
from config import (
    FACE_IMAGE_SIZE, BBOX_COLOR_BGR, BBOX_THICKNESS,
    TEXT_FONT, TEXT_FONT_SCALE, TEXT_FONT_SCALE_SMALL,
    TEXT_THICKNESS, TEXT_BG_COLOR_BGR, TEXT_COLOR_BGR,
    TEXT_PADDING, TEXT_Y_OFFSET, TEXT_Y_FALLBACK
)


class FaceImageProcessor:
    """Processes face images: cropping, resizing, and annotations."""
    
    @staticmethod
    def crop_face(image, box):
        """
        Crop face region from image using bounding box.
        
        Args:
            image: Source image
            box: Bounding box - either (x1, y1, x2, y2) or (x, y, w, h) from MTCNN dict
            
        Returns:
            Cropped face image or None if invalid
        """
        height, width = image.shape[:2]
        
        if len(box) != 4:
            return None
        
        x1, y1, param3, param4 = box
        
        # If param3 and param4 are greater than x1 and y1, it's (x1, y1, x2, y2)
        # Otherwise it's (x, y, w, h)
        if param3 > x1 and param4 > y1:
            # (x1, y1, x2, y2) format
            x2 = param3
            y2 = param4
        else:
            # (x, y, w, h) format - convert to (x1, y1, x2, y2)
            x2 = x1 + param3
            y2 = y1 + param4
        
        # Clamp to image boundaries
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(width, int(x2))
        y2 = min(height, int(y2))
        
        # Ensure valid coordinates
        if x2 <= x1 or y2 <= y1:
            return None
        
        # Crop using [y1:y2, x1:x2] - THIS IS THE KEY FIX
        face = image[y1:y2, x1:x2]
        return face if face.size > 0 else None
    
    @staticmethod
    def resize_face(face, target_size=FACE_IMAGE_SIZE):
        """
        Resize face to target dimensions.
        
        Args:
            face: Face image
            target_size: Target (width, height)
            
        Returns:
            Resized face image
        """
        if face is None or face.size == 0:
            return None
        return cv2.resize(face, target_size)
    
    @staticmethod
    def extract_faces(image, boxes):
        """
        Extract multiple face images from an image.
        
        Args:
            image: Source image
            boxes: List of bounding boxes in (x1, y1, x2, y2) format
            
        Returns:
            List of cropped face images
        """
        faces = []
        for box in boxes:
            face = FaceImageProcessor.crop_face(image, box)
            if face is not None:
                faces.append(face)
        return faces
    
    @staticmethod
    def draw_bounding_boxes(image, boxes, color=BBOX_COLOR_BGR, thickness=BBOX_THICKNESS):
        """
        Draw rectangles around faces.
        
        Args:
            image: Image to draw on
            boxes: List of bounding boxes in (x1, y1, x2, y2) format
            color: Box color in BGR
            thickness: Line thickness
            
        Returns:
            Annotated image
        """
        annotated = image.copy()
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
        return annotated
    
    @staticmethod
    def draw_text_with_background(image, text, position, 
                                  font_scale=TEXT_FONT_SCALE,
                                  text_color=TEXT_COLOR_BGR,
                                  bg_color=TEXT_BG_COLOR_BGR):
        """
        Draw text with background rectangle for visibility.
        
        Args:
            image: Image to draw on (modified in place)
            text: Text to draw
            position: (x, y) position
            font_scale: Text scale
            text_color: Text color in BGR
            bg_color: Background color in BGR
        """
        font = TEXT_FONT
        thickness = TEXT_THICKNESS
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        
        x, y = position
        padding = TEXT_PADDING
        
        # Background rectangle
        cv2.rectangle(image,
                     (x - padding, y - text_size[1] - padding),
                     (x + text_size[0] + padding, y + padding),
                     bg_color, -1)
        
        # Text
        cv2.putText(image, text, (x, y), font, font_scale, text_color, thickness)
    
    @staticmethod
    def add_labels_to_faces(image, boxes, labels):
        """
        Add text labels above detected faces.
        
        Args:
            image: Image to annotate
            boxes: List of bounding boxes in (x1, y1, x2, y2) format
            labels: List of label strings (same length as boxes)
            
        Returns:
            Labeled image
        """
        labeled = image.copy()
        
        for (x1, y1, x2, y2), label in zip(boxes, labels):
            # Position text above box
            text_y = y1 - TEXT_Y_OFFSET if y1 > 40 else y1 + TEXT_Y_FALLBACK
            FaceImageProcessor.draw_text_with_background(
                labeled, label, (int(x1), int(text_y))
            )
        
        return labeled
    
    @staticmethod
    def add_label_to_face_image(face_image, label, font_scale=TEXT_FONT_SCALE_SMALL):
        """
        Add label overlay to a face image.
        
        Args:
            face_image: Face image
            label: Label text
            font_scale: Text scale
            
        Returns:
            Labeled face image
        """
        labeled = face_image.copy()
        FaceImageProcessor.draw_text_with_background(
            labeled, label, (5, 25), font_scale=font_scale
        )
        return labeled