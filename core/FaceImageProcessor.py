"""
core/FaceImageProcessor.py
Fix: Adaptive text sizing based on face size to prevent overlap.
Replace the entire file with this version.
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
    """Processes face images with adaptive text sizing for dense crowds."""
    
    @staticmethod
    def crop_face(image, box):
        """
        Crop face region from image using bounding box.
        
        Args:
            image: Source image
            box: Bounding box - either (x1, y1, x2, y2) or (x, y, w, h)
            
        Returns:
            Cropped face image or None if invalid
        """
        height, width = image.shape[:2]
        
        if len(box) != 4:
            return None
        
        x1, y1, param3, param4 = box
        
        if param3 > x1 and param4 > y1:
            x2 = param3
            y2 = param4
        else:
            x2 = x1 + param3
            y2 = y1 + param4
        
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(width, int(x2))
        y2 = min(height, int(y2))
        
        if x2 <= x1 or y2 <= y1:
            return None
        
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
    def calculate_adaptive_font_scale(box_width, box_height):
        """
        Calculate adaptive font scale based on face size.
        Smaller faces get smaller text to prevent overlap.
        
        Args:
            box_width: Width of bounding box
            box_height: Height of bounding box
            
        Returns:
            tuple: (font_scale, thickness)
        """
        # Calculate face size (use smaller dimension)
        face_size = min(box_width, box_height)
        
        # Adaptive scaling
        if face_size < 50:
            # Tiny faces (lecture hall, far away)
            return 0.3, 1
        elif face_size < 80:
            # Small faces
            return 0.4, 1
        elif face_size < 120:
            # Medium faces
            return 0.5, 1
        elif face_size < 200:
            # Large faces
            return 0.7, 2
        else:
            # Very large faces (close-up)
            return 0.9, 2
    
    @staticmethod
    def draw_text_with_background(image, text, position, 
                                  font_scale=TEXT_FONT_SCALE,
                                  text_color=TEXT_COLOR_BGR,
                                  bg_color=TEXT_BG_COLOR_BGR,
                                  thickness=TEXT_THICKNESS):
        """
        Draw text with background rectangle for visibility.
        
        Args:
            image: Image to draw on (modified in place)
            text: Text to draw
            position: (x, y) position
            font_scale: Text scale
            text_color: Text color in BGR
            bg_color: Background color in BGR
            thickness: Text thickness
        """
        font = TEXT_FONT
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        
        x, y = position
        padding = max(2, int(TEXT_PADDING * font_scale))  # Adaptive padding
        
        # Background rectangle
        cv2.rectangle(image,
                     (x - padding, y - text_size[1] - padding),
                     (x + text_size[0] + padding, y + padding),
                     bg_color, -1)
        
        # Text
        cv2.putText(image, text, (x, y), font, font_scale, text_color, thickness)
    
    @staticmethod
    def truncate_name(name, max_length=15):
        """
        Truncate long names to prevent overflow.
        
        Args:
            name: Full name
            max_length: Maximum characters
            
        Returns:
            Truncated name with ellipsis if needed
        """
        if len(name) <= max_length:
            return name
        return name[:max_length-2] + ".."
    
    @staticmethod
    def add_labels_to_faces(image, boxes, labels):
        """
        Add text labels above detected faces with adaptive sizing.
        Prevents overlap by using smaller text for smaller faces.
        
        Args:
            image: Image to annotate
            boxes: List of bounding boxes in (x1, y1, x2, y2) format
            labels: List of label strings (same length as boxes)
            
        Returns:
            Labeled image
        """
        labeled = image.copy()
        
        for (x1, y1, x2, y2), label in zip(boxes, labels):
            # Calculate box dimensions
            box_width = x2 - x1
            box_height = y2 - y1
            
            # Get adaptive font scale based on face size
            font_scale, thickness = FaceImageProcessor.calculate_adaptive_font_scale(
                box_width, box_height
            )
            
            # Truncate long names for small faces
            if box_width < 100:
                label = FaceImageProcessor.truncate_name(label, max_length=12)
            elif box_width < 150:
                label = FaceImageProcessor.truncate_name(label, max_length=20)
            
            # Calculate text position
            # For small faces, put text inside top of box
            # For larger faces, put text above box
            if box_height < 60:
                # Small face - text inside at top
                text_y = int(y1 + 15 * font_scale)
            else:
                # Larger face - text above box
                text_y = int(y1 - 5)
            
            # Ensure text stays within image bounds
            text_y = max(15, text_y)
            
            FaceImageProcessor.draw_text_with_background(
                labeled, 
                label, 
                (int(x1), text_y),
                font_scale=font_scale,
                thickness=thickness
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