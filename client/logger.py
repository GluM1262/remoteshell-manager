"""
Logging configuration for RemoteShell client.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(logging_config):
    """Configure logging based on configuration."""
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, logging_config.level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    if logging_config.console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, logging_config.level.upper()))
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if logging_config.file:
        log_path = Path(logging_config.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=logging_config.max_size,
            backupCount=logging_config.backup_count
        )
        file_handler.setLevel(getattr(logging, logging_config.level.upper()))
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger
