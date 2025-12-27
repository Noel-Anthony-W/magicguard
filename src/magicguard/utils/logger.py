"""Centralized logging system for MagicGuard.

This module provides a unified logging interface with support for:
- Beautiful console output using Rich library
- Daily rotating file logs
- Automatic cleanup of old log files
- Thread-safe singleton pattern
- Environment-based configuration

The logger writes to both console (with colors) and daily log files stored
in ~/.magicguard/log/ directory.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from magicguard.utils import config


# Singleton logger registry
_loggers: dict[str, logging.Logger] = {}
_initialized: bool = False


def setup_logging(
    level: Optional[str] = None, log_dir: Optional[Path] = None
) -> None:
    """Configure global logging settings.
    
    Sets up both console (Rich) and file handlers with appropriate formatting.
    This should be called once at application startup.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses config.get_log_level()
        log_dir: Directory for log files. If None, uses config.get_log_dir()
        
    Example:
        >>> setup_logging(level="DEBUG")
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    global _initialized
    
    if _initialized:
        return
    
    # Determine log level and directory
    log_level = level or config.get_log_level()
    log_directory = log_dir or config.get_log_dir()
    
    # Ensure log directory exists
    log_directory.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler with Rich formatting
    console = Console(stderr=True)
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=True,
        show_path=True,
    )
    console_handler.setLevel(getattr(logging, log_level))
    root_logger.addHandler(console_handler)
    
    # File handler with daily rotation
    log_file = log_directory / datetime.now().strftime(config.LOG_FILE_FORMAT)
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(getattr(logging, log_level))
    
    # Detailed format for file logs
    file_formatter = logging.Formatter(
        fmt=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Cleanup old log files
    cleanup_old_logs(log_directory, config.MAX_LOG_FILES)
    
    _initialized = True
    
    # Log initialization
    init_logger = get_logger("magicguard.utils.logger")
    init_logger.info(
        f"Logging initialized: level={log_level}, log_dir={log_directory}"
    )


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger for the given module.
    
    Returns a configured logger instance. If logging hasn't been set up yet,
    initializes it automatically with default settings.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
        >>> logger.info("Info message")
        >>> logger.warning("Warning message")
        >>> logger.error("Error message")
    """
    global _initialized
    
    # Lazy initialization
    if not _initialized:
        setup_logging()
    
    # Return cached logger if exists
    if name in _loggers:
        return _loggers[name]
    
    # Create new logger
    logger = logging.getLogger(name)
    _loggers[name] = logger
    
    return logger


def cleanup_old_logs(log_dir: Path, max_days: int = 30) -> int:
    """Remove log files older than specified number of days.
    
    Scans the log directory for log files matching the date format pattern
    and removes any that are older than max_days.
    
    Args:
        log_dir: Directory containing log files
        max_days: Maximum age of log files to keep (default: 30 days)
        
    Returns:
        Number of log files deleted
        
    Example:
        >>> cleanup_old_logs(Path("~/.magicguard/log"), max_days=30)
        3  # Deleted 3 old log files
    """
    if not log_dir.exists():
        return 0
    
    deleted_count = 0
    cutoff_date = datetime.now() - timedelta(days=max_days)
    
    # Find all log files matching the date pattern
    for log_file in log_dir.glob("*.log"):
        try:
            # Extract date from filename (YYYY-MM-DD.log)
            filename = log_file.stem  # Remove .log extension
            file_date = datetime.strptime(filename, "%Y-%m-%d")
            
            if file_date < cutoff_date:
                log_file.unlink()
                deleted_count += 1
                
        except (ValueError, OSError):
            # Skip files that don't match expected format or can't be deleted
            continue
    
    return deleted_count


def rotate_log_file_if_needed(log_dir: Path) -> None:
    """Check if a new log file is needed for today.
    
    If the current log file is from a previous day, this function will
    trigger the creation of a new log file for today.
    
    Args:
        log_dir: Directory containing log files
    """
    # Get current root logger handlers
    root_logger = logging.getLogger()
    
    # Find file handler
    file_handler = None
    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
            break
    
    if not file_handler:
        return
    
    # Check if current log file matches today's date
    current_file = Path(file_handler.baseFilename)
    expected_file = log_dir / datetime.now().strftime(config.LOG_FILE_FORMAT)
    
    if current_file != expected_file:
        # Close current handler
        file_handler.close()
        root_logger.removeHandler(file_handler)
        
        # Create new handler for today
        new_handler = logging.FileHandler(
            expected_file, mode="a", encoding="utf-8"
        )
        new_handler.setLevel(file_handler.level)
        
        file_formatter = logging.Formatter(
            fmt=config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT
        )
        new_handler.setFormatter(file_formatter)
        root_logger.addHandler(new_handler)


# Initialize logging when module is imported (lazy)
# This ensures logging is available even if setup_logging() isn't called explicitly
def _ensure_logging_initialized():
    """Ensure logging is initialized when module is first imported."""
    global _initialized
    if not _initialized:
        try:
            setup_logging()
        except Exception:
            # Fallback to basic console logging if setup fails
            logging.basicConfig(
                level=logging.INFO,
                format="%(levelname)s: %(message)s",
                stream=sys.stderr,
            )
            _initialized = True
