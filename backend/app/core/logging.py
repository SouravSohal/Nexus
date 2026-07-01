import logging
import sys

def setup_logging() -> logging.Logger:
    """
    Sets up a standardized logger for the NEXUS platform.
    """
    logger = logging.getLogger("nexus")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if already initialized
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        # Simple format that keeps console output clean and premium
        formatter = logging.Formatter(
            fmt="%(asctime)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    # Disable propagation to prevent duplicate logs in FastAPI/Uvicorn
    logger.propagate = False
    return logger

logger = setup_logging()
