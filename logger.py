"""
logger.py
Centralized logging system for the Face Recognition Attendance System.
Logs all important events to app.log file with timestamps and rotation.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_FILE = "app.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 3  # Keep 3 old log files
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# LOGGER SETUP
# ============================================================================

def setup_logger():
    """
    Set up the application logger with file rotation.
    Creates app.log file and configures logging format.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("AttendanceTracker")
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler (optional - shows logs in console too)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Initialize the global logger
_logger = setup_logger()


# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

def log_info(message):
    """
    Log an informational message.
    Use for: Normal operations, successful actions, status updates.
    
    Args:
        message: Message to log
        
    Example:
        log_info("Camera opened successfully")
    """
    _logger.info(message)


def log_warning(message):
    """
    Log a warning message.
    Use for: Recoverable issues, deprecation notices, unexpected but handled situations.
    
    Args:
        message: Message to log
        
    Example:
        log_warning("Unknown face detected")
    """
    _logger.warning(message)


def log_error(message, exception=None):
    """
    Log an error message.
    Use for: Failures, exceptions, critical issues.
    
    Args:
        message: Error message to log
        exception: Optional exception object
        
    Example:
        log_error("Failed to open camera", exc)
    """
    if exception:
        _logger.error(f"{message}: {str(exception)}", exc_info=True)
    else:
        _logger.error(message)


def log_debug(message):
    """
    Log a debug message.
    Use for: Detailed technical information, troubleshooting.
    
    Args:
        message: Message to log
        
    Example:
        log_debug("Processing frame 10/50")
    """
    _logger.debug(message)


def log_separator():
    """
    Log a visual separator line.
    Use for: Separating major sections in logs.
    """
    _logger.info("=" * 60)


def log_section(title):
    """
    Log a section header.
    Use for: Starting a major operation.
    
    Args:
        title: Section title
        
    Example:
        log_section("TRAINING MODEL")
    """
    log_separator()
    _logger.info(title)
    log_separator()


# ============================================================================
# STARTUP LOGGING
# ============================================================================

def log_startup():
    """Log application startup with version and timestamp."""
    log_separator()
    log_info("AttendanceTracker Application Started")
    log_info(f"Version: 0.9-beta")
    log_info(f"Log file: {os.path.abspath(LOG_FILE)}")
    log_separator()


def log_shutdown():
    """Log application shutdown."""
    log_separator()
    log_info("AttendanceTracker Application Closed")
    log_separator()


# ============================================================================
# EXAMPLE USAGE (for testing)
# ============================================================================

if __name__ == "__main__":
    # Test the logger
    log_startup()
    log_info("This is an info message")
    log_warning("This is a warning message")
    log_error("This is an error message")
    log_debug("This is a debug message")
    log_section("TEST SECTION")
    log_info("Section content here")
    log_shutdown()
    
    print(f"\nLog file created at: {os.path.abspath(LOG_FILE)}")
    print("Check app.log to see the logged messages!")