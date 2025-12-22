import cv2
import numpy as np
from mtcnn import MTCNN
from collections import Counter
import os

# Public directory for storing face data
FACES_DIR = r"C:\D\programming\ML\TinyExpirements\PersonExists\AttendanceTaker\Faces"


class PeopleCounter:
    """Handles people detection using MTCNN face detector."""
    
    def __init__(self, total_frames=1, url=0, face_recognizer=None):
        self.detector = MTCNN()
        self.total_frames = total_frames
        self.url = url
        self.cap = None
        self.face_recognizer = face_recognizer
        
        # Ensure faces directory exists
        os.makedirs(FACES_DIR, exist_ok=True)
    
    def _ensure_camera(self):
        """Initialize camera if not already open."""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.url)
            if not self.cap.isOpened():
                raise RuntimeError("Failed to open camera")
    
    def _cleanup_camera(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def capture_frames(self):
        """Capture multiple frames from camera."""
        try:
            self._ensure_camera()
            frames = []
            
            for i in range(self.total_frames):
                ret, frame = self.cap.read()
                if ret:
                    frames.append(cv2.flip(frame, flipCode=1))
            
            if not frames:
                raise RuntimeError("No frames captured successfully")
            
            return frames
        finally:
            self._cleanup_camera()
    
    def _detect_faces_in_frame(self, frame):
        """Detect faces in a single frame using MTCNN."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.detector.detect_faces(frame_rgb)
        
        boxes = []
        for res in results:
            x, y, w, h = res['box']
            # Convert to (x1, y1, x2, y2) format
            boxes.append((x, y, x + w, y + h))
        
        return len(boxes), boxes
    
    def find_stable_detection(self, frames):
        """Find most consistent face count across frames."""
        detections = [self._detect_faces_in_frame(f) for f in frames]
        counts = [count for count, _ in detections]
        
        # Get most common count
        stable_count = Counter(counts).most_common(1)[0][0]
        
        # Find first frame matching stable count
        for frame, (count, boxes) in zip(frames, detections):
            if count == stable_count:
                return frame.copy(), stable_count, boxes
        
        raise RuntimeError("No stable frame found")
    
    def draw_bounding_boxes(self, image, boxes):
        """Draw rectangles around detected faces."""
        annotated = image.copy()
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        return annotated
    
    def get_person_name(self, person_image):
        """Get person name using face recognizer or return Unknown."""
        if self.face_recognizer is None or not self.face_recognizer.has_trained_model():
            return "Unknown"
        
        name, confidence = self.face_recognizer.predict_face(person_image)
        return name
    
    def get_person_name_from_box(self, image, box):
        """Get person name from image and bounding box."""
        if self.face_recognizer is None or not self.face_recognizer.has_trained_model():
            return "Unknown", 0.0
        
        name, confidence = self.face_recognizer.predict_from_box(image, box)
        return name, confidence
    
    def save_face_encoding(self, person_image, name):
        """Save a face image with the given name."""
        person_dir = os.path.join(FACES_DIR, name)
        os.makedirs(person_dir, exist_ok=True)
        
        # Count existing images for this person
        existing_files = [f for f in os.listdir(person_dir) if f.endswith('.png')]
        next_number = len(existing_files) + 1
        
        # Save the image
        filename = f"{name}_{next_number}.png"
        filepath = os.path.join(person_dir, filename)
        cv2.imwrite(filepath, person_image)
        
        return filepath
    
    def _draw_text_with_background(self, image, text, pos, font_scale=0.8):
        """Draw text with black background for visibility."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        
        x, y = pos
        padding = 5
        
        # Background rectangle
        cv2.rectangle(image,
                     (x - padding, y - text_size[1] - padding),
                     (x + text_size[0] + padding, y + padding),
                     (0, 0, 0), -1)
        
        # Text
        cv2.putText(image, text, (x, y), font, font_scale, (0, 255, 0), thickness)
    
    def label_faces_in_image(self, image, boxes):
        """Add name labels above each detected face."""
        labeled = image.copy()
        height, width = image.shape[:2]
        
        for x1, y1, x2, y2 in boxes:
            # Crop face image
            x1_c, y1_c = max(0, x1), max(0, y1)
            x2_c, y2_c = min(width, x2), min(height, y2)
            person_img = image[y1_c:y2_c, x1_c:x2_c]
            
            if person_img.size == 0:
                continue
            
            # Get name (and confidence if available)
            if self.face_recognizer and self.face_recognizer.has_trained_model():
                name, confidence = self.get_person_name_from_box(image, (x1, y1, x2, y2))
                label = f"{name} ({confidence:.2f})"
            else:
                name = self.get_person_name(person_img)
                label = name
            
            # Position text
            text_y = y1 - 10 if y1 > 40 else y1 + 30
            self._draw_text_with_background(labeled, label, (x1, text_y))
        
        return labeled
    
    def extract_people_images(self, image, boxes):
        """Extract individual cropped images for each face."""
        height, width = image.shape[:2]
        people = []
        
        for x1, y1, x2, y2 in boxes:
            x1_c = max(0, x1)
            y1_c = max(0, y1)
            x2_c = min(width, x2)
            y2_c = min(height, y2)
            
            person_img = image[y1_c:y2_c, x1_c:x2_c].copy()
            if person_img.size > 0:
                people.append(person_img)
        
        return people
    
    def add_names_to_images(self, people_images):
        """Add name overlay to individual face images."""
        labeled = []
        
        for person_img in people_images:
            img_copy = person_img.copy()
            name = self.get_person_name(person_img)
            self._draw_text_with_background(img_copy, name, (5, 25), font_scale=0.6)
            labeled.append(img_copy)
        
        return labeled
    
    def capture_and_count(self):
        """Complete pipeline: capture, detect, and return results."""
        frames = self.capture_frames()
        stable_frame, count, boxes = self.find_stable_detection(frames)
        return stable_frame, count, boxes, None
    
    def __del__(self):
        self._cleanup_camera()


if __name__ == "__main__":
    counter = PeopleCounter()
    
    try:
        stable_image, count, boxes, _ = counter.capture_and_count()
        
        # Label faces in main image
        labeled_image = counter.label_faces_in_image(stable_image, boxes)
        
        # Extract and label individual faces
        people_images = counter.extract_people_images(stable_image, boxes)
        labeled_people = counter.add_names_to_images(people_images)
        
        # Display results
        cv2.putText(stable_image, f"Count: {count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow("Detection", stable_image)
        cv2.imshow("Labeled Faces", labeled_image)
        
        for i, img in enumerate(labeled_people):
            cv2.imshow(f"Person {i+1}", img)
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {e}")