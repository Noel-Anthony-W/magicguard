# src/magicguard/core/validator.py
"""Core file validation logic using magic bytes.

This module provides the FileValidator class for validating files against
their declared extensions using magic byte signatures.
"""

from pathlib import Path
from typing import Optional

from magicguard.core.database import SignatureDatabase
from magicguard.core.exceptions import (
    FileReadError,
    InvalidSignatureError,
    ValidationError,
)

# Maximum file size to read (100MB)
MAX_FILE_SIZE = 104857600


class FileValidator:
    """Validates files using magic byte signatures.
    
    Reads magic bytes from files and compares them against signatures
    stored in the database to detect file type spoofing.
    
    Attributes:
        database: SignatureDatabase instance for signature lookups
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize file validator.
        
        Args:
            db_path: Path to signature database. If None, uses default location.
        """
        self.database = SignatureDatabase(db_path)
    
    def validate(self, file_path: str) -> bool:
        """Validate that file matches its declared extension.
        
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
        
        # Verify file exists and is readable
        if not path.exists():
            raise FileReadError(f"File not found: '{file_path}'")
        
        if not path.is_file():
            raise FileReadError(f"Path is not a file: '{file_path}'")
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise FileReadError(
                f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})"
            )
        
        # Get extension
        extension = path.suffix.lstrip('.').lower()
        if not extension:
            raise ValidationError(f"File has no extension: '{file_path}'")
        
        # Get signatures for extension
        signatures = self.database.get_signatures(extension)
        
        # Check each signature (some file types have multiple)
        for magic_hex, offset in signatures:
            if self._check_signature(file_path, magic_hex, offset):
                return True
        
        # If we get here, none of the signatures matched
        actual_bytes = self._read_magic_bytes(file_path, 8, 0)
        raise ValidationError(
            f"File '{file_path}' has extension '.{extension}' but magic bytes "
            f"don't match. Expected: {magic_hex}, Found: {actual_bytes.hex().upper()}"
        )
    
    def _check_signature(self, file_path: str, magic_hex: str, offset: int) -> bool:
        """Check if file has expected magic bytes at offset.
        
        Args:
            file_path: Path to file
            magic_hex: Expected magic bytes as hex string
            offset: Byte offset to check
            
        Returns:
            True if magic bytes match, False otherwise
            
        Raises:
            FileReadError: If file cannot be read
            InvalidSignatureError: If signature format is invalid
        """
        try:
            expected_bytes = bytes.fromhex(magic_hex)
        except ValueError:
            raise InvalidSignatureError(
                f"Invalid magic bytes format: '{magic_hex}' (must be hex string)"
            )
        
        actual_bytes = self._read_magic_bytes(file_path, len(expected_bytes), offset)
        
        return actual_bytes == expected_bytes
    
    def _read_magic_bytes(self, file_path: str, length: int, offset: int = 0) -> bytes:
        """Read magic bytes from file.
        
        Args:
            file_path: Path to file
            length: Number of bytes to read
            offset: Byte offset to start reading from
            
        Returns:
            Bytes read from file
            
        Raises:
            FileReadError: If file cannot be read
        """
        try:
            with open(file_path, 'rb') as f:
                f.seek(offset)
                return f.read(length)
        except IOError as e:
            raise FileReadError(
                f"Failed to read file '{file_path}': {str(e)}"
            )
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex string of SHA-256 hash
            
        Raises:
            FileReadError: If file cannot be read
        """
        import hashlib
        
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
            
        except IOError as e:
            raise FileReadError(
                f"Failed to hash file '{file_path}': {str(e)}"
            )
    
    def close(self) -> None:
        """Close database connection."""
        self.database.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()