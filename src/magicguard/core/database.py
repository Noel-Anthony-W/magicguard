"""Database access layer for file signature management.

This module provides the Database class for managing the SQLite
database containing file type signatures (magic bytes).

Implements the DatabaseProtocol for dependency injection.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from magicguard.core.exceptions import DatabaseError, SignatureNotFoundError
from magicguard.utils.logger import get_logger


class Database:
    """Manages file signature database operations.
    
    Implements the DatabaseProtocol for dependency injection.
    Provides methods for initializing, querying, and managing the SQLite
    database that stores file type signatures and their magic bytes.
    
    Attributes:
        db_path: Path to the SQLite database file
        conn: Active database connection
        logger: Logger instance for diagnostic output
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default
                location from config (~/.magicguard/data/signatures.db).
            logger: Logger instance for diagnostic output. If None, creates
                a logger for this module.
                
        Raises:
            DatabaseError: If database connection or initialization fails
        """
        self.logger = logger or get_logger(__name__)
        
        if db_path is None:
            # Import here to avoid circular dependency
            from magicguard.utils.config import get_database_path
            self.db_path = get_database_path()
        else:
            self.db_path = Path(db_path)
        
        self.conn: Optional[sqlite3.Connection] = None
        
        try:
            self.logger.debug(f"Initializing database at: {self.db_path}")
            
            # Create parent directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            
            # Initialize schema if needed
            self._initialize_schema()
            
            self.logger.info(
                f"Database initialized successfully: {self.db_path}"
            )
            
        except sqlite3.Error as e:
            error_msg = (
                f"Failed to initialize database at '{self.db_path}': {str(e)}"
            )
            self.logger.critical(error_msg)
            raise DatabaseError(error_msg)
    
    @staticmethod
    def _normalize_extension(extension: str) -> str:
        """Normalize file extension to lowercase without leading dot.
        
        Args:
            extension: File extension (may include dot, mixed case)
            
        Returns:
            Normalized extension (lowercase, no dot)
        """
        return extension.lower().lstrip('.')
    
    @staticmethod
    def _normalize_magic_bytes(magic_bytes: str) -> str:
        """Normalize magic bytes to uppercase hex without spaces.
        
        Args:
            magic_bytes: Hex string (may have spaces, mixed case)
            
        Returns:
            Normalized hex string (uppercase, no spaces)
        """
        return magic_bytes.upper().replace(' ', '')
    
    def _validate_signature_input(
        self, extension: str, magic_bytes: str
    ) -> tuple[str, str]:
        """Validate and normalize signature input.
        
        Args:
            extension: File extension
            magic_bytes: Hex string of magic bytes
            
        Returns:
            Tuple of (normalized_extension, normalized_magic_bytes)
            
        Raises:
            DatabaseError: If input is invalid
        """
        # Normalize
        norm_ext = self._normalize_extension(extension)
        norm_hex = self._normalize_magic_bytes(magic_bytes)
        
        # Validate extension
        if not norm_ext:
            raise DatabaseError("Extension cannot be empty")
        
        # Validate magic bytes
        if not norm_hex:
            raise DatabaseError("Magic bytes cannot be empty")
        
        # Validate hex format
        try:
            bytes.fromhex(norm_hex)
        except ValueError:
            raise DatabaseError(
                f"Invalid hex string for magic bytes: '{magic_bytes}'"
            )
        
        return norm_ext, norm_hex
    
    def _initialize_schema(self) -> None:
        """Create database schema if it doesn't exist.
        
        Raises:
            DatabaseError: If schema creation fails
        """
        try:
            self.logger.debug("Checking/creating database schema")
            
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signatures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extension TEXT NOT NULL,
                    magic_bytes TEXT NOT NULL,
                    offset INTEGER DEFAULT 0,
                    description TEXT,
                    mime_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(extension, magic_bytes, offset)
                )
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_extension 
                ON signatures(extension)
            """)
            
            self.conn.commit()
            self.logger.debug("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            error_msg = f"Failed to create database schema: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)
    @staticmethod
    def _normalize_extension(extension: str) -> str:
        """Normalize file extension to lowercase without leading dot.
        
        Args:
            extension: File extension (may include dot, mixed case)
            
        Returns:
            Normalized extension (lowercase, no dot)
        """
        return extension.lower().lstrip('.')
    
    @staticmethod
    def _normalize_magic_bytes(magic_bytes: str) -> str:
        """Normalize magic bytes to uppercase hex without spaces.
        
        Args:
            magic_bytes: Hex string (may have spaces, mixed case)
            
        Returns:
            Normalized hex string (uppercase, no spaces)
        """
        return magic_bytes.upper().replace(' ', '')
    
    def _validate_signature_input(
        self, extension: str, magic_bytes: str
    ) -> tuple[str, str]:
        """Validate and normalize signature input.
        
        Args:
            extension: File extension
            magic_bytes: Hex string of magic bytes
            
        Returns:
            Tuple of (normalized_extension, normalized_magic_bytes)
            
        Raises:
            DatabaseError: If input is invalid
        """
        # Normalize
        norm_ext = self._normalize_extension(extension)
        norm_hex = self._normalize_magic_bytes(magic_bytes)
        
        # Validate extension
        if not norm_ext:
            raise DatabaseError("Extension cannot be empty")
        
        # Validate magic bytes
        if not norm_hex:
            raise DatabaseError("Magic bytes cannot be empty")
        
        # Validate hex format
        try:
            bytes.fromhex(norm_hex)
        except ValueError:
            raise DatabaseError(
                f"Invalid hex string for magic bytes: '{magic_bytes}'"
            )
        
        return norm_ext, norm_hex
    def get_signatures(self, extension: str) -> list[tuple[str, int]]:
        """Get all signatures for a file extension.
        
        Args:
            extension: File extension without dot (e.g., 'pdf', 'jpg')
            
        Returns:
            List of tuples containing (magic_bytes, offset) for the extension.
            Magic bytes are returned as hex strings.
            
        Raises:
            SignatureNotFoundError: If no signature found for extension
            DatabaseError: If database query fails
        """
        try:
            self.logger.debug(f"Querying signatures for extension: .{extension}")
            norm_ext = self._normalize_extension(extension)
            
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT magic_bytes, offset FROM signatures WHERE extension = ?",
                (norm_ext,)
            )
            results = cursor.fetchall()
            
            if not results:
                error_msg = f"No signature found for extension '.{norm_ext}'"
                self.logger.warning(error_msg)
                raise SignatureNotFoundError(error_msg)
            
            signatures = [(row["magic_bytes"], row["offset"]) for row in results]
            self.logger.debug(
                f"Found {len(signatures)} signature(s) for '.{norm_ext}'"
            )
            
            return signatures
            
        except sqlite3.Error as e:
            error_msg = f"Failed to query signatures for '.{norm_ext}': {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def add_signature(
        self,
        extension: str,
        magic_bytes: str,
        offset: int = 0,
        description: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> None:
        """Add a new signature to the database.
        
        Args:
            extension: File extension without dot (e.g., 'pdf')
            magic_bytes: Hex string of magic bytes (e.g., '25504446')
            offset: Byte offset where magic bytes appear (default: 0)
            description: Human-readable description of file type
            mime_type: MIME type (e.g., 'application/pdf')
            
        Raises:
            DatabaseError: If signature cannot be added or input is invalid
        """
        # Validate and normalize input
        norm_ext, norm_hex = self._validate_signature_input(extension, magic_bytes)
        
        try:
            self.logger.debug(
                f"Adding signature for '.{norm_ext}': {norm_hex} at offset {offset}"
            )
            
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO signatures 
                (extension, magic_bytes, offset, description, mime_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (norm_ext, norm_hex, offset, description, mime_type)
            )
            self.conn.commit()
            
            self.logger.info(f"Successfully added signature for '.{norm_ext}'")
            
        except sqlite3.IntegrityError:
            error_msg = (
                f"Signature for '.{norm_ext}' with magic bytes {norm_hex} "
                f"at offset {offset} already exists"
            )
            self.logger.warning(error_msg)
            raise DatabaseError(error_msg)
        except sqlite3.Error as e:
            error_msg = f"Failed to add signature for '.{norm_ext}': {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def get_all_extensions(self) -> list[str]:
        """Get list of all supported extensions.
        
        Returns:
            List of file extensions (without dots) that have signatures
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            self.logger.debug("Retrieving all extensions from database")
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT extension FROM signatures ORDER BY extension")
            results = cursor.fetchall()
            extensions = [row["extension"] for row in results]
            
            self.logger.debug(f"Found {len(extensions)} unique extensions")
            return extensions
            
        except sqlite3.Error as e:
            error_msg = f"Failed to retrieve extensions: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def signature_count(self) -> int:
        """Get total number of signatures in database.
        
        Returns:
            Total count of signature entries
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM signatures")
            result = cursor.fetchone()
            count = result["count"]
            
            self.logger.debug(f"Database contains {count} signatures")
            return count
            
        except sqlite3.Error as e:
            error_msg = f"Failed to count signatures: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.logger.debug("Closing database connection")
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close()
