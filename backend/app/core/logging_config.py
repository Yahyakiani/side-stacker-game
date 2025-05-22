# backend/app/core/logging_config.py
import logging
import sys

# --- Configuration ---
LOG_LEVEL = logging.INFO  # Default level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# --- Setup ---
def setup_logger(name="app_logger", level=LOG_LEVEL):
    """
    Sets up and returns a logger instance.
    Each module can get its own logger instance using its __name__.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if already configured (e.g., during uvicorn reload)
    if not logger.handlers:
        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)  # Output to stdout
        console_handler.setLevel(level)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(console_handler)

        # Optionally, add a file handler
        # file_handler = logging.FileHandler("app.log")
        # file_handler.setLevel(logging.WARNING) # Log warnings and above to file
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

    return logger
