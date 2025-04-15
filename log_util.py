import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
load_dotenv()

LOG_PATH = os.environ.get("LOG_PATH")
os.makedirs(LOG_PATH, exist_ok = True)

def getLogger(name : str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        log_path = os.path.join(LOG_PATH, "collector.log")
        handler = RotatingFileHandler(log_path, maxBytes = 10 * 1024 * 1024, backupCount = 10)
        formatter = logging.Formatter( "[%(asctime)s] :: [%(levelname)s] :: %(name)s :: [%(message)s]" )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


