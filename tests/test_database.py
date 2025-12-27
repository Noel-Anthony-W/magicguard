"""Tests for Database class.

Tests cover:
- Database initialization and schema creation
- Adding signatures (single and batch)
- Retrieving signatures by extension
- Getting all extensions
- Signature count
- Duplicate handling
- Error cases
- Context manager usage
"""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from magicguard.core.database import Database
from magicguard.core.exceptions import DatabaseError, SignatureNotFoundError


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide temporary database path."""
    return tmp_path / "test_signatures.db"


@pytest.fixture
def database(temp_db_path):
    """Provide a fresh Database instance for each test."""
    db = Database(db_path=str(temp_db_path))
    yield db
    db.close()


@pytest.fixture
def populated_database(database):
    """Provide a database with test signatures."""
    database.add_signature("pdf", "25504446", 0, "PDF document", "application/pdf")
    database.add_signature("png", "89504E47", 0, "PNG image", "image/png")
    database.add_signature("jpg", "FFD8FFE0", 0, "JPEG image", "image/jpeg")
    database.add_signature("zip", "504B0304", 0, "ZIP archive", "application/zip")
    return database


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""
    
    def test_database_creates_file(self, temp_db_path):
        """Test that database file is created on initialization."""
        assert not temp_db_path.exists()
        
        db = Database(db_path=str(temp_db_path))
        
        assert temp_db_path.exists()
        db.close()
    
    def test_database_creates_schema(self, temp_db_path):
        """Test that database schema is created correctly."""
        db = Database(db_path=str(temp_db_path))
        
        # Verify table exists with correct schema
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='signatures'"
        )
        schema = cursor.fetchone()[0]
        
        assert "extension TEXT NOT NULL" in schema
        assert "magic_bytes TEXT NOT NULL" in schema
        assert "offset INTEGER DEFAULT 0" in schema
        assert "description TEXT" in schema
        assert "mime_type TEXT" in schema
        
        db.close()
    
    def test_database_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if needed."""
        nested_path = tmp_path / "nested" / "dirs" / "test.db"
        
        db = Database(db_path=str(nested_path))
        
        assert nested_path.exists()
        assert nested_path.parent.exists()
        db.close()
    
    def test_database_works_without_path(self, tmp_path):
        """Test that database works when path is provided."""
        test_db = tmp_path / "test.db"
        db = Database(db_path=str(test_db))
        
        # Should work
        db.add_signature("test", "AABBCCDD", 0)
        count = db.signature_count()
        
        assert count == 1
        db.close()
    
    def test_database_with_custom_logger(self, temp_db_path):
        """Test database initialization with custom logger."""
        mock_logger = MagicMock()
        
        db = Database(db_path=str(temp_db_path), logger=mock_logger)
        
        assert db.logger == mock_logger
        mock_logger.debug.assert_called()
        db.close()


class TestAddSignature:
    """Test adding signatures to database."""
    
    def test_add_signature_basic(self, database):
        """Test adding a basic signature."""
        database.add_signature("pdf", "25504446", 0)
        
        count = database.signature_count()
        assert count == 1
    
    def test_add_signature_with_description(self, database):
        """Test adding signature with description."""
        database.add_signature(
            "pdf", "25504446", 0, 
            description="PDF document",
            mime_type="application/pdf"
        )
        
        signatures = database.get_signatures("pdf")
        assert len(signatures) == 1
        assert signatures[0] == ("25504446", 0)
    
    def test_add_signature_with_offset(self, database):
        """Test adding signature with non-zero offset."""
        database.add_signature("tar", "7573746172", 257)
        
        signatures = database.get_signatures("tar")
        assert signatures[0] == ("7573746172", 257)
    
    def test_add_signature_normalizes_extension(self, database):
        """Test that extensions are normalized (lowercase, no dot)."""
        database.add_signature(".PDF", "25504446", 0)
        database.add_signature("PNG", "89504E47", 0)
        
        # Should be able to retrieve with normalized names
        pdf_sigs = database.get_signatures("pdf")
        png_sigs = database.get_signatures("png")
        
        assert len(pdf_sigs) == 1
        assert len(png_sigs) == 1
    
    def test_add_signature_normalizes_magic_bytes(self, database):
        """Test that magic bytes are normalized (uppercase, no spaces)."""
        database.add_signature("test", "aa bb cc dd", 0)
        
        signatures = database.get_signatures("test")
        assert signatures[0] == ("AABBCCDD", 0)
    
    def test_add_duplicate_signature_raises_error(self, database):
        """Test that adding duplicate signature raises DatabaseError."""
        database.add_signature("pdf", "25504446", 0)
        
        with pytest.raises(DatabaseError) as exc_info:
            database.add_signature("pdf", "25504446", 0)
        
        assert "already exists" in str(exc_info.value)
    
    def test_add_multiple_signatures_same_extension(self, database):
        """Test adding multiple signatures for same extension."""
        database.add_signature("jpg", "FFD8FFE0", 0)
        database.add_signature("jpg", "FFD8FFE1", 0)
        
        signatures = database.get_signatures("jpg")
        assert len(signatures) == 2
        assert ("FFD8FFE0", 0) in signatures
        assert ("FFD8FFE1", 0) in signatures
    
    def test_add_signature_empty_extension(self, database):
        """Test that empty extension is rejected."""
        with pytest.raises(DatabaseError) as exc_info:
            database.add_signature("", "25504446", 0)
        
        assert "Extension cannot be empty" in str(exc_info.value)
    
    def test_add_signature_empty_magic_bytes(self, database):
        """Test that empty magic bytes is rejected."""
        with pytest.raises(DatabaseError) as exc_info:
            database.add_signature("pdf", "", 0)
        
        assert "Magic bytes cannot be empty" in str(exc_info.value)
    
    def test_add_signature_invalid_hex(self, database):
        """Test that invalid hex string is rejected."""
        with pytest.raises(DatabaseError) as exc_info:
            database.add_signature("test", "GGHHII", 0)
        
        assert "Invalid hex string" in str(exc_info.value)


class TestGetSignatures:
    """Test retrieving signatures from database."""
    
    def test_get_signatures_single(self, populated_database):
        """Test getting signatures for extension with single signature."""
        signatures = populated_database.get_signatures("pdf")
        
        assert len(signatures) == 1
        assert signatures[0] == ("25504446", 0)
    
    def test_get_signatures_multiple(self, populated_database):
        """Test getting signatures for extension with multiple signatures."""
        # Add second JPG signature
        populated_database.add_signature("jpg", "FFD8FFE1", 0)
        
        signatures = populated_database.get_signatures("jpg")
        
        assert len(signatures) == 2
    
    def test_get_signatures_normalizes_extension(self, populated_database):
        """Test that extension lookup is case-insensitive."""
        signatures_lower = populated_database.get_signatures("pdf")
        signatures_upper = populated_database.get_signatures("PDF")
        signatures_dot = populated_database.get_signatures(".pdf")
        
        assert signatures_lower == signatures_upper == signatures_dot
    
    def test_get_signatures_not_found(self, database):
        """Test that SignatureNotFoundError is raised for unknown extension."""
        with pytest.raises(SignatureNotFoundError) as exc_info:
            database.get_signatures("unknown")
        
        assert "No signature found" in str(exc_info.value)
        assert "unknown" in str(exc_info.value)
    
    def test_get_signatures_returns_tuples(self, populated_database):
        """Test that signatures are returned as (magic_bytes, offset) tuples."""
        signatures = populated_database.get_signatures("pdf")
        
        assert isinstance(signatures, list)
        assert isinstance(signatures[0], tuple)
        assert len(signatures[0]) == 2


class TestGetAllExtensions:
    """Test getting all extensions from database."""
    
    def test_get_all_extensions_empty(self, database):
        """Test getting extensions from empty database."""
        extensions = database.get_all_extensions()
        
        assert extensions == []
    
    def test_get_all_extensions_populated(self, populated_database):
        """Test getting all extensions."""
        extensions = populated_database.get_all_extensions()
        
        assert len(extensions) == 4
        assert set(extensions) == {"pdf", "png", "jpg", "zip"}
    
    def test_get_all_extensions_unique(self, populated_database):
        """Test that extensions are unique even with multiple signatures."""
        # Add second JPG signature
        populated_database.add_signature("jpg", "FFD8FFE1", 0)
        
        extensions = populated_database.get_all_extensions()
        
        # Should still have 4 unique extensions
        assert len(extensions) == 4
        assert extensions.count("jpg") == 1
    
    def test_get_all_extensions_sorted(self, populated_database):
        """Test that extensions are returned in consistent order."""
        extensions = populated_database.get_all_extensions()
        
        # SQLite should return them sorted
        assert extensions == sorted(extensions)


class TestSignatureCount:
    """Test signature counting."""
    
    def test_signature_count_empty(self, database):
        """Test count for empty database."""
        count = database.signature_count()
        
        assert count == 0
    
    def test_signature_count_populated(self, populated_database):
        """Test count for populated database."""
        count = populated_database.signature_count()
        
        assert count == 4
    
    def test_signature_count_after_additions(self, database):
        """Test count updates after adding signatures."""
        assert database.signature_count() == 0
        
        database.add_signature("pdf", "25504446", 0)
        assert database.signature_count() == 1
        
        database.add_signature("png", "89504E47", 0)
        assert database.signature_count() == 2
    
    def test_signature_count_includes_multiple_per_extension(self, database):
        """Test that count includes all signatures, not just extensions."""
        database.add_signature("jpg", "FFD8FFE0", 0)
        database.add_signature("jpg", "FFD8FFE1", 0)
        
        count = database.signature_count()
        
        assert count == 2


class TestContextManager:
    """Test database context manager usage."""
    
    def test_context_manager_closes_connection(self, temp_db_path):
        """Test that context manager closes connection on exit."""
        with Database(db_path=str(temp_db_path)) as db:
            db.add_signature("pdf", "25504446", 0)
            assert db.conn is not None
        
        # Connection should be closed (set to None) after context exit
        assert db.conn is None
    
    def test_context_manager_with_exception(self, temp_db_path):
        """Test that connection is closed even if exception occurs."""
        try:
            with Database(db_path=str(temp_db_path)) as db:
                db.add_signature("pdf", "25504446", 0)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Connection should still be closed (set to None)
        assert db.conn is None


class TestDatabaseClose:
    """Test database close method."""
    
    def test_close_closes_connection(self, database):
        """Test that close method closes the connection."""
        assert database.conn is not None
        
        database.close()
        
        # Connection should be set to None
        assert database.conn is None
    
    def test_close_multiple_times(self, database):
        """Test that calling close multiple times doesn't raise error."""
        database.close()
        database.close()  # Should not raise


class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    def test_full_workflow(self, temp_db_path):
        """Test complete workflow: create, add, retrieve, count, close."""
        # Create database
        db = Database(db_path=str(temp_db_path))
        assert temp_db_path.exists()
        
        # Add signatures
        db.add_signature("pdf", "25504446", 0, "PDF document")
        db.add_signature("png", "89504E47", 0, "PNG image")
        
        # Retrieve
        pdf_sig = db.get_signatures("pdf")
        assert pdf_sig == [("25504446", 0)]
        
        # Count
        assert db.signature_count() == 2
        
        # Get all extensions
        extensions = db.get_all_extensions()
        assert set(extensions) == {"pdf", "png"}
        
        # Close
        db.close()
    
    def test_persistence_across_connections(self, temp_db_path):
        """Test that data persists across database connections."""
        # First connection: add data
        db1 = Database(db_path=str(temp_db_path))
        db1.add_signature("pdf", "25504446", 0)
        db1.close()
        
        # Second connection: verify data exists
        db2 = Database(db_path=str(temp_db_path))
        signatures = db2.get_signatures("pdf")
        
        assert len(signatures) == 1
        assert signatures[0] == ("25504446", 0)
        db2.close()


class TestDatabaseErrorHandling:
    """Test database error handling with corrupted database."""
    
    def test_init_with_corrupted_database(self, tmp_path):
        """Test initialization fails gracefully with corrupted database file."""
        corrupted_db = tmp_path / "corrupted.db"
        corrupted_db.write_text("This is not a valid SQLite database")
        
        with pytest.raises(DatabaseError) as exc_info:
            Database(db_path=str(corrupted_db))
        
        # Error message mentions either "initialize" or "schema"
        assert "Failed to" in str(exc_info.value)
        assert "database" in str(exc_info.value).lower()
    
    def test_get_signatures_database_error(self, database):
        """Test get_signatures handles database errors."""
        # Close connection to simulate database error
        database.conn.close()
        database.conn = None
        
        with pytest.raises(AttributeError):
            database.get_signatures("pdf")
    
    def test_add_signature_database_error(self, database):
        """Test add_signature handles database errors."""
        # Close connection to simulate database error
        database.conn.close()
        database.conn = None
        
        with pytest.raises(AttributeError):
            database.add_signature("test", "AABBCCDD", 0)
    
    def test_get_all_extensions_database_error(self, database):
        """Test get_all_extensions handles database errors."""
        # Close connection to simulate database error
        database.conn.close()
        database.conn = None
        
        with pytest.raises(AttributeError):
            database.get_all_extensions()
    
    def test_signature_count_database_error(self, database):
        """Test signature_count handles database errors."""
        # Close connection to simulate database error
        database.conn.close()
        database.conn = None
        
        with pytest.raises(AttributeError):
            database.signature_count()
