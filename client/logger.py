"""
Logging configuration for RemoteShell client.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(config) -> logging.Logger:
    """
    Setup and configure logger based on configuration.
    
    Args:
        config: LoggingConfig object
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("remoteshell_client")
    logger.setLevel(getattr(logging, config.level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if config.console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if config.file:
        file_handler = RotatingFileHandler(
            config.file,
            maxBytes=config.max_size,
            backupCount=config.backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
