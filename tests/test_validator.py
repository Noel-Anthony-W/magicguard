"""Tests for FileValidator class.

Tests cover:
- File validation with different file types
- Magic bytes verification
- Structure validation integration
- Error handling (file not found, invalid files, etc.)
- Hash calculation
- Integration with Database and ReaderFactory
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import zipfile

import pytest

from magicguard.core.validator import FileValidator
from magicguard.core.database import Database
from magicguard.core.readers import ReaderFactory
from magicguard.core.exceptions import (
    FileReadError,
    ValidationError,
    SignatureNotFoundError,
)


class TestFileValidatorInitialization:
    """Test FileValidator initialization and dependency injection."""
    
    def test_init_with_dependencies(self, tmp_path):
        """Test initialization with provided dependencies."""
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        database.add_signature("pdf", "25504446", 0)
        
        factory = ReaderFactory()
        
        validator = FileValidator(database=database, reader_factory=factory)
        
        assert validator.database is database
        assert validator.reader_factory is factory
        database.close()
    
    def test_init_creates_default_database(self):
        """Test that default Database is created if not provided."""
        validator = FileValidator()
        
        try:
            assert validator.database is not None
            assert hasattr(validator.database, 'get_signatures')
        finally:
            validator.close()
    
    def test_init_creates_default_reader_factory(self):
        """Test that default ReaderFactory is created if not provided."""
        validator = FileValidator()
        
        try:
            assert validator.reader_factory is not None
            assert hasattr(validator.reader_factory, 'get_reader')
        finally:
            validator.close()
    
    def test_init_with_custom_logger(self, tmp_path):
        """Test initialization with custom logger."""
        mock_logger = MagicMock()
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        
        validator = FileValidator(database=database, logger=mock_logger)
        
        assert validator.logger == mock_logger
        database.close()


class TestFileValidation:
    """Test file validation functionality."""
    
    @pytest.fixture
    def populated_db(self, tmp_path):
        """Provide database with test signatures."""
        db = Database(db_path=str(tmp_path / "test.db"))
        db.add_signature("pdf", "25504446", 0, "PDF document")
        db.add_signature("png", "89504E47", 0, "PNG image")
        db.add_signature("jpg", "FFD8FFE0", 0, "JPEG image")
        db.add_signature("jpg", "FFD8FFE1", 0, "JPEG image variant")
        db.add_signature("docx", "504B0304", 0, "DOCX document")
        return db
    
    @pytest.fixture
    def validator(self, populated_db):
        """Provide validator with populated database."""
        factory = ReaderFactory()
        v = FileValidator(database=populated_db, reader_factory=factory)
        yield v
        v.close()
    
    def test_validate_valid_pdf(self, validator, tmp_path):
        """Test validation of valid PDF file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")
        
        result = validator.validate(str(pdf_file))
        
        assert result is True
    
    def test_validate_valid_png(self, validator, tmp_path):
        """Test validation of valid PNG file."""
        png_file = tmp_path / "test.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        
        result = validator.validate(str(png_file))
        
        assert result is True
    
    def test_validate_valid_jpg(self, validator, tmp_path):
        """Test validation of valid JPEG file."""
        jpg_file = tmp_path / "test.jpg"
        jpg_file.write_bytes(b"\xFF\xD8\xFF\xE0")
        
        result = validator.validate(str(jpg_file))
        
        assert result is True
    
    def test_validate_jpg_variant(self, validator, tmp_path):
        """Test validation with multiple signatures for same extension."""
        jpg_file = tmp_path / "test.jpg"
        jpg_file.write_bytes(b"\xFF\xD8\xFF\xE1")  # Second variant
        
        result = validator.validate(str(jpg_file))
        
        assert result is True
    
    def test_validate_valid_docx(self, validator, tmp_path):
        """Test validation of valid DOCX file."""
        docx_file = tmp_path / "test.docx"
        with zipfile.ZipFile(docx_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
            zf.writestr('word/document.xml', '<document/>')
        
        result = validator.validate(str(docx_file))
        
        assert result is True
    
    def test_validate_spoofed_pdf(self, validator, tmp_path):
        """Test detection of spoofed PDF (PNG with .pdf extension)."""
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"\x89PNG\r\n\x1a\n")
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(str(fake_pdf))
        
        assert "magic bytes don't match" in str(exc_info.value)
        assert "pdf" in str(exc_info.value).lower()
    
    def test_validate_spoofed_png(self, validator, tmp_path):
        """Test detection of spoofed PNG (PDF with .png extension)."""
        fake_png = tmp_path / "fake.png"
        fake_png.write_bytes(b"%PDF-1.4")
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(str(fake_png))
        
        assert "89504E47" in str(exc_info.value)  # Expected PNG signature
    
    def test_validate_file_not_found(self, validator):
        """Test error when file doesn't exist."""
        with pytest.raises(FileReadError) as exc_info:
            validator.validate("/nonexistent/file.pdf")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_validate_not_a_file(self, validator, tmp_path):
        """Test error when path is a directory."""
        directory = tmp_path / "testdir"
        directory.mkdir()
        
        with pytest.raises(FileReadError) as exc_info:
            validator.validate(str(directory))
        
        assert "not a file" in str(exc_info.value).lower()
    
    def test_validate_file_too_large(self, validator, tmp_path):
        """Test error when file exceeds maximum size."""
        large_file = tmp_path / "large.pdf"
        # Create file larger than 100MB (MAX_FILE_SIZE)
        large_file.write_bytes(b"%PDF" + b"\x00" * (100 * 1024 * 1024 + 1))
        
        with pytest.raises(FileReadError) as exc_info:
            validator.validate(str(large_file))
        
        assert "too large" in str(exc_info.value).lower()
    
    def test_validate_file_no_extension(self, validator, tmp_path):
        """Test error when file has no extension."""
        no_ext = tmp_path / "noextension"
        no_ext.write_bytes(b"%PDF-1.4")
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(str(no_ext))
        
        assert "no extension" in str(exc_info.value).lower()
    
    def test_validate_unknown_extension(self, validator, tmp_path):
        """Test error when extension not in database."""
        unknown = tmp_path / "test.unknown"
        unknown.write_bytes(b"Some data")
        
        with pytest.raises(SignatureNotFoundError) as exc_info:
            validator.validate(str(unknown))
        
        assert "unknown" in str(exc_info.value)
    
    def test_validate_docx_with_wrong_structure(self, validator, tmp_path):
        """Test that DOCX with correct magic but wrong structure fails."""
        fake_docx = tmp_path / "fake.docx"
        # Valid ZIP but not a DOCX
        with zipfile.ZipFile(fake_docx, 'w') as zf:
            zf.writestr('random.txt', 'content')
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(str(fake_docx))
        
        assert "failed internal structure validation" in str(exc_info.value)


class TestGetFileHash:
    """Test SHA-256 hash calculation."""
    
    @pytest.fixture
    def validator(self, tmp_path):
        """Provide validator instance."""
        db = Database(db_path=str(tmp_path / "test.db"))
        v = FileValidator(database=db)
        yield v
        v.close()
    
    def test_hash_simple_file(self, validator, tmp_path):
        """Test hash calculation for simple file."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Hello, World!")
        
        file_hash = validator.get_file_hash(str(test_file))
        
        # SHA-256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert file_hash == expected
    
    def test_hash_empty_file(self, validator, tmp_path):
        """Test hash calculation for empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        
        file_hash = validator.get_file_hash(str(empty_file))
        
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert file_hash == expected
    
    def test_hash_binary_file(self, validator, tmp_path):
        """Test hash calculation for binary file."""
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\xFF\xFE")
        
        file_hash = validator.get_file_hash(str(binary_file))
        
        assert len(file_hash) == 64  # SHA-256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in file_hash)
    
    def test_hash_large_file(self, validator, tmp_path):
        """Test hash calculation for larger file (chunked reading)."""
        large_file = tmp_path / "large.txt"
        # Write 1MB of data
        data = b"A" * (1024 * 1024)
        large_file.write_bytes(data)
        
        file_hash = validator.get_file_hash(str(large_file))
        
        assert len(file_hash) == 64
    
    def test_hash_file_not_found(self, validator):
        """Test error when file doesn't exist."""
        with pytest.raises(FileReadError) as exc_info:
            validator.get_file_hash("/nonexistent/file.txt")
        
        assert "Failed to hash file" in str(exc_info.value)
    
    def test_hash_consistency(self, validator, tmp_path):
        """Test that same file produces same hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Consistent data")
        
        hash1 = validator.get_file_hash(str(test_file))
        hash2 = validator.get_file_hash(str(test_file))
        
        assert hash1 == hash2


class TestValidatorContextManager:
    """Test context manager functionality."""
    
    def test_context_manager_closes_database(self, tmp_path):
        """Test that context manager closes database."""
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        
        with FileValidator(database=database) as validator:
            assert validator.database.conn is not None
        
        # Database should be closed
        assert validator.database.conn is None
    
    def test_context_manager_with_exception(self, tmp_path):
        """Test that database closes even if exception occurs."""
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        
        try:
            with FileValidator(database=database) as validator:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Database should still be closed
        assert validator.database.conn is None


class TestValidatorClose:
    """Test close method."""
    
    def test_close_closes_database(self, tmp_path):
        """Test that close method closes database connection."""
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        validator = FileValidator(database=database)
        
        assert validator.database.conn is not None
        
        validator.close()
        
        assert validator.database.conn is None
    
    def test_close_multiple_times(self, tmp_path):
        """Test that calling close multiple times doesn't raise error."""
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        validator = FileValidator(database=database)
        
        validator.close()
        validator.close()  # Should not raise


class TestValidatorIntegration:
    """Integration tests for validator with real components."""
    
    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow."""
        # Setup
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        database.add_signature("pdf", "25504446", 0)
        
        validator = FileValidator(database=database)
        
        # Create test file
        pdf_file = tmp_path / "document.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nContent here")
        
        # Validate
        result = validator.validate(str(pdf_file))
        
        # Get hash
        file_hash = validator.get_file_hash(str(pdf_file))
        
        assert result is True
        assert len(file_hash) == 64
        
        validator.close()
    
    def test_validation_with_multiple_file_types(self, tmp_path):
        """Test validating different file types in sequence."""
        # Setup database with multiple signatures
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        database.add_signature("pdf", "25504446", 0)
        database.add_signature("png", "89504E47", 0)
        database.add_signature("jpg", "FFD8FFE0", 0)
        
        validator = FileValidator(database=database)
        
        # Create test files
        pdf_file = tmp_path / "doc.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        
        png_file = tmp_path / "img.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        
        jpg_file = tmp_path / "photo.jpg"
        jpg_file.write_bytes(b"\xFF\xD8\xFF\xE0")
        
        # Validate all
        assert validator.validate(str(pdf_file)) is True
        assert validator.validate(str(png_file)) is True
        assert validator.validate(str(jpg_file)) is True
        
        validator.close()
    
    def test_detect_multiple_spoofed_files(self, tmp_path):
        """Test detection of multiple spoofed files."""
        db_path = tmp_path / "test.db"
        database = Database(db_path=str(db_path))
        database.add_signature("pdf", "25504446", 0)
        database.add_signature("png", "89504E47", 0)
        
        validator = FileValidator(database=database)
        
        # Create spoofed files
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"\x89PNG\r\n\x1a\n")
        
        fake_png = tmp_path / "fake.png"
        fake_png.write_bytes(b"%PDF-1.4")
        
        # Both should fail validation
        with pytest.raises(ValidationError):
            validator.validate(str(fake_pdf))
        
        with pytest.raises(ValidationError):
            validator.validate(str(fake_png))
        
        validator.close()
