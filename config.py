"""
config.py
Central configuration file for Face Recognition System.
Contains all system parameters, paths, colors, camera settings, and external service URLs.
"""

import os

# Directory Paths
FACES_DIR = "Faces"
MODELS_DIR = "Models"
DOWNLOADS_DIR = "Downloaded_Faces"

# Google Drive Configuration
# Replace this URL with your actual Google Drive folder URL
GOOGLE_DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1pZBcKW5CpQORjYXAnPZrHHeV0MtWNTHx"

# Camera Configuration
CAMERA_URL = 0  # 0 for default webcam, or use IP camera URL like "rtsp://192.168.1.100:554/stream"
DEFAULT_CAMERA_INDEX = 0  # Fallback for compatibility

# Face Recognition Parameters
FACE_IMAGE_SIZE = (160, 160)  # Required input size for FaceNet
CONFIDENCE_THRESHOLD = 0.5
MIN_FACE_SIZE = 20  # Minimum face size in pixels

# Capture Parameters
CAPTURE_FRAME_COUNT = 3  # Number of frames to capture for stable detection
LIVE_DETECTION_FRAME_SKIP = 100 #number of frames to skip to not lag the live feed

# Face Detection Parameters (MTCNN)
MTCNN_MIN_FACE_SIZE = 20
MTCNN_SCALE_FACTOR = 0.709
MTCNN_STEPS_THRESHOLD = [0.6, 0.7, 0.7]

# File Naming
DEFAULT_MODEL_NAME = "face_model"
EMBEDDINGS_SUFFIX = "_embeddings.npy"
LABELS_SUFFIX = "_labels.npy"

# Image Processing
FLIP_HORIZONTAL = 1
MAX_DISPLAY_WIDTH = 760
MAX_DISPLAY_HEIGHT = 450
THUMBNAIL_PADDING = 20

# UI Colors (Hex)
COLOR_PRIMARY_BG = "#2c3e50"
COLOR_SECONDARY_BG = "#34495e"
COLOR_TEXT_PRIMARY = "white"
COLOR_TEXT_SECONDARY = "#95a5a6"
COLOR_SUCCESS = "#27ae60"
COLOR_WARNING = "#e67e22"
COLOR_ERROR = "#e74c3c"
COLOR_INFO = "#3498db"
COLOR_PURPLE = "#9b59b6"
COLOR_TEAL = "#1abc9c"

# Bounding Box Drawing
BBOX_COLOR_BGR = (0, 255, 0)  # Green in BGR
BBOX_THICKNESS = 2
TEXT_FONT = 0  # cv2.FONT_HERSHEY_SIMPLEX
TEXT_FONT_SCALE = 0.8
TEXT_FONT_SCALE_SMALL = 0.6
TEXT_THICKNESS = 2
TEXT_BG_COLOR_BGR = (0, 0, 0)  # Black
TEXT_COLOR_BGR = (0, 255, 0)  # Green
TEXT_PADDING = 5
TEXT_Y_OFFSET = 10
TEXT_Y_FALLBACK = 30

# UI Dimensions
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
DIALOG_WIDTH = 500
DIALOG_HEIGHT = 600
BUTTON_PADX = 20
BUTTON_PADY = 10

# External Capture Window
CAPTURE_WINDOW_WIDTH = 800
CAPTURE_WINDOW_HEIGHT = 600

# Fonts
FONT_TITLE = ("Helvetica", 20, "bold")
FONT_SUBTITLE = ("Helvetica", 16, "bold")
FONT_BUTTON = ("Helvetica", 12, "bold")
FONT_DIALOG_TITLE = ("Helvetica", 14, "bold")
FONT_LABEL = ("Helvetica", 12)
FONT_STATUS = ("Helvetica", 10)

# Ensure directories exist
os.makedirs(FACES_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)