import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def configure_logger(name: str = "app"):
    """Configure and return a production-ready logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    )


    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = configure_logger()