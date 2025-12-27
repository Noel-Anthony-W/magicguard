"""Protocol interfaces for MagicGuard core components.

This module defines protocol-based interfaces (using typing.Protocol) organized
by responsibility. Protocols provide structural subtyping (duck typing) with
type hints, enabling dependency injection and making implementations swappable.

Protocol Groups:
    - Storage Protocols: Database operations for signatures
    - Reading Protocols: File signature reading strategies  
    - Validation Protocols: File type validation
    - Infrastructure Protocols: Logging and data loading

Each protocol group includes implementation guidelines to help developers
create custom implementations.
"""

from pathlib import Path
from typing import Optional, Protocol


# ==============================================================================
# STORAGE PROTOCOLS
# ==============================================================================
# Purpose: Define contracts for storing and retrieving file type signatures
#
# Implementation Guide:
# - Implement persistent storage for file signatures (SQLite, PostgreSQL, etc.)
# - Support CRUD operations for signature management
# - Handle signature queries efficiently (indexing recommended)
# - Provide transaction support for data consistency
#
# Example Use Cases:
# - Default SQLite implementation for local storage
# - PostgreSQL for multi-user environments
# - Redis for high-performance caching
# - In-memory implementation for testing
# ==============================================================================


class DatabaseProtocol(Protocol):
    """Protocol for file signature database operations.
    
    Defines the contract for storing and retrieving file type signatures.
    Implementations should provide efficient signature lookup and management.
    
    Implementation Requirements:
        - Thread-safe operations if used in concurrent environments
        - Support for multiple signatures per extension (at different offsets)
        - Unique constraint on (extension, offset) to prevent duplicates
        - Proper resource cleanup via close() method
        
    Example Implementation:
        ```python
        class CustomDatabase:
            def get_signatures(self, extension: str) -> list[tuple[str, int]]:
                # Query your storage backend
                return [(magic_bytes_hex, offset), ...]
            
            def add_signature(self, extension: str, magic_bytes: str, 
                            offset: int = 0, description: Optional[str] = None,
                            mime_type: Optional[str] = None) -> None:
                # Store signature in your backend
                pass
            
            # ... implement other methods
        ```
    """
    
    def get_signatures(self, extension: str) -> list[tuple[str, int]]:
        """Get all signatures for a file extension.
        
        Args:
            extension: File extension without dot (e.g., 'pdf', 'jpg')
            
        Returns:
            List of tuples containing (magic_bytes_hex, offset)
            Magic bytes should be uppercase hex strings
            
        Raises:
            SignatureNotFoundError: If no signature exists for extension
            DatabaseError: If database query fails
        """
        ...
    
    def add_signature(
        self,
        extension: str,
        magic_bytes: str,
        offset: int = 0,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> None:
        """Add a new signature to the database.
        
        Args:
            extension: File extension without dot (e.g., 'pdf')
            magic_bytes: Hex string of magic bytes (e.g., '25504446')
            offset: Byte offset where magic bytes appear (default: 0)
            description: Human-readable file type description
            mime_type: MIME type (e.g., 'application/pdf')
            
        Raises:
            DatabaseError: If signature cannot be added or already exists
        """
        ...
    
    def get_all_extensions(self) -> list[str]:
        """Get list of all supported extensions.
        
        Returns:
            List of file extensions (without dots) that have signatures
            Should be sorted alphabetically for consistency
            
        Raises:
            DatabaseError: If query fails
        """
        ...
    
    def signature_count(self) -> int:
        """Get total number of signatures in database.
        
        Returns:
            Total count of signature entries
            
        Raises:
            DatabaseError: If query fails
        """
        ...
    
    def close(self) -> None:
        """Close database connection and cleanup resources.
        
        Should be idempotent - safe to call multiple times.
        Ensure all connections/transactions are properly closed.
        """
        ...


# ==============================================================================
# READING PROTOCOLS
# ==============================================================================
# Purpose: Define contracts for reading and validating file signatures
#
# Implementation Guide:
# - Handle different file type categories (simple vs. complex formats)
# - Support reading bytes at arbitrary offsets
# - Implement file type-specific structure validation
# - Return consistent byte representations
#
# Example Use Cases:
# - SimpleReader: PDF, PNG, JPG (direct magic bytes)
# - ZipBasedReader: docx, xlsx, pptx (ZIP with structure validation)
# - NetworkReader: Read from remote storage (S3, HTTP)
# - EncryptedReader: Handle encrypted file containers
# ==============================================================================


class ReaderProtocol(Protocol):
    """Protocol for reading file signatures.
    
    Defines the contract for different file reading strategies.
    Different file types may require different reading approaches
    (e.g., simple magic bytes vs. complex structure validation).
    
    Implementation Requirements:
        - Handle binary file reading safely
        - Support arbitrary byte offsets
        - Provide type-specific validation logic
        - Return consistent byte sequences
        
    Example Implementation:
        ```python
        class CustomReader:
            def read_signature(self, file_path: str, length: int, 
                             offset: int = 0) -> bytes:
                with open(file_path, 'rb') as f:
                    f.seek(offset)
                    return f.read(length)
            
            def supports_file_type(self, extension: str) -> bool:
                return extension in ['custom', 'myformat']
            
            def validate_structure(self, file_path: str, 
                                 extension: str) -> bool:
                # Optional deep validation logic
                return True
        ```
    """
    
    def read_signature(
        self, file_path: str, length: int, offset: int = 0
    ) -> bytes:
        """Read signature bytes from a file.
        
        Args:
            file_path: Path to the file to read
            length: Number of bytes to read
            offset: Byte offset to start reading from (default: 0)
            
        Returns:
            Bytes read from the file (may be less than length if EOF)
            
        Raises:
            FileReadError: If file cannot be read or accessed
        """
        ...
    
    def supports_file_type(self, extension: str) -> bool:
        """Check if this reader supports the given file type.
        
        Used by factories to select appropriate reader for file types.
        
        Args:
            extension: File extension without dot (e.g., 'pdf')
            
        Returns:
            True if this reader can handle the file type
        """
        ...
    
    def validate_structure(self, file_path: str, extension: str) -> bool:
        """Validate internal file structure (for complex formats).
        
        For simple formats (PDF, PNG): Return True immediately
        For complex formats (docx, xlsx): Validate internal structure
        
        Args:
            file_path: Path to the file
            extension: Expected file extension
            
        Returns:
            True if structure is valid for the file type
            
        Raises:
            FileReadError: If file cannot be accessed
        """
        ...


# ==============================================================================
# VALIDATION PROTOCOLS
# ==============================================================================
# Purpose: Define contracts for file type validation
#
# Implementation Guide:
# - Coordinate between database and readers
# - Implement validation logic (magic bytes + structure)
# - Provide file integrity checking (hashing)
# - Handle validation errors appropriately
#
# Example Use Cases:
# - Standard validator: Magic bytes + structure validation
# - Strict validator: Additional metadata checks
# - Fast validator: Skip structure validation for speed
# - Batch validator: Optimize for multiple files
# ==============================================================================


class ValidatorProtocol(Protocol):
    """Protocol for file validation operations.
    
    Defines the contract for validating files against their declared
    extensions using magic bytes and optionally structure validation.
    
    Implementation Requirements:
        - Use appropriate reader for each file type
        - Check magic bytes against database signatures
        - Perform structure validation when needed
        - Provide clear error messages
        
    Example Implementation:
        ```python
        class CustomValidator:
            def __init__(self, database: DatabaseProtocol, 
                        reader_factory: ReaderFactoryProtocol):
                self.database = database
                self.reader_factory = reader_factory
            
            def validate(self, file_path: str) -> bool:
                # 1. Extract extension
                # 2. Get signatures from database
                # 3. Select appropriate reader
                # 4. Validate magic bytes
                # 5. Validate structure if needed
                return True
            
            def get_file_hash(self, file_path: str) -> str:
                # Calculate SHA-256 hash
                import hashlib
                sha256 = hashlib.sha256()
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        sha256.update(chunk)
                return sha256.hexdigest()
        ```
    """
    
    def validate(self, file_path: str) -> bool:
        """Validate that file matches its declared extension.
        
        Checks magic bytes and optionally internal structure to ensure
        the file is actually of the type its extension claims.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if file is valid (magic bytes and structure match)
            
        Raises:
            FileReadError: If file cannot be read or doesn't exist
            ValidationError: If magic bytes don't match extension
            SignatureNotFoundError: If extension not in database
        """
        ...
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for integrity checking.
        
        Useful for verifying file integrity, detecting modifications,
        and creating file fingerprints.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex string of SHA-256 hash (64 characters)
            
        Raises:
            FileReadError: If file cannot be read
        """
        ...
    
    def close(self) -> None:
        """Close validator and cleanup resources.
        
        Should close database connections and other resources.
        Safe to call multiple times (idempotent).
        """
        ...


# ==============================================================================
# INFRASTRUCTURE PROTOCOLS
# ==============================================================================
# Purpose: Define contracts for supporting infrastructure
#
# Implementation Guide:
# - Provide logging capabilities
# - Support data import/export operations
# - Handle configuration and initialization
# - Enable monitoring and debugging
#
# Example Use Cases:
# - Logger: Console, file, remote logging
# - DataLoader: JSON, CSV, API import
# - Monitor: Performance tracking, metrics
# ==============================================================================


class LoggerProtocol(Protocol):
    """Protocol for logging operations.
    
    Defines the contract for logging at different severity levels.
    Implementations can output to console, files, remote services, etc.
    
    Implementation Requirements:
        - Support all standard log levels
        - Format messages consistently
        - Be thread-safe if used concurrently
        - Handle logging errors gracefully
        
    Example Implementation:
        ```python
        import logging
        
        class CustomLogger:
            def __init__(self, name: str):
                self.logger = logging.getLogger(name)
            
            def debug(self, message: str) -> None:
                self.logger.debug(message)
            
            def info(self, message: str) -> None:
                self.logger.info(message)
            
            # ... implement other methods
        ```
    """
    
    def debug(self, message: str) -> None:
        """Log debug-level diagnostic information.
        
        For detailed troubleshooting information, variable values, etc.
        """
        ...
    
    def info(self, message: str) -> None:
        """Log informational messages.
        
        For general operational information and progress updates.
        """
        ...
    
    def warning(self, message: str) -> None:
        """Log warning messages for recoverable issues.
        
        For unexpected situations that don't prevent operation.
        """
        ...
    
    def error(self, message: str) -> None:
        """Log error messages for failures.
        
        For errors that prevent specific operations from completing.
        """
        ...
    
    def critical(self, message: str) -> None:
        """Log critical messages for system-level failures.
        
        For severe errors that may cause system shutdown or data loss.
        """
        ...


class DataLoaderProtocol(Protocol):
    """Protocol for loading signature data into database.
    
    Defines the contract for importing file signatures from various
    sources (JSON, CSV, API, etc.) into the signature database.
    
    Implementation Requirements:
        - Validate source data format
        - Handle import errors gracefully
        - Support bulk operations efficiently
        - Provide progress feedback
        
    Example Implementation:
        ```python
        import json
        
        class CustomDataLoader:
            def load_signatures(self, source_path: str, 
                              database: DatabaseProtocol) -> int:
                with open(source_path) as f:
                    data = json.load(f)
                
                count = 0
                for sig in data['signatures']:
                    database.add_signature(
                        extension=sig['extension'],
                        magic_bytes=sig['magic_bytes'],
                        offset=sig.get('offset', 0)
                    )
                    count += 1
                return count
            
            def validate_source(self, source_path: str) -> bool:
                try:
                    with open(source_path) as f:
                        data = json.load(f)
                    return 'signatures' in data
                except:
                    return False
        ```
    """
    
    def load_signatures(
        self, source_path: str, database: DatabaseProtocol
    ) -> int:
        """Load signatures from a source file into database.
        
        Args:
            source_path: Path to signature data file (JSON, CSV, etc.)
            database: DatabaseProtocol instance to load signatures into
            
        Returns:
            Number of signatures successfully loaded
            
        Raises:
            FileReadError: If source file cannot be read
            DatabaseError: If signatures cannot be inserted
            ValueError: If source data format is invalid
        """
        ...
    
    def validate_source(self, source_path: str) -> bool:
        """Validate that source file has correct format.
        
        Checks file format, structure, and required fields before
        attempting to load data.
        
        Args:
            source_path: Path to signature data file
            
        Returns:
            True if source file is valid and can be loaded
        """
        ...


# ==============================================================================
# FACTORY PROTOCOLS
# ==============================================================================
# Purpose: Define contracts for creating appropriate implementations
#
# Implementation Guide:
# - Select correct implementation based on criteria
# - Manage implementation lifecycle
# - Support plugin/extension mechanisms
# ==============================================================================


class ReaderFactoryProtocol(Protocol):
    """Protocol for creating appropriate file readers.
    
    Defines the contract for factories that select and create the
    appropriate reader implementation based on file type.
    
    Implementation Requirements:
        - Maintain registry of available readers
        - Select reader based on file extension
        - Support fallback mechanisms
        - Handle unknown file types gracefully
        
    Example Implementation:
        ```python
        class CustomReaderFactory:
            def __init__(self):
                self.readers = [
                    ZipBasedReader(),
                    SimpleReader(),
                ]
            
            def get_reader(self, extension: str) -> ReaderProtocol:
                for reader in self.readers:
                    if reader.supports_file_type(extension):
                        return reader
                # Return default reader
                return self.readers[-1]
        ```
    """
    
    def get_reader(self, extension: str) -> ReaderProtocol:
        """Get appropriate reader for file extension.
        
        Selects the best reader implementation for the given file type.
        Returns a reader that supports the extension or a default reader.
        
        Args:
            extension: File extension without dot (e.g., 'pdf', 'docx')
            
        Returns:
            ReaderProtocol implementation that supports the extension
        """
        ...


# ==============================================================================
# LEGACY ALIASES
# ==============================================================================
# Backward compatibility for existing code
# ==============================================================================

IDatabase = DatabaseProtocol
IReader = ReaderProtocol
IReaderFactory = ReaderFactoryProtocol
IValidator = ValidatorProtocol
ILogger = LoggerProtocol
IDataLoader = DataLoaderProtocol

# Additional legacy aliases for backward compatibility
IFileValidator = ValidatorProtocol
ISignatureReader = ReaderProtocol
ISignatureReaderFactory = ReaderFactoryProtocol

__all__ = [
    # Storage Protocols
    "DatabaseProtocol",
    # Reading Protocols
    "ReaderProtocol",
    "ReaderFactoryProtocol",
    # Validation Protocols
    "ValidatorProtocol",
    # Infrastructure Protocols
    "LoggerProtocol",
    "DataLoaderProtocol",
    # Legacy aliases (deprecated)
    "IDatabase",
    "IReader",
    "IReaderFactory",
    "IValidator",
    "ILogger",
    "IDataLoader",
    "IFileValidator",
    "ISignatureReader",
    "ISignatureReaderFactory",
]
