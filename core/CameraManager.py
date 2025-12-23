"""
CameraManager.py
Camera management module with live streaming support.
Handles camera initialization, frame capture, continuous streaming, and cleanup.
"""

import cv2
import threading
import time
from config import CAMERA_URL, FLIP_HORIZONTAL


class CameraManager:
    """Manages camera operations with automatic resource cleanup and live streaming."""
    
    def __init__(self, camera_source=CAMERA_URL):
        self.camera_source = camera_source
        self.cap = None
        self.is_streaming = False
        self.stream_thread = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
    
    def open(self):
        """Open camera connection."""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_source)
            if not self.cap.isOpened():
                raise RuntimeError(f"Failed to open camera {self.camera_source}")
    
    def close(self):
        """Release camera resources."""
        self.stop_stream()
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
    
    def start_stream(self):
        """Start continuous video streaming in background thread."""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self.stream_thread.start()
    
    def stop_stream(self):
        """Stop continuous video streaming."""
        self.is_streaming = False
        if self.stream_thread is not None:
            self.stream_thread.join(timeout=2)
            self.stream_thread = None
    
    def _stream_loop(self):
        """Internal streaming loop running in background thread."""
        self.open()
        
        while self.is_streaming:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                frame = cv2.flip(frame, FLIP_HORIZONTAL)
                
                with self.frame_lock:
                    self.current_frame = frame.copy()
    
    def get_current_frame(self):
        """
        Get the most recent frame from live stream.
        
        Returns:
            numpy.ndarray: Current frame or None if no frame available
        """
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
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