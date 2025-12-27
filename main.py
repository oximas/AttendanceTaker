"""
main.py
Main entry point for Face Recognition System.
Logs application startup and shutdown.
"""

from ui.GUI import main
from logger import log_startup, log_shutdown, log_error

if __name__ == "__main__":
    try:
        log_startup()  # Log application start
        main()
    except Exception as e:
        log_error("Application crashed", e)
        raise
    finally:
        log_shutdown()  # Log application shutdown