"""Core file validation logic using magic bytes.

This module provides the FileValidator class for validating files against
their declared extensions using magic byte signatures.

Implements the ValidatorProtocol and uses dependency injection for
database and file readers.
"""

import hashlib
import logging
from pathlib import Path
from typing import Optional

from magicguard.core.exceptions import (
    FileReadError,
    InvalidSignatureError,
    ValidationError,
)
from magicguard.utils.logger import get_logger

# Maximum file size to read (100MB)
MAX_FILE_SIZE = 104857600


class FileValidator:
    """Validates files using magic byte signatures.
    
    Implements the ValidatorProtocol. Uses dependency injection for
    database access and file reading strategies.
    
    Reads magic bytes from files and compares them against signatures
    stored in the database to detect file type spoofing. Uses the Strategy
    pattern for different file types (simple vs. ZIP-based).
    
    Attributes:
        database: DatabaseProtocol instance for signature lookups
        reader_factory: ReaderFactoryProtocol for creating appropriate readers
        logger: LoggerProtocol instance for diagnostic output
    """
    
    def __init__(
        self,
        database=None,
        reader_factory=None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize file validator with dependency injection.
        
        Args:
            database: DatabaseProtocol implementation. If None, creates
                a new Database with default path.
            reader_factory: ReaderFactoryProtocol instance. If None, creates
                a new ReaderFactory.
            logger: LoggerProtocol instance. If None, creates logger for this module.
        """
        self.logger = logger or get_logger(__name__)
        
        # Lazy import to avoid circular dependency
        if database is None:
            from magicguard.core.database import Database
            self.database = Database(logger=self.logger)
            self.logger.debug("Created default Database")
        else:
            self.database = database
            self.logger.debug("Using injected database")
        
        if reader_factory is None:
            from magicguard.core.readers import ReaderFactory
            self.reader_factory = ReaderFactory(logger=self.logger)
            self.logger.debug("Created default ReaderFactory")
        else:
            self.reader_factory = reader_factory
            self.logger.debug("Using injected reader factory")
        
        self.logger.info("FileValidator initialized successfully")
    
    def validate(self, file_path: str) -> bool:
        """Validate that file matches its declared extension.
        
        Uses the appropriate signature reader strategy based on file type
        and validates both magic bytes and internal structure (for complex
        formats like Office documents).
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if file is valid (magic bytes match extension)
            
        Raises:
            FileReadError: If file cannot be read
            ValidationError: If magic bytes don't match extension
            SignatureNotFoundError: If extension not in database
        """
        path = Path(file_path)
        
        self.logger.info(f"Validating file: {file_path}")
        
        # Verify file exists and is readable
        if not path.exists():
            error_msg = f"File not found: '{file_path}'"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)
        
        if not path.is_file():
            error_msg = f"Path is not a file: '{file_path}'"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            error_msg = (
                f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})"
            )
            self.logger.error(error_msg)
            raise FileReadError(error_msg)
        
        self.logger.debug(f"File size: {file_size} bytes")
        
        # Get extension
        extension = path.suffix.lstrip('.').lower()
        if not extension:
            error_msg = f"File has no extension: '{file_path}'"
            self.logger.error(error_msg)
            raise ValidationError(error_msg)
        
        self.logger.debug(f"File extension: .{extension}")
        
        # Get appropriate signature reader for this file type
        reader = self.reader_factory.get_reader(extension)
        
        # Get signatures for extension
        signatures = self.database.get_signatures(extension)
        self.logger.debug(f"Checking {len(signatures)} signature(s)")
        
        # Check each signature (some file types have multiple)
        for magic_hex, offset in signatures:
            if self._check_signature(file_path, magic_hex, offset, reader):
                # Magic bytes match, now validate structure if needed
                if reader.validate_structure(file_path, extension):
                    self.logger.info(
                        f"✓ File '{file_path}' validated successfully as '.{extension}'"
                    )
                    return True
                else:
                    error_msg = (
                        f"File '{file_path}' has correct magic bytes for '.{extension}' "
                        f"but failed internal structure validation"
                    )
                    self.logger.error(error_msg)
                    raise ValidationError(error_msg)
        
        # If we get here, none of the signatures matched
        actual_bytes = reader.read_signature(file_path, 8, 0)
        error_msg = (
            f"File '{file_path}' has extension '.{extension}' but magic bytes "
            f"don't match. Expected: {magic_hex}, Found: {actual_bytes.hex().upper()}"
        )
        self.logger.error(error_msg)
        raise ValidationError(error_msg)
    
    def _check_signature(
        self, file_path: str, magic_hex: str, offset: int, reader
    ) -> bool:
        """Check if file has expected magic bytes at offset.
        
        Args:
            file_path: Path to file
            magic_hex: Expected magic bytes as hex string
            offset: Byte offset to check
            reader: Signature reader to use
            
        Returns:
            True if magic bytes match, False otherwise
            
        Raises:
            FileReadError: If file cannot be read
            InvalidSignatureError: If signature format is invalid
        """
        try:
            expected_bytes = bytes.fromhex(magic_hex)
        except ValueError:
            error_msg = (
                f"Invalid magic bytes format: '{magic_hex}' (must be hex string)"
            )
            self.logger.error(error_msg)
            raise InvalidSignatureError(error_msg)
        
        actual_bytes = reader.read_signature(file_path, len(expected_bytes), offset)
        
        match = actual_bytes == expected_bytes
        if match:
            self.logger.debug(
                f"✓ Magic bytes match at offset {offset}: {magic_hex}"
            )
        else:
            self.logger.debug(
                f"✗ Magic bytes mismatch at offset {offset}. "
                f"Expected: {magic_hex}, Got: {actual_bytes.hex().upper()}"
            )
        
        return match
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex string of SHA-256 hash
            
        Raises:
            FileReadError: If file cannot be read
        """
        self.logger.debug(f"Calculating SHA-256 hash for: {file_path}")
        
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            
            file_hash = sha256.hexdigest()
            self.logger.debug(f"SHA-256 hash: {file_hash}")
            return file_hash
            
        except IOError as e:
            error_msg = f"Failed to hash file '{file_path}': {str(e)}"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)
    
    def close(self) -> None:
        """Close database connection and cleanup resources."""
        self.logger.debug("Closing FileValidator and associated resources")
        self.database.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
