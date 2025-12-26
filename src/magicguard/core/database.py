# src/magicguard/core/database.py
"""Database access layer for file signature management.

This module provides the SignatureDatabase class for managing the SQLite
database containing file type signatures (magic bytes).
"""

import sqlite3
from pathlib import Path
from typing import Optional

from magicguard.core.exceptions import DatabaseError, SignatureNotFoundError
    

class SignatureDatabase:
    """Manages file signature database operations.
    
    Provides methods for initializing, querying, and managing the SQLite
    database that stores file type signatures and their magic bytes.
    
    Attributes:
        db_path: Path to the SQLite database file
        conn: Active database connection
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default
                location in user's home directory or package data directory.
                
        Raises:
            DatabaseError: If database connection or initialization fails
        """
        if db_path is None:
            # Default to package data directory or home directory
            db_path = str(Path.home() / ".magicguard" / "signatures.db")
        
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        
        try:
            # Create parent directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            
            # Initialize schema if needed
            self._initialize_schema()
            
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to initialize database at '{self.db_path}': {str(e)}"
            )
    
    def _initialize_schema(self) -> None:
        """Create database schema if it doesn't exist.
        
        Raises:
            DatabaseError: If schema creation fails
        """
        try:
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
                    UNIQUE(extension, offset)
                )
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_extension 
                ON signatures(extension)
            """)
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create database schema: {str(e)}")
    
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
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT magic_bytes, offset FROM signatures WHERE extension = ?",
                (extension.lower(),)
            )
            results = cursor.fetchall()
            
            if not results:
                raise SignatureNotFoundError(
                    f"No signature found for extension '.{extension}'"
                )
            
            return [(row["magic_bytes"], row["offset"]) for row in results]
            
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to query signatures for '.{extension}': {str(e)}"
            )
    
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
            DatabaseError: If signature cannot be added
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO signatures 
                (extension, magic_bytes, offset, description, mime_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (extension.lower(), magic_bytes.upper(), offset, description, mime_type)
            )
            self.conn.commit()
            
        except sqlite3.IntegrityError:
            raise DatabaseError(
                f"Signature for '.{extension}' at offset {offset} already exists"
            )
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to add signature for '.{extension}': {str(e)}"
            )
    
    def get_all_extensions(self) -> list[str]:
        """Get list of all supported extensions.
        
        Returns:
            List of file extensions (without dots) that have signatures
            
        Raises:
            DatabaseError: If query fails
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT extension FROM signatures ORDER BY extension")
            results = cursor.fetchall()
            return [row["extension"] for row in results]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve extensions: {str(e)}")
    
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
            return result["count"]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to count signatures: {str(e)}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close()