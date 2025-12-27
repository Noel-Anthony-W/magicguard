"""Core module for MagicGuard file validation.

This module contains the core business logic for file type validation using
magic bytes (file signatures). It includes database access, file validation,
and file reading strategies.
"""

from magicguard.core.database import Database
from magicguard.core.exceptions import (
    DatabaseError,
    FileReadError,
    InvalidSignatureError,
    MagicGuardError,
    SignatureNotFoundError,
    ValidationError,
)
from magicguard.core.interfaces import (
    # New protocol names (grouped by responsibility)
    DatabaseProtocol,
    ReaderProtocol,
    ReaderFactoryProtocol,
    ValidatorProtocol,
    DataLoaderProtocol,
    LoggerProtocol,
    # Legacy aliases for backward compatibility
    IDataLoader,
    IFileValidator,
    ILogger,
    IDatabase,
    ISignatureReader,
    ISignatureReaderFactory,
)
from magicguard.core.readers import (
    SimpleReader,
    ZipBasedReader,
    PlainZipReader,
    ReaderFactory,
)
from magicguard.core.validator import FileValidator

__all__ = [
    # Main classes
    "FileValidator",
    "Database",
    # File readers
    "SimpleReader",
    "ZipBasedReader",
    "PlainZipReader",
    "ReaderFactory",
    # Protocols (new names)
    "DatabaseProtocol",
    "ReaderProtocol",
    "ReaderFactoryProtocol",
    "ValidatorProtocol",
    "DataLoaderProtocol",
    "LoggerProtocol",
    # Legacy protocol aliases
    "IDatabase",
    "ISignatureReader",
    "ISignatureReaderFactory",
    "IFileValidator",
    "ILogger",
    "IDataLoader",
    # Exceptions
    "MagicGuardError",
    "ValidationError",
    "SignatureNotFoundError",
    "DatabaseError",
    "FileReadError",
    "InvalidSignatureError",
]
