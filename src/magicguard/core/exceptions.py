# src/magicguard/core/exceptions.py
"""Custom exceptions for MagicGuard.

This module defines the exception hierarchy used throughout the application.
All custom exceptions inherit from MagicGuardError base class.
"""


class MagicGuardError(Exception):
    """Base exception for all MagicGuard errors.
    
    All custom exceptions in the application should inherit from this class
    to allow for unified error handling.
    """
    pass


class ValidationError(MagicGuardError):
    """Raised when file validation fails.
    
    This exception is raised when a file's magic bytes don't match its
    declared extension, indicating potential file type spoofing.
    """
    pass


class SignatureNotFoundError(MagicGuardError):
    """Raised when signature not found in database.
    
    This exception is raised when attempting to validate a file type
    that doesn't have a signature entry in the database.
    """
    pass


class DatabaseError(MagicGuardError):
    """Raised when database operations fail.
    
    This exception is raised for any database-related errors including
    connection failures, query errors, or schema validation issues.
    """
    pass


class FileReadError(MagicGuardError):
    """Raised when file cannot be read.
    
    This exception is raised when a file cannot be accessed or read,
    due to permissions, missing file, or I/O errors.
    """
    pass


class InvalidSignatureError(MagicGuardError):
    """Raised when signature format is invalid.
    
    This exception is raised when a signature in the database has
    an invalid format (e.g., malformed hex string).
    """
    pass