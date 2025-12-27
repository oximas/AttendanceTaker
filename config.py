"""
config.py
Central configuration file for Face Recognition System.
Loads user settings from SettingsManager, falls back to hardcoded defaults.
Contains all system parameters, paths, colors, camera settings, and external service URLs.
"""

import os

# ============================================================================
# SETTINGS MANAGER INTEGRATION
# ============================================================================
# Try to load settings from SettingsManager
# If it fails (first run, missing file), use hardcoded defaults below
try:
    from SettingsManager import get_settings_manager
    _settings = get_settings_manager()
    _use_settings_manager = True
except Exception as e:
    print(f"Warning: Could not load SettingsManager: {e}")
    print("Using hardcoded defaults from config.py")
    _settings = None
    _use_settings_manager = False


def _get_setting(key, default):
    """Helper function to get setting from SettingsManager or use default."""
    if _use_settings_manager and _settings:
        return _settings.get(key, default)
    return default


# ============================================================================
# USER-CONFIGURABLE SETTINGS (Loaded from settings.json via SettingsManager)
# ============================================================================

# Directory Paths
FACES_DIR = _get_setting("FACES_DIR", "Faces")
MODELS_DIR = _get_setting("MODELS_DIR", "Models")
DOWNLOADS_DIR = _get_setting("DOWNLOADS_DIR", "Downloaded_Faces")
ATTENDANCE_DATA_DIR = _get_setting("ATTENDANCE_DATA_DIR", "Attendance_Data")

# Attendance Files
ATTENDANCE_EXCEL_FILE = os.path.join(ATTENDANCE_DATA_DIR, "students_attendance.xlsx")
WRONG_FORMAT_LOG_FILE = os.path.join(ATTENDANCE_DATA_DIR, "wrong_student_name_format.txt")
ATTENDANCE_MARK = _get_setting("ATTENDANCE_MARK", "✓")

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_URL = _get_setting(
    "GOOGLE_DRIVE_FOLDER_URL",
    "https://drive.google.com/drive/folders/1pZBcKW5CpQORjYXAnPZrHHeV0MtWNTHx"
)

# Camera Configuration
CAMERA_URL = _get_setting("CAMERA_URL", 0)
DEFAULT_CAMERA_INDEX = 0  # Fallback for compatibility
# FLIP_HORIZONTAL: 1 = horizontal flip (mirror), 0 = no flip, -1 = vertical flip
FLIP_HORIZONTAL = _get_setting("FLIP_HORIZONTAL", -1)  # cv2.flip uses 1 for horizontal

# Face Recognition Parameters
CONFIDENCE_THRESHOLD = _get_setting("CONFIDENCE_THRESHOLD", 0.5)
MIN_FACE_SIZE = _get_setting("MIN_FACE_SIZE", 20)

# Capture Parameters
CAPTURE_FRAME_COUNT = _get_setting("CAPTURE_FRAME_COUNT", 3)
LIVE_DETECTION_FRAME_SKIP = _get_setting("LIVE_DETECTION_FRAME_SKIP", 100)

# Face Detection Parameters (MTCNN)
MTCNN_MIN_FACE_SIZE = _get_setting("MTCNN_MIN_FACE_SIZE", 20)
MTCNN_SCALE_FACTOR = _get_setting("MTCNN_SCALE_FACTOR", 0.709)
MTCNN_STEPS_THRESHOLD = [0.6, 0.7, 0.7]

# UI Window Dimensions
WINDOW_WIDTH = _get_setting("WINDOW_WIDTH", 900)
WINDOW_HEIGHT = _get_setting("WINDOW_HEIGHT", 700)


# ============================================================================
# HARDCODED CONSTANTS (Not configurable via Settings UI)
# ============================================================================

# Face Recognition Constants
FACE_IMAGE_SIZE = (160, 160)  # Required input size for FaceNet

# File Naming
DEFAULT_MODEL_NAME = "face_model"
EMBEDDINGS_SUFFIX = "_embeddings.npy"
LABELS_SUFFIX = "_labels.npy"

# Image Processing
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


# ============================================================================
# DIRECTORY CREATION
# ============================================================================
# Ensure directories exist
os.makedirs(FACES_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(ATTENDANCE_DATA_DIR, exist_ok=True)