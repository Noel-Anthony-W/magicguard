"""Tests for file reader classes.

Tests cover:
- SimpleReader: basic file reading, signature validation
- ZipBasedReader: ZIP file reading, Office document validation
- PlainZipReader: plain ZIP archive validation
- ReaderFactory: reader selection based on file type
"""

from pathlib import Path
from unittest.mock import MagicMock
import zipfile

import pytest

from magicguard.core.readers import (
    SimpleReader,
    ZipBasedReader,
    PlainZipReader,
    ReaderFactory,
)
from magicguard.core.exceptions import FileReadError


class TestSimpleReader:
    """Test SimpleReader for basic file types."""
    
    @pytest.fixture
    def reader(self):
        """Provide SimpleReader instance."""
        return SimpleReader()
    
    def test_read_signature_from_file(self, reader, tmp_path):
        """Test reading signature bytes from file."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\nSome content")
        
        signature = reader.read_signature(str(test_file), length=4, offset=0)
        
        assert signature == b"%PDF"
    
    def test_read_signature_with_offset(self, reader, tmp_path):
        """Test reading signature at non-zero offset."""
        test_file = tmp_path / "test.tar"
        # TAR signature is at offset 257
        data = b"\x00" * 257 + b"ustar\x00"
        test_file.write_bytes(data)
        
        signature = reader.read_signature(str(test_file), length=5, offset=257)
        
        assert signature == b"ustar"
    
    def test_read_signature_full_length(self, reader, tmp_path):
        """Test reading complete signature."""
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        
        signature = reader.read_signature(str(test_file), length=8, offset=0)
        
        assert signature == b"\x89PNG\r\n\x1a\n"
    
    def test_read_signature_file_not_found(self, reader):
        """Test error when file doesn't exist."""
        with pytest.raises(FileReadError) as exc_info:
            reader.read_signature("/nonexistent/file.txt", length=4, offset=0)
        
        assert "Failed to read file" in str(exc_info.value)
    
    def test_read_signature_empty_file(self, reader, tmp_path):
        """Test reading from empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        signature = reader.read_signature(str(test_file), length=4, offset=0)
        
        assert signature == b""
    
    def test_read_signature_permission_error(self, reader, tmp_path):
        """Test IOError when file cannot be read due to permissions."""
        test_file = tmp_path / "noperm.txt"
        test_file.write_bytes(b"data")
        test_file.chmod(0o000)  # Remove all permissions
        
        try:
            with pytest.raises(FileReadError) as exc_info:
                reader.read_signature(str(test_file), length=4, offset=0)
            
            assert "Failed to read file" in str(exc_info.value)
        finally:
            test_file.chmod(0o644)  # Restore permissions for cleanup
    
    def test_supports_pdf(self, reader):
        """Test that SimpleReader supports PDF files."""
        assert reader.supports_file_type("pdf") is True
    
    def test_supports_image_formats(self, reader):
        """Test support for various image formats."""
        for ext in ["png", "jpg", "jpeg", "gif", "bmp", "ico", "webp"]:
            assert reader.supports_file_type(ext) is True
    
    def test_supports_media_formats(self, reader):
        """Test support for audio/video formats."""
        for ext in ["mp3", "mp4", "avi", "mkv", "wav", "flac"]:
            assert reader.supports_file_type(ext) is True
    
    def test_supports_archive_formats(self, reader):
        """Test support for archive formats."""
        for ext in ["rar", "7z", "tar", "gz"]:
            assert reader.supports_file_type(ext) is True
    
    def test_does_not_support_office_formats(self, reader):
        """Test that Office formats are not supported by SimpleReader."""
        for ext in ["docx", "xlsx", "pptx"]:
            assert reader.supports_file_type(ext) is False
    
    def test_does_not_support_zip(self, reader):
        """Test that ZIP is not supported by SimpleReader."""
        assert reader.supports_file_type("zip") is False
    
    def test_supports_case_insensitive(self, reader):
        """Test that extension matching is case insensitive."""
        assert reader.supports_file_type("PDF") is True
        assert reader.supports_file_type("Png") is True
        assert reader.supports_file_type("MP3") is True
    
    def test_validate_structure_returns_true(self, reader, tmp_path):
        """Test that structure validation always returns True for simple files."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4")
        
        result = reader.validate_structure(str(test_file), "pdf")
        
        assert result is True
    
    def test_custom_logger(self, tmp_path):
        """Test SimpleReader with custom logger."""
        mock_logger = MagicMock()
        reader = SimpleReader(logger=mock_logger)
        
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF")
        reader.read_signature(str(test_file), 4, 0)
        
        # Logger should have been called
        assert mock_logger.debug.called


class TestZipBasedReader:
    """Test ZipBasedReader for Office documents."""
    
    @pytest.fixture
    def reader(self):
        """Provide ZipBasedReader instance."""
        return ZipBasedReader()
    
    @pytest.fixture
    def valid_docx(self, tmp_path):
        """Create a valid DOCX file structure."""
        docx_file = tmp_path / "test.docx"
        with zipfile.ZipFile(docx_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
            zf.writestr('word/document.xml', '<?xml version="1.0"?>')
        return docx_file
    
    @pytest.fixture
    def valid_xlsx(self, tmp_path):
        """Create a valid XLSX file structure."""
        xlsx_file = tmp_path / "test.xlsx"
        with zipfile.ZipFile(xlsx_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
            zf.writestr('xl/workbook.xml', '<?xml version="1.0"?>')
        return xlsx_file
    
    @pytest.fixture
    def valid_pptx(self, tmp_path):
        """Create a valid PPTX file structure."""
        pptx_file = tmp_path / "test.pptx"
        with zipfile.ZipFile(pptx_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
            zf.writestr('ppt/presentation.xml', '<?xml version="1.0"?>')
        return pptx_file
    
    def test_read_signature(self, reader, valid_docx):
        """Test reading ZIP signature from Office document."""
        signature = reader.read_signature(str(valid_docx), length=4, offset=0)
        
        # ZIP files start with PK\x03\x04
        assert signature == b'PK\x03\x04'
    
    def test_supports_docx(self, reader):
        """Test that ZipBasedReader supports DOCX."""
        assert reader.supports_file_type("docx") is True
    
    def test_supports_xlsx(self, reader):
        """Test that ZipBasedReader supports XLSX."""
        assert reader.supports_file_type("xlsx") is True
    
    def test_supports_pptx(self, reader):
        """Test that ZipBasedReader supports PPTX."""
        assert reader.supports_file_type("pptx") is True
    
    def test_does_not_support_pdf(self, reader):
        """Test that PDF is not supported by ZipBasedReader."""
        assert reader.supports_file_type("pdf") is False
    
    def test_does_not_support_zip(self, reader):
        """Test that plain ZIP is not supported by ZipBasedReader."""
        assert reader.supports_file_type("zip") is False
    
    def test_validate_structure_docx_valid(self, reader, valid_docx):
        """Test validation of valid DOCX structure."""
        result = reader.validate_structure(str(valid_docx), "docx")
        
        assert result is True
    
    def test_validate_structure_xlsx_valid(self, reader, valid_xlsx):
        """Test validation of valid XLSX structure."""
        result = reader.validate_structure(str(valid_xlsx), "xlsx")
        
        assert result is True
    
    def test_validate_structure_pptx_valid(self, reader, valid_pptx):
        """Test validation of valid PPTX structure."""
        result = reader.validate_structure(str(valid_pptx), "pptx")
        
        assert result is True
    
    def test_validate_structure_docx_missing_content_types(self, reader, tmp_path):
        """Test validation fails when [Content_Types].xml is missing."""
        docx_file = tmp_path / "invalid.docx"
        with zipfile.ZipFile(docx_file, 'w') as zf:
            zf.writestr('word/document.xml', '<?xml version="1.0"?>')
        
        result = reader.validate_structure(str(docx_file), "docx")
        
        assert result is False
    
    def test_validate_structure_docx_missing_document_xml(self, reader, tmp_path):
        """Test validation fails when word/document.xml is missing."""
        docx_file = tmp_path / "invalid.docx"
        with zipfile.ZipFile(docx_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
        
        result = reader.validate_structure(str(docx_file), "docx")
        
        assert result is False
    
    def test_validate_structure_xlsx_missing_workbook(self, reader, tmp_path):
        """Test validation fails when xl/workbook.xml is missing."""
        xlsx_file = tmp_path / "invalid.xlsx"
        with zipfile.ZipFile(xlsx_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
        
        result = reader.validate_structure(str(xlsx_file), "xlsx")
        
        assert result is False
    
    def test_validate_structure_not_zip(self, reader, tmp_path):
        """Test validation fails for non-ZIP file."""
        fake_docx = tmp_path / "fake.docx"
        fake_docx.write_bytes(b"Not a ZIP file")
        
        result = reader.validate_structure(str(fake_docx), "docx")
        
        assert result is False
    
    def test_validate_structure_corrupted_zip(self, reader, tmp_path):
        """Test that corrupted ZIP returns False."""
        corrupted = tmp_path / "corrupted.docx"
        corrupted.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
        
        result = reader.validate_structure(str(corrupted), "docx")
        
        assert result is False
    
    def test_validate_structure_unknown_extension(self, reader, valid_docx):
        """Test validation returns False for unknown extension."""
        result = reader.validate_structure(str(valid_docx), "unknown")
        
        assert result is False
    
    def test_validate_structure_io_error(self, reader, tmp_path):
        """Test that permission errors during validation return False."""
        test_file = tmp_path / "noperm.docx"
        with zipfile.ZipFile(test_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
        test_file.chmod(0o000)  # Remove all permissions
        
        try:
            # Permission denied treated as invalid ZIP, returns False
            result = reader.validate_structure(str(test_file), "docx")
            assert result is False
        finally:
            test_file.chmod(0o644)  # Restore permissions


class TestPlainZipReader:
    """Test PlainZipReader for plain ZIP archives."""
    
    @pytest.fixture
    def reader(self):
        """Provide PlainZipReader instance."""
        return PlainZipReader()
    
    @pytest.fixture
    def valid_zip(self, tmp_path):
        """Create a valid ZIP file."""
        zip_file = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr('file1.txt', 'Content 1')
            zf.writestr('file2.txt', 'Content 2')
        return zip_file
    
    def test_read_signature(self, reader, valid_zip):
        """Test reading ZIP signature."""
        signature = reader.read_signature(str(valid_zip), length=4, offset=0)
        
        assert signature == b'PK\x03\x04'
    
    def test_supports_zip(self, reader):
        """Test that PlainZipReader supports ZIP."""
        assert reader.supports_file_type("zip") is True
    
    def test_supports_case_insensitive(self, reader):
        """Test case-insensitive extension matching."""
        assert reader.supports_file_type("ZIP") is True
        assert reader.supports_file_type("Zip") is True
    
    def test_does_not_support_office_formats(self, reader):
        """Test that Office formats are not supported."""
        for ext in ["docx", "xlsx", "pptx"]:
            assert reader.supports_file_type(ext) is False
    
    def test_does_not_support_other_formats(self, reader):
        """Test that other formats are not supported."""
        for ext in ["pdf", "png", "mp3"]:
            assert reader.supports_file_type(ext) is False
    
    def test_validate_structure_valid_zip(self, reader, valid_zip):
        """Test validation of valid ZIP file."""
        result = reader.validate_structure(str(valid_zip), "zip")
        
        assert result is True
    
    def test_validate_structure_invalid_zip(self, reader, tmp_path):
        """Test validation fails for non-ZIP file."""
        fake_zip = tmp_path / "fake.zip"
        fake_zip.write_bytes(b"Not a ZIP file")
        
        result = reader.validate_structure(str(fake_zip), "zip")
        
        assert result is False
    
    def test_validate_structure_empty_zip(self, reader, tmp_path):
        """Test validation of empty ZIP file."""
        empty_zip = tmp_path / "empty.zip"
        with zipfile.ZipFile(empty_zip, 'w'):
            pass  # Create empty ZIP
        
        result = reader.validate_structure(str(empty_zip), "zip")
        
        assert result is True
    
    def test_read_signature_permission_error(self, reader, tmp_path):
        """Test IOError when file cannot be read."""
        test_file = tmp_path / "noperm.zip"
        with zipfile.ZipFile(test_file, 'w') as zf:
            zf.writestr('test.txt', 'content')
        test_file.chmod(0o000)
        
        try:
            with pytest.raises(FileReadError) as exc_info:
                reader.read_signature(str(test_file), length=4, offset=0)
            
            assert "Failed to read file" in str(exc_info.value)
        finally:
            test_file.chmod(0o644)
    
    def test_validate_structure_io_error(self, reader, tmp_path):
        """Test that permission errors during validation return False."""
        test_file = tmp_path / "noperm.zip"
        with zipfile.ZipFile(test_file, 'w') as zf:
            zf.writestr('test.txt', 'content')
        test_file.chmod(0o000)
        
        try:
            # Permission denied treated as invalid ZIP, returns False
            result = reader.validate_structure(str(test_file), "zip")
            assert result is False
        finally:
            test_file.chmod(0o644)


class TestReaderFactory:
    """Test ReaderFactory for selecting appropriate readers."""
    
    @pytest.fixture
    def factory(self):
        """Provide ReaderFactory instance."""
        return ReaderFactory()
    
    def test_get_reader_for_pdf(self, factory):
        """Test factory returns SimpleReader for PDF."""
        reader = factory.get_reader("pdf")
        
        assert isinstance(reader, SimpleReader)
    
    def test_get_reader_for_png(self, factory):
        """Test factory returns SimpleReader for PNG."""
        reader = factory.get_reader("png")
        
        assert isinstance(reader, SimpleReader)
    
    def test_get_reader_for_docx(self, factory):
        """Test factory returns ZipBasedReader for DOCX."""
        reader = factory.get_reader("docx")
        
        assert isinstance(reader, ZipBasedReader)
    
    def test_get_reader_for_xlsx(self, factory):
        """Test factory returns ZipBasedReader for XLSX."""
        reader = factory.get_reader("xlsx")
        
        assert isinstance(reader, ZipBasedReader)
    
    def test_get_reader_for_pptx(self, factory):
        """Test factory returns ZipBasedReader for PPTX."""
        reader = factory.get_reader("pptx")
        
        assert isinstance(reader, ZipBasedReader)
    
    def test_get_reader_for_zip(self, factory):
        """Test factory returns PlainZipReader for ZIP."""
        reader = factory.get_reader("zip")
        
        assert isinstance(reader, PlainZipReader)
    
    def test_get_reader_case_insensitive(self, factory):
        """Test factory works with uppercase extensions."""
        reader_pdf = factory.get_reader("PDF")
        reader_docx = factory.get_reader("DOCX")
        reader_zip = factory.get_reader("ZIP")
        
        assert isinstance(reader_pdf, SimpleReader)
        assert isinstance(reader_docx, ZipBasedReader)
        assert isinstance(reader_zip, PlainZipReader)
    
    def test_get_reader_for_unknown_extension(self, factory):
        """Test factory returns SimpleReader as fallback."""
        reader = factory.get_reader("unknown_extension")
        
        assert isinstance(reader, SimpleReader)
    
    def test_get_reader_returns_same_type_for_same_extension(self, factory):
        """Test factory consistently returns same reader type."""
        reader1 = factory.get_reader("pdf")
        reader2 = factory.get_reader("pdf")
        
        assert type(reader1) == type(reader2)
    
    def test_factory_with_custom_logger(self):
        """Test factory with custom logger."""
        mock_logger = MagicMock()
        factory = ReaderFactory(logger=mock_logger)
        
        reader = factory.get_reader("pdf")
        
        assert mock_logger.debug.called
        assert isinstance(reader, SimpleReader)
    
    def test_reader_priority_zip_based_before_plain(self, factory):
        """Test that ZipBasedReader is checked before PlainZipReader."""
        # DOCX should match ZipBasedReader even though it's a ZIP
        reader = factory.get_reader("docx")
        
        assert isinstance(reader, ZipBasedReader)
        assert not isinstance(reader, PlainZipReader)
    
    def test_all_simple_file_types(self, factory):
        """Test factory returns SimpleReader for all simple file types."""
        simple_types = [
            'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'ico', 'webp',
            'mp3', 'mp4', 'avi', 'mkv', 'wav', 'flac',
            'exe', 'dll', 'elf', 'tar', 'gz', 'rar', '7z',
            'xml', 'html', 'json', 'sqlite', 'db'
        ]
        
        for ext in simple_types:
            reader = factory.get_reader(ext)
            assert isinstance(reader, SimpleReader), f"Failed for {ext}"


class TestReadersIntegration:
    """Integration tests for readers working together."""
    
    def test_read_and_validate_real_pdf(self, tmp_path):
        """Test reading and validating a real PDF structure."""
        factory = ReaderFactory()
        reader = factory.get_reader("pdf")
        
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
        
        signature = reader.read_signature(str(pdf_file), 4, 0)
        is_valid = reader.validate_structure(str(pdf_file), "pdf")
        
        assert signature == b"%PDF"
        assert is_valid is True
    
    def test_read_and_validate_real_docx(self, tmp_path):
        """Test reading and validating a real DOCX structure."""
        factory = ReaderFactory()
        reader = factory.get_reader("docx")
        
        docx_file = tmp_path / "test.docx"
        with zipfile.ZipFile(docx_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
            zf.writestr('word/document.xml', '<document/>')
            zf.writestr('word/_rels/document.xml.rels', '<Relationships/>')
        
        signature = reader.read_signature(str(docx_file), 4, 0)
        is_valid = reader.validate_structure(str(docx_file), "docx")
        
        assert signature == b'PK\x03\x04'
        assert is_valid is True
    
    def test_factory_selects_correct_reader_for_validation(self, tmp_path):
        """Test that factory selection leads to correct validation."""
        factory = ReaderFactory()
        
        # Create DOCX
        docx_file = tmp_path / "test.docx"
        with zipfile.ZipFile(docx_file, 'w') as zf:
            zf.writestr('[Content_Types].xml', '<?xml version="1.0"?>')
            zf.writestr('word/document.xml', '<document/>')
        
        # Create plain ZIP
        zip_file = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_file, 'w') as zf:
            zf.writestr('file.txt', 'content')
        
        # Factory should select appropriate readers
        docx_reader = factory.get_reader("docx")
        zip_reader = factory.get_reader("zip")
        
        assert isinstance(docx_reader, ZipBasedReader)
        assert isinstance(zip_reader, PlainZipReader)
        
        # Both should validate correctly
        assert docx_reader.validate_structure(str(docx_file), "docx") is True
        assert zip_reader.validate_structure(str(zip_file), "zip") is True
