import logging
from logging.handlers import RotatingFileHandler

def get_logger(name):
    """Create a logger with console and file output"""
    logger = logging.getLogger(name)
    
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    
    file_handler = RotatingFileHandler('app.log', maxBytes=10000000, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.setLevel(logging.INFO)
    return logger