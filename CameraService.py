"""
Camera Service Module
Handles camera capture and frame management.
"""
import cv2
import numpy as np
from typing import List, Optional
from collections import Counter


class CameraService:
    """Manages camera operations and frame capture."""
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize camera service.
        
        Args:
            camera_index: Camera device index (0 for default camera)
        """
        self.camera_index = camera_index
        self._capture: Optional[cv2.VideoCapture] = None
    
    def capture_single_frame(self, flip_horizontal: bool = True) -> np.ndarray:
        """
        Capture a single frame from camera.
        
        Args:
            flip_horizontal: Whether to flip the frame horizontally
            
        Returns:
            Captured frame as numpy array
            
        Raises:
            RuntimeError: If frame capture fails
        """
        self._ensure_camera_open()
        
        success, frame = self._capture.read()
        
        if not success or frame is None:
            raise RuntimeError("Failed to capture frame from camera")
        
        if flip_horizontal:
            frame = cv2.flip(frame, flipCode=1)
        
        return frame
    
    def capture_multiple_frames(
        self, 
        num_frames: int, 
        flip_horizontal: bool = True
    ) -> List[np.ndarray]:
        """
        Capture multiple consecutive frames.
        
        Args:
            num_frames: Number of frames to capture
            flip_horizontal: Whether to flip frames horizontally
            
        Returns:
            List of captured frames
            
        Raises:
            RuntimeError: If no frames captured successfully
        """
        frames = []
        
        for _ in range(num_frames):
            try:
                frame = self.capture_single_frame(flip_horizontal)
                frames.append(frame)
            except RuntimeError:
                continue
        
        if not frames:
            raise RuntimeError("No frames captured successfully")
        
        return frames
    
    def release(self):
        """Release camera resources."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
    
    def _ensure_camera_open(self):
        """Open camera if not already open."""
        if self._capture is None or not self._capture.isOpened():
            self._capture = cv2.VideoCapture(self.camera_index)
            
            if not self._capture.isOpened():
                raise RuntimeError(f"Failed to open camera at index {self.camera_index}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures camera is released."""
        self.release()
    
    def __del__(self):
        """Destructor - cleanup camera resources."""
        self.release()


class FrameStabilizer:
    """Finds the most stable frame from a sequence based on detection consistency."""
    
    @staticmethod
    def find_most_consistent_detection(
        frames: List[np.ndarray],
        detection_function
    ) -> tuple:
        """
        Find frame with most consistent detection count.
        
        Args:
            frames: List of frames to analyze
            detection_function: Function that returns (count, boxes) for a frame
            
        Returns:
            Tuple of (stable_frame, count, boxes)
            
        Raises:
            RuntimeError: If no stable frame found
        """
        if not frames:
            raise RuntimeError("No frames provided for stabilization")
        
        # Run detection on all frames
        detections = [detection_function(frame) for frame in frames]
        
        # Find most common detection count
        counts = [count for count, _ in detections]
        most_common_count = Counter(counts).most_common(1)[0][0]
        
        # Return first frame matching the most common count
        for frame, (count, boxes) in zip(frames, detections):
            if count == most_common_count:
                return frame.copy(), count, boxes
        
        raise RuntimeError("No stable frame found")