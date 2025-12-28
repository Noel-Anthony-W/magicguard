"""Configuration management for MagicGuard.

This module provides application-wide configuration constants and functions
for managing paths, settings, and environment-specific configurations.

All paths support environment variable overrides for flexibility in different
deployment scenarios (development, testing, production).
"""

import os
from pathlib import Path


# Application metadata
APP_NAME = "MagicGuard"
APP_VERSION = "0.1.0"

# Base application directory (user's home directory)
BASE_DIR = Path.home() / ".magicguard"

# Data directory for database and signatures
DATA_DIR = BASE_DIR / "data"

# Log directory for application logs
LOG_DIR = BASE_DIR / "log"

# Default database path
DEFAULT_DB_PATH = DATA_DIR / "signatures.db"

# Bundled signatures file (in package data)
BUNDLED_SIGNATURES_FILE = "signatures.json"

# File size limits
MAX_FILE_SIZE = 104857600  # 100MB in bytes
MAX_SIGNATURE_LENGTH = 64  # Maximum signature length in bytes

# Logging configuration
DEFAULT_LOG_LEVEL = "DEBUG"  # Development default
LOG_FILE_FORMAT = "%Y-%m-%d.log"  # Daily log files: YYYY-MM-DD.log
MAX_LOG_FILES = 30  # Keep 30 days of logs
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Environment variable names for overrides
ENV_DB_PATH = "MAGICGUARD_DB_PATH"
ENV_LOG_LEVEL = "MAGICGUARD_LOG_LEVEL"
ENV_LOG_DIR = "MAGICGUARD_LOG_DIR"
ENV_DATA_DIR = "MAGICGUARD_DATA_DIR"
ENV_MAX_FILE_SIZE = "MAGICGUARD_MAX_FILE_SIZE"


def get_database_path() -> Path:
    """Get the database file path.
    
    Checks environment variable first, then returns default path.
    Creates parent directory if it doesn't exist.
    
    Returns:
        Path to the signature database file
        
    Example:
        >>> db_path = get_database_path()
        >>> print(db_path)
        /Users/username/.magicguard/data/signatures.db
    """
    # Check environment variable override
    env_path = os.getenv(ENV_DB_PATH)
    if env_path:
        db_path = Path(env_path)
    else:
        db_path = DEFAULT_DB_PATH
    
    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    return db_path


def get_data_dir() -> Path:
    """Get the application data directory.
    
    Creates directory if it doesn't exist.
    
    Returns:
        Path to the data directory
    """
    env_dir = os.getenv(ENV_DATA_DIR)
    data_dir = Path(env_dir) if env_dir else DATA_DIR
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_dir() -> Path:
    """Get the application log directory.
    
    Creates directory if it doesn't exist.
    
    Returns:
        Path to the log directory
    """
    env_dir = os.getenv(ENV_LOG_DIR)
    log_dir = Path(env_dir) if env_dir else LOG_DIR
    
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_level() -> str:
    """Get the configured log level.
    
    Checks environment variable first, then returns default.
    
    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    return os.getenv(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL).upper()


def get_max_file_size() -> int:
    """Get the maximum file size limit.
    
    Checks environment variable first, then returns default.
    Validates that the value is a positive integer.
    
    Returns:
        Maximum file size in bytes
        
    Example:
        >>> max_size = get_max_file_size()
        >>> print(f"Max file size: {max_size / 1024 / 1024:.0f}MB")
        Max file size: 100MB
    """
    env_value = os.getenv(ENV_MAX_FILE_SIZE)
    if env_value:
        try:
            size = int(env_value)
            if size <= 0:
                # Log warning and use default
                import logging
                logging.warning(
                    f"Invalid MAX_FILE_SIZE: {env_value} (must be positive). "
                    f"Using default: {MAX_FILE_SIZE}"
                )
                return MAX_FILE_SIZE
            return size
        except ValueError:
            # Log warning and use default
            import logging
            logging.warning(
                f"Invalid MAX_FILE_SIZE: {env_value} (must be integer). "
                f"Using default: {MAX_FILE_SIZE}"
            )
            return MAX_FILE_SIZE
    return MAX_FILE_SIZE


def ensure_directories() -> None:
    """Ensure all required application directories exist.
    
    Creates base directory, data directory, and log directory if needed.
    This should be called on application initialization.
    """
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    get_data_dir()
    get_log_dir()
