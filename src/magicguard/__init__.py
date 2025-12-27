"""MagicGuard - File type validator using magic bytes.

A Python library for detecting file type spoofing by validating files
against their magic bytes (file signatures). Supports simple file types
(PDF, PNG, JPG) and complex ZIP-based formats (docx, xlsx, pptx).

Example usage:
    >>> from magicguard import FileValidator
    >>> validator = FileValidator()
    >>> validator.validate("document.pdf")
    True
"""

__version__ = "0.1.0"
__author__ = "Anthony Weiß"
__email__ = "weissanthony.code@gmail.com"

from magicguard.core import (
    FileValidator,
    Database,
    ValidationError,
    MagicGuardError,
    DatabaseError,
    SignatureNotFoundError,
    FileReadError,
)

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    # Main API
    "FileValidator",
    "Database",
    # Common exceptions
    "MagicGuardError",
    "ValidationError",
    "SignatureNotFoundError",
    "DatabaseError",
    "FileReadError",
]
