"""File reading strategies for different file types.

This module implements different reading strategies using Protocol-based design.
Different file types require different validation approaches:

- Simple files (PDF, PNG, JPG): Read magic bytes directly
- ZIP-based files (docx, xlsx, pptx): Check ZIP signature + internal structure

The ReaderFactory selects the appropriate reader based on file type.

All readers implement the ReaderProtocol interface for dependency injection.
"""

import zipfile
from pathlib import Path
from typing import Optional

from magicguard.core.exceptions import FileReadError, ValidationError
from magicguard.utils.logger import get_logger


class SimpleReader:
    """Reader for simple file types with straightforward magic bytes.
    
    Handles files like PDF, PNG, JPG, GIF, etc. that have magic bytes
    at the beginning and don't require deep structure validation.
    
    Implements the ReaderProtocol interface.
    """
    
    # File types supported by simple reader
    SIMPLE_FILE_TYPES = {
        'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico', 'webp',
        'mp3', 'mp4', 'avi', 'mkv', 'wav', 'flac',
        'exe', 'dll', 'elf', 'tar', 'gz', 'rar', '7z',
        'xml', 'html', 'json', 'sqlite', 'db'
    }
    
    def __init__(self, logger: Optional[object] = None):
        """Initialize reader.
        
        Args:
            logger: Logger instance (supports LoggerProtocol).
                   If None, creates a logger for this module.
        """
        self.logger = logger or get_logger(__name__)
    
    def read_signature(
        self, file_path: str, length: int, offset: int = 0
    ) -> bytes:
        """Read signature bytes from a file.
        
        Args:
            file_path: Path to the file to read
            length: Number of bytes to read
            offset: Byte offset to start reading from
            
        Returns:
            Bytes read from the file
            
        Raises:
            FileReadError: If file cannot be read
        """
        try:
            self.logger.debug(
                f"Reading {length} bytes from '{file_path}' at offset {offset}"
            )
            
            with open(file_path, 'rb') as f:
                f.seek(offset)
                signature = f.read(length)
            
            self.logger.debug(f"Read signature: {signature.hex().upper()}")
            return signature
            
        except IOError as e:
            error_msg = f"Failed to read file '{file_path}': {str(e)}"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)
    
    def supports_file_type(self, extension: str) -> bool:
        """Check if this reader supports the file type.
        
        Args:
            extension: File extension without dot
            
        Returns:
            True if extension is in SIMPLE_FILE_TYPES
        """
        return extension.lower() in self.SIMPLE_FILE_TYPES
    
    def validate_structure(self, file_path: str, extension: str) -> bool:
        """Validate structure (no-op for simple files).
        
        Simple files don't require deep structure validation beyond
        magic bytes checking.
        
        Args:
            file_path: Path to the file
            extension: Expected file extension
            
        Returns:
            Always returns True for simple files
        """
        self.logger.debug(
            f"Simple file type '.{extension}' - no deep structure validation needed"
        )
        return True


class ZipBasedReader:
    """Reader for ZIP-based file types (Office documents).
    
    Handles Microsoft Office formats (docx, xlsx, pptx) which are actually
    ZIP archives containing XML files. These require:
    1. ZIP signature verification (504B0304)
    2. Internal structure validation (specific files must exist)
    
    Implements the ReaderProtocol interface.
    """
    
    # Office file types and their required internal files
    OFFICE_FILE_STRUCTURES = {
        'docx': ['[Content_Types].xml', 'word/document.xml'],
        'xlsx': ['[Content_Types].xml', 'xl/workbook.xml'],
        'pptx': ['[Content_Types].xml', 'ppt/presentation.xml'],
    }
    
    def __init__(self, logger: Optional[object] = None):
        """Initialize reader.
        
        Args:
            logger: Logger instance (supports LoggerProtocol).
                   If None, creates a logger for this module.
        """
        self.logger = logger or get_logger(__name__)
    
    def read_signature(
        self, file_path: str, length: int, offset: int = 0
    ) -> bytes:
        """Read signature bytes from a file.
        
        Args:
            file_path: Path to the file to read
            length: Number of bytes to read
            offset: Byte offset to start reading from
            
        Returns:
            Bytes read from the file
            
        Raises:
            FileReadError: If file cannot be read
        """
        try:
            self.logger.debug(
                f"Reading {length} bytes from '{file_path}' at offset {offset}"
            )
            
            with open(file_path, 'rb') as f:
                f.seek(offset)
                signature = f.read(length)
            
            self.logger.debug(f"Read signature: {signature.hex().upper()}")
            return signature
            
        except IOError as e:
            error_msg = f"Failed to read file '{file_path}': {str(e)}"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)
    
    def supports_file_type(self, extension: str) -> bool:
        """Check if this reader supports the file type.
        
        Args:
            extension: File extension without dot
            
        Returns:
            True if extension is an Office document type
        """
        return extension.lower() in self.OFFICE_FILE_STRUCTURES
    
    def validate_structure(self, file_path: str, extension: str) -> bool:
        """Validate ZIP-based Office document internal structure.
        
        Checks that the file is a valid ZIP and contains the required
        internal files for the specific Office document type.
        
        Args:
            file_path: Path to the file
            extension: Expected file extension (docx, xlsx, pptx)
            
        Returns:
            True if structure is valid
            
        Raises:
            FileReadError: If file cannot be accessed
            ValidationError: If structure is invalid
        """
        extension = extension.lower()
        
        if extension not in self.OFFICE_FILE_STRUCTURES:
            self.logger.warning(
                f"Extension '.{extension}' not recognized as Office document"
            )
            return False
        
        required_files = self.OFFICE_FILE_STRUCTURES[extension]
        
        try:
            self.logger.debug(f"Validating ZIP structure for '.{extension}' file")
            
            # Verify it's a valid ZIP file
            if not zipfile.is_zipfile(file_path):
                self.logger.warning(
                    f"File '{file_path}' is not a valid ZIP archive"
                )
                return False
            
            # Check for required internal files
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                zip_contents = zip_file.namelist()
                self.logger.debug(
                    f"ZIP contains {len(zip_contents)} files/directories"
                )
                
                for required_file in required_files:
                    if required_file not in zip_contents:
                        self.logger.warning(
                            f"Missing required file '{required_file}' in "
                            f"'.{extension}' document"
                        )
                        return False
                
                self.logger.debug(
                    f"All required files present for '.{extension}' document"
                )
                return True
                
        except zipfile.BadZipFile as e:
            error_msg = f"Corrupted ZIP file '{file_path}': {str(e)}"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)
        except IOError as e:
            error_msg = f"Failed to access file '{file_path}': {str(e)}"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)


class PlainZipReader:
    """Reader for plain ZIP files (not Office documents).
    
    Handles regular ZIP archives that aren't Office documents.
    
    Implements the ReaderProtocol interface.
    """
    
    def __init__(self, logger: Optional[object] = None):
        """Initialize reader.
        
        Args:
            logger: Logger instance (supports LoggerProtocol).
                   If None, creates a logger for this module.
        """
        self.logger = logger or get_logger(__name__)
    
    def read_signature(
        self, file_path: str, length: int, offset: int = 0
    ) -> bytes:
        """Read signature bytes from a file.
        
        Args:
            file_path: Path to the file to read
            length: Number of bytes to read
            offset: Byte offset to start reading from
            
        Returns:
            Bytes read from the file
            
        Raises:
            FileReadError: If file cannot be read
        """
        try:
            self.logger.debug(
                f"Reading {length} bytes from '{file_path}' at offset {offset}"
            )
            
            with open(file_path, 'rb') as f:
                f.seek(offset)
                signature = f.read(length)
            
            self.logger.debug(f"Read signature: {signature.hex().upper()}")
            return signature
            
        except IOError as e:
            error_msg = f"Failed to read file '{file_path}': {str(e)}"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)
    
    def supports_file_type(self, extension: str) -> bool:
        """Check if this reader supports the file type.
        
        Args:
            extension: File extension without dot
            
        Returns:
            True if extension is 'zip'
        """
        return extension.lower() == 'zip'
    
    def validate_structure(self, file_path: str, extension: str) -> bool:
        """Validate that file is a valid ZIP archive.
        
        Args:
            file_path: Path to the file
            extension: Expected file extension
            
        Returns:
            True if file is a valid ZIP
            
        Raises:
            FileReadError: If file cannot be accessed
        """
        try:
            self.logger.debug(f"Validating plain ZIP file")
            is_valid = zipfile.is_zipfile(file_path)
            
            if not is_valid:
                self.logger.warning(f"File '{file_path}' is not a valid ZIP")
            
            return is_valid
            
        except IOError as e:
            error_msg = f"Failed to access file '{file_path}': {str(e)}"
            self.logger.error(error_msg)
            raise FileReadError(error_msg)


class ReaderFactory:
    """Factory for creating appropriate file readers.
    
    Selects the correct reader strategy based on file extension.
    Implements the ReaderFactoryProtocol interface.
    """
    
    def __init__(self, logger: Optional[object] = None):
        """Initialize factory.
        
        Args:
            logger: Logger instance (supports LoggerProtocol)
        """
        self.logger = logger or get_logger(__name__)
        
        # Initialize all available readers
        self._readers = [
            ZipBasedReader(logger),
            PlainZipReader(logger),
            SimpleReader(logger),
        ]
    
    def get_reader(self, extension: str):
        """Get appropriate reader for file extension.
        
        Args:
            extension: File extension without dot
            
        Returns:
            Reader instance that supports the extension
            Implements ReaderProtocol
        """
        extension = extension.lower()
        
        for reader in self._readers:
            if reader.supports_file_type(extension):
                self.logger.debug(
                    f"Selected {reader.__class__.__name__} for '.{extension}'"
                )
                return reader
        
        # Fallback to simple reader for unknown types
        self.logger.warning(
            f"No specific reader for '.{extension}', using SimpleReader"
        )
        return self._readers[-1]  # SimpleReader
