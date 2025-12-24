"""
services/ModelManager.py
Manages model training state and tracks which students the model was trained on.
Automatically determines when retraining is needed.
"""

import os
from config import MODELS_DIR, FACES_DIR


class ModelManager:
    """
    Tracks trained students and determines when retraining is needed.
    """
    
    def __init__(self, models_dir=MODELS_DIR, faces_dir=FACES_DIR):
        self.models_dir = models_dir
        self.faces_dir = faces_dir
        self.trained_students_file = os.path.join(models_dir, "trained_students.txt")
        
        os.makedirs(models_dir, exist_ok=True)
    
    def get_current_student_ids(self):
        """
        Get list of student IDs that currently have faces in the Faces folder.
        
        Returns:
            set: Set of student IDs
        """
        if not os.path.exists(self.faces_dir):
            return set()
        
        student_ids = set()
        for item in os.listdir(self.faces_dir):
            folder_path = os.path.join(self.faces_dir, item)
            if os.path.isdir(folder_path):
                student_ids.add(item)
        
        return student_ids
    
    def get_trained_student_ids(self):
        """
        Get list of student IDs the model was trained on.
        
        Returns:
            set: Set of student IDs from last training
        """
        if not os.path.exists(self.trained_students_file):
            return set()
        
        with open(self.trained_students_file, 'r') as f:
            student_ids = {line.strip() for line in f if line.strip()}
        
        return student_ids
    
    def save_trained_student_ids(self, student_ids):
        """
        Save the list of student IDs that were used for training.
        
        Args:
            student_ids: Set or list of student IDs
        """
        with open(self.trained_students_file, 'w') as f:
            for student_id in sorted(student_ids):
                f.write(f"{student_id}\n")
    
    def needs_retraining(self):
        """
        Check if model needs retraining based on changes in Faces folder.
        
        Returns:
            tuple: (needs_training: bool, reason: str, new_students: set, removed_students: set)
        """
        current_ids = self.get_current_student_ids()
        trained_ids = self.get_trained_student_ids()
        
        # No students at all
        if not current_ids:
            return False, "No students in Faces folder", set(), set()
        
        # Never trained before
        if not trained_ids:
            return True, "Model never trained", current_ids, set()
        
        # Check for differences
        new_students = current_ids - trained_ids
        removed_students = trained_ids - current_ids
        
        if new_students:
            return True, f"New students added: {len(new_students)}", new_students, removed_students
        
        if removed_students:
            return True, f"Students removed: {len(removed_students)}", new_students, removed_students
        
        return False, "Model up to date", set(), set()
    
    def update_after_training(self):
        """
        Update trained students list after successful training.
        Call this after model training completes.
        """
        current_ids = self.get_current_student_ids()
        self.save_trained_student_ids(current_ids)
    
    def get_training_stats(self):
        """
        Get statistics about current training state.
        
        Returns:
            dict: Statistics including student counts and training status
        """
        current_ids = self.get_current_student_ids()
        trained_ids = self.get_trained_student_ids()
        needs_training, reason, new, removed = self.needs_retraining()
        
        return {
            'current_students': len(current_ids),
            'trained_students': len(trained_ids),
            'needs_training': needs_training,
            'reason': reason,
            'new_students': len(new),
            'removed_students': len(removed)
        }


if __name__ == "__main__":
    # Test the manager
    manager = ModelManager()
    stats = manager.get_training_stats()
    
    print("Model Training Status:")
    print(f"  Current students in Faces/: {stats['current_students']}")
    print(f"  Students model trained on: {stats['trained_students']}")
    print(f"  Needs retraining: {stats['needs_training']}")
    print(f"  Reason: {stats['reason']}")