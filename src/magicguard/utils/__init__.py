"""Utilities module for MagicGuard.

This module provides utility functions and classes used throughout the
application, including logging, configuration, and data loading.
"""

from magicguard.utils.config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_DB_PATH,
    LOG_DIR,
    DATA_DIR,
    get_database_path,
    get_data_dir,
    get_log_dir,
    get_log_level,
    ensure_directories,
)
from magicguard.utils.logger import get_logger, setup_logging, cleanup_old_logs
from magicguard.utils.data_loader import (
    DataLoader,
    initialize_default_signatures,
    export_signatures_to_json,
)

__all__ = [
    # Config exports
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_DB_PATH",
    "LOG_DIR",
    "DATA_DIR",
    "get_database_path",
    "get_data_dir",
    "get_log_dir",
    "get_log_level",
    "ensure_directories",
    # Logger exports
    "get_logger",
    "setup_logging",
    "cleanup_old_logs",
    # Data loader exports
    "DataLoader",
    "initialize_default_signatures",
    "export_signatures_to_json",
]
