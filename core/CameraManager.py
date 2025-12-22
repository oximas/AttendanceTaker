"""
Camera management module.
Handles camera initialization, frame capture, and cleanup.
"""

import cv2
from config import DEFAULT_CAMERA_INDEX, FLIP_HORIZONTAL


class CameraManager:
    """Manages camera operations with automatic resource cleanup."""
    
    def __init__(self, camera_index=DEFAULT_CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = None
    
    def open(self):
        """Open camera connection."""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.camera_index}")
    
    def close(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def is_open(self):
        """Check if camera is currently open."""
        return self.cap is not None and self.cap.isOpened()
    
    def capture_frame(self, flip=True):
        """
        Capture a single frame from camera.
        
        Args:
            flip: Whether to flip frame horizontally
            
        Returns:
            numpy.ndarray: Captured frame
        """
        if not self.is_open():
            self.open()
        
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Failed to capture frame")
        
        if flip:
            frame = cv2.flip(frame, FLIP_HORIZONTAL)
        
        return frame
    
    def capture_frames(self, count, flip=True):
        """
        Capture multiple frames from camera.
        
        Args:
            count: Number of frames to capture
            flip: Whether to flip frames horizontally
            
        Returns:
            list: List of captured frames
        """
        self.open()
        frames = []
        
        for _ in range(count):
            try:
                frame = self.capture_frame(flip=flip)
                frames.append(frame)
            except RuntimeError:
                continue
        
        if not frames:
            raise RuntimeError("No frames captured successfully")
        
        return frames
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()