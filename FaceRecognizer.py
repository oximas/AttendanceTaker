import os
import cv2
import numpy as np
from mtcnn import MTCNN
from keras_facenet import FaceNet
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# Public directories
MODELS_DIR = r"C:\D\programming\ML\TinyExpirements\PersonExists\AttendanceTaker\Models"
CONFIDENCE_THRESHOLD = 0.5


class FaceRecognizer:
    """Handles face recognition using MTCNN and FaceNet."""
    
    def __init__(self):
        self.detector = MTCNN()
        self.embedder = FaceNet()
        self.embeddings = None
        self.labels = None
        
        # Ensure models directory exists
        os.makedirs(MODELS_DIR, exist_ok=True)
    
    def _extract_face_from_box(self, image, box):
        """Extract and resize face from bounding box."""
        x, y, w, h = box
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = x1 + w, y1 + h
        face = image[y1:y2, x1:x2]
        
        if face.size == 0:
            return None
        
        face = cv2.resize(face, (160, 160))
        return face
    
    def _get_face_embedding(self, face_image):
        """Generate embedding for a face image."""
        if face_image is None:
            return None
        
        embedding = self.embedder.embeddings([face_image])[0]
        return embedding
    
    def _load_person_faces(self, person_dir, person_name):
        """Load all face images for a person and extract embeddings."""
        person_embeddings = []
        
        for img_name in os.listdir(person_dir):
            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)
            
            if img is None:
                continue
            
            # Detect faces using MTCNN
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.detector.detect_faces(img_rgb)
            
            if len(results) == 0:
                continue
            
            # Take biggest face
            face_data = max(results, key=lambda r: r['box'][2] * r['box'][3])
            face = self._extract_face_from_box(img, face_data['box'])
            
            if face is None:
                continue
            
            # Get embedding
            embedding = self._get_face_embedding(face)
            if embedding is not None:
                person_embeddings.append(embedding)
        
        return person_embeddings
    
    def train_from_directory(self, faces_dir):
        """Train face recognition model from directory of labeled faces."""
        embeddings_list = []
        labels_list = []
        
        if not os.path.exists(faces_dir):
            raise RuntimeError(f"Directory {faces_dir} does not exist")
        
        person_folders = [d for d in os.listdir(faces_dir) 
                         if os.path.isdir(os.path.join(faces_dir, d))]
        
        if len(person_folders) == 0:
            raise RuntimeError(f"No person folders found in {faces_dir}")
        
        print(f"\n=== Training on {len(person_folders)} people ===")
        
        for person_name in tqdm(person_folders, desc="Processing people"):
            person_dir = os.path.join(faces_dir, person_name)
            person_embeddings = self._load_person_faces(person_dir, person_name)
            
            # Add all embeddings for this person
            for embedding in person_embeddings:
                embeddings_list.append(embedding)
                labels_list.append(person_name)
        
        if len(embeddings_list) == 0:
            raise RuntimeError("No faces found for training")
        
        # Store as numpy arrays
        self.embeddings = np.array(embeddings_list)
        self.labels = np.array(labels_list)
        
        print(f"Training complete: {len(self.embeddings)} face embeddings from {len(person_folders)} people")
        return len(self.embeddings), len(person_folders)
    
    def save_model(self, filename="face_model"):
        """Save trained embeddings and labels to disk."""
        if self.embeddings is None or self.labels is None:
            raise RuntimeError("No trained model to save. Train first.")
        
        embeddings_path = os.path.join(MODELS_DIR, f"{filename}_embeddings.npy")
        labels_path = os.path.join(MODELS_DIR, f"{filename}_labels.npy")
        
        np.save(embeddings_path, self.embeddings)
        np.save(labels_path, self.labels)
        
        print(f"Model saved to {MODELS_DIR}/")
        return embeddings_path, labels_path
    
    def load_model(self, filename="face_model"):
        """Load trained embeddings and labels from disk."""
        embeddings_path = os.path.join(MODELS_DIR, f"{filename}_embeddings.npy")
        labels_path = os.path.join(MODELS_DIR, f"{filename}_labels.npy")
        
        if not os.path.exists(embeddings_path) or not os.path.exists(labels_path):
            return False
        
        self.embeddings = np.load(embeddings_path)
        self.labels = np.load(labels_path)
        
        print(f"Model loaded: {len(self.embeddings)} embeddings")
        return True
    
    def has_trained_model(self):
        """Check if model is trained or loaded."""
        return self.embeddings is not None and self.labels is not None
    
    def _find_best_match(self, embedding, threshold=CONFIDENCE_THRESHOLD):
        """Find best matching person for an embedding."""
        if not self.has_trained_model():
            return "Unknown", 0.0
        
        similarities = cosine_similarity([embedding], self.embeddings)[0]
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score >= threshold:
            return self.labels[best_idx], best_score
        else:
            return "Unknown", best_score
    
    def predict_face(self, face_image, threshold=CONFIDENCE_THRESHOLD):
        """Predict name for a single face image."""
        embedding = self._get_face_embedding(face_image)
        
        if embedding is None:
            return "Unknown", 0.0
        
        name, confidence = self._find_best_match(embedding, threshold)
        return name, confidence
    
    def predict_from_box(self, image, box, threshold=CONFIDENCE_THRESHOLD):
        """Predict name from image and bounding box coordinates."""
        # Convert YOLO-style box (x1, y1, x2, y2) to MTCNN-style (x, y, w, h)
        x1, y1, x2, y2 = box
        mtcnn_box = (x1, y1, x2 - x1, y2 - y1)
        
        face = self._extract_face_from_box(image, mtcnn_box)
        
        if face is None:
            return "Unknown", 0.0
        
        return self.predict_face(face, threshold)


if __name__ == "__main__":
    # Example usage
    recognizer = FaceRecognizer()
    
    # Train on faces directory
    try:
        num_faces, num_people = recognizer.train_from_directory("Faces")
        recognizer.save_model()
        print(f"\nTrained on {num_faces} faces from {num_people} people")
        
        # Test prediction
        test_img_path = "test_image.jpg"
        if os.path.exists(test_img_path):
            test_img = cv2.imread(test_img_path)
            test_img_rgb = cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB)
            results = recognizer.detector.detect_faces(test_img_rgb)
            
            for res in results:
                face = recognizer._extract_face_from_box(test_img, res['box'])
                name, score = recognizer.predict_face(face)
                print(f"Detected: {name} (confidence: {score:.2f})")
    
    except Exception as e:
        print(f"Error: {e}")