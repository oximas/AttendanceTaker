"""
People counter module (refactored).
Lightweight coordinator that uses separate components for each responsibility.
"""

from core.CameraManager import CameraManager
from core.FaceDetector import FaceDetector
from core.FaceImageProcessor import FaceImageProcessor
from storage.FaceStorage import FaceStorage
from config import CAPTURE_FRAME_COUNT


class PeopleCounter:
    """
    Coordinates face detection workflow.
    Uses composition to delegate responsibilities to specialized components.
    """
    
    def __init__(self, camera_index=0, frame_count=CAPTURE_FRAME_COUNT):
        self.camera = CameraManager(camera_index)
        self.detector = FaceDetector()
        self.processor = FaceImageProcessor()
        self.storage = FaceStorage()
        self.frame_count = frame_count
    
    def capture_and_detect(self):
        """
        Complete detection pipeline: capture frames and detect faces.
        
        Returns:
            tuple: (stable_frame, face_count, bounding_boxes)
        """
        # Capture frames
        frames = self.camera.capture_frames(self.frame_count)
        
        # Find stable detection
        stable_frame, count, boxes = self.detector.find_stable_detection(frames)
        
        return stable_frame, count, boxes
    
    def extract_face_images(self, image, boxes):
        """
        Extract individual face images from detected boxes.
        
        Args:
            image: Source image
            boxes: Bounding boxes
            
        Returns:
            list: List of cropped face images
        """
        return self.processor.extract_faces(image, boxes)
    
    def annotate_image(self, image, boxes, labels=None):
        """
        Draw bounding boxes and optional labels on image.
        
        Args:
            image: Image to annotate
            boxes: Bounding boxes
            labels: Optional list of labels (same length as boxes)
            
        Returns:
            Annotated image
        """
        annotated = self.processor.draw_bounding_boxes(image, boxes)
        
        if labels:
            annotated = self.processor.add_labels_to_faces(annotated, boxes, labels)
        
        return annotated
    
    def save_face(self, face_image, person_name):
        """
        Save a face image with a person name.
        
        Args:
            face_image: Face image to save
            person_name: Name of the person
            
        Returns:
            str: Path to saved file
        """
        return self.storage.save_face(face_image, person_name)
    
    def cleanup(self):
        """Release camera resources."""
        self.camera.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()


if __name__ == "__main__":
    # Example usage
    counter = PeopleCounter()
    
    try:
        # Capture and detect
        frame, count, boxes = counter.capture_and_detect()
        print(f"Detected {count} people")
        
        # Annotate image
        annotated = counter.annotate_image(frame, boxes)
        
        # Extract faces
        faces = counter.extract_face_images(frame, boxes)
        print(f"Extracted {len(faces)} face images")
        
        # Display (requires cv2)
        import cv2
        cv2.imshow("Detection", annotated)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        counter.cleanup()