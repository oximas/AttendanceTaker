"""
storage/FaceStorage.py
Handles saving and loading face images from disk.
Uses student ID as folder and file naming convention.
"""

import os
import cv2
from config import FACES_DIR

# Import centralized logger functions
from logger import (
    log_info,
    log_warning,
    log_error,
    log_debug
)


class FaceStorage:
    """Manages face image storage on disk using student IDs."""

    def __init__(self, base_dir=FACES_DIR):
        self.base_dir = base_dir
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            log_info(f"Face storage directory initialized at: {self.base_dir}")
        except Exception as e:
            log_error("Failed to initialize face storage directory", e)
            raise

    def save_face(self, face_image, student_id):
        """
        Save a face image with the given student ID.
        """
        person_dir = os.path.join(self.base_dir, student_id)

        try:
            os.makedirs(person_dir, exist_ok=True)

            existing_files = [
                f for f in os.listdir(person_dir) if f.endswith(".png")
            ]
            next_number = len(existing_files) + 1

            filename = f"{student_id}_{next_number}.png"
            filepath = os.path.join(person_dir, filename)

            success = cv2.imwrite(filepath, face_image)
            if not success:
                raise IOError("cv2.imwrite returned False")

            log_info(
                f"Face image saved | Student ID: {student_id} | File: {filename}"
            )
            return filepath

        except Exception as e:
            log_error(
                f"Failed to save face image for student ID: {student_id}", e
            )
            return None

    def get_person_directory(self, student_id):
        """Get directory path for a student."""
        return os.path.join(self.base_dir, student_id)

    def list_people(self):
        """Get list of all student IDs with saved faces."""
        if not os.path.exists(self.base_dir):
            log_warning("Face storage base directory does not exist")
            return []

        people = [
            d for d in os.listdir(self.base_dir)
            if os.path.isdir(os.path.join(self.base_dir, d))
        ]

        log_debug(f"Found {len(people)} registered students in face storage")
        return people

    def load_person_images(self, student_id):
        """
        Load all face images for a student.
        """
        person_dir = self.get_person_directory(student_id)

        if not os.path.exists(person_dir):
            log_warning(f"No face directory found for student ID: {student_id}")
            return []

        images = []
        for img_name in os.listdir(person_dir):
            if not img_name.lower().endswith((".png", ".jpg", ".jpeg")):
                continue

            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)

            if img is None:
                log_warning(f"Failed to read image file: {img_path}")
                continue

            images.append((img, img_path))

        log_debug(
            f"Loaded {len(images)} images for student ID: {student_id}"
        )
        return images

    def count_faces(self, student_id=None):
        """
        Count total face images.
        """
        if student_id:
            count = len(self.load_person_images(student_id))
            log_debug(
                f"Face count for student ID {student_id}: {count}"
            )
            return count

        total = 0
        for person_id in self.list_people():
            total += len(self.load_person_images(person_id))

        log_debug(f"Total face images stored: {total}")
        return total
