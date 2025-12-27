"""
main.py
Main entry point for the Face Recognition Attendance System.
Handles first-run detection, stdout/stderr redirection for PyInstaller builds,
and initializes the GUI application with proper error handling.
"""

import os
import sys

# CRITICAL FIX for PyInstaller --windowed mode
# Redirect stdout/stderr to prevent 'NoneType' has no attribute 'write' errors
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# Now safe to import everything else
from ui.GUI import main
from logger import log_startup, log_shutdown, log_error, log_info

# First run marker file
FIRST_RUN_FILE = ".first_run_complete"

def is_first_run():
    """Check if this is the first time running the application."""
    return not os.path.exists(FIRST_RUN_FILE)

def mark_first_run_complete():
    """Mark that first run is complete."""
    try:
        with open(FIRST_RUN_FILE, 'w') as f:
            f.write("First run completed")
        log_info("First run marked as complete")
    except Exception as e:
        log_error("Failed to mark first run complete", e)

if __name__ == "__main__":
    try:
        log_startup()
        
        # Check if first run
        first_run = is_first_run()
        if first_run:
            log_info("First run detected - will show welcome dialog")
        
        # Run main application
        main(first_run=first_run)
        
        # Mark first run as complete
        if first_run:
            mark_first_run_complete()
        
    except Exception as e:
        log_error("Application crashed", e)
        raise
    finally:
        log_shutdown()