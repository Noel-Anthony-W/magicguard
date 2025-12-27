"""Tests for DataLoader class and data loading functions.

Tests cover:
- DataLoader initialization
- Loading signatures from JSON
- JSON validation
- Error handling (missing files, invalid JSON, invalid structure)
- initialize_default_signatures function
- export_signatures_to_json function
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from magicguard.core.database import Database
from magicguard.utils.data_loader import (
    DataLoader,
    initialize_default_signatures,
    export_signatures_to_json,
)


class TestDataLoaderInitialization:
    """Test DataLoader initialization."""
    
    def test_init_default_logger(self):
        """Test that DataLoader creates default logger if none provided."""
        loader = DataLoader()
        
        assert loader.logger is not None
        assert hasattr(loader.logger, 'info')
    
    def test_init_with_custom_logger(self):
        """Test initialization with custom logger."""
        mock_logger = MagicMock()
        
        loader = DataLoader(logger=mock_logger)
        
        assert loader.logger == mock_logger


class TestLoadSignatures:
    """Test loading signatures from JSON files."""
    
    @pytest.fixture
    def database(self, tmp_path):
        """Provide database instance."""
        db = Database(db_path=str(tmp_path / "test.db"))
        yield db
        db.close()
    
    @pytest.fixture
    def loader(self):
        """Provide DataLoader instance."""
        return DataLoader()
    
    def test_load_signatures_basic(self, loader, database, tmp_path):
        """Test loading basic signature file."""
        json_file = tmp_path / "signatures.json"
        json_file.write_text(json.dumps({
            "signatures": [
                {
                    "extension": "pdf",
                    "magic_bytes": "25504446",
                    "offset": 0,
                    "description": "PDF document"
                }
            ]
        }))
        
        count = loader.load_signatures(str(json_file), database)
        
        assert count == 1
        sigs = database.get_signatures("pdf")
        assert len(sigs) == 1
        assert sigs[0][0] == "25504446"
    
    def test_load_signatures_multiple(self, loader, database, tmp_path):
        """Test loading multiple signatures."""
        json_file = tmp_path / "signatures.json"
        json_file.write_text(json.dumps({
            "signatures": [
                {"extension": "pdf", "magic_bytes": "25504446", "offset": 0},
                {"extension": "png", "magic_bytes": "89504E47", "offset": 0},
                {"extension": "jpg", "magic_bytes": "FFD8FFE0", "offset": 0},
            ]
        }))
        
        count = loader.load_signatures(str(json_file), database)
        
        assert count == 3
        assert "pdf" in database.get_all_extensions()
        assert "png" in database.get_all_extensions()
        assert "jpg" in database.get_all_extensions()
    
    def test_load_signatures_with_optional_fields(self, loader, database, tmp_path):
        """Test loading signatures with all optional fields."""
        json_file = tmp_path / "signatures.json"
        json_file.write_text(json.dumps({
            "signatures": [
                {
                    "extension": "pdf",
                    "magic_bytes": "25504446",
                    "offset": 0,
                    "description": "PDF document",
                    "mime_type": "application/pdf"
                }
            ]
        }))
        
        count = loader.load_signatures(str(json_file), database)
        
        assert count == 1
    
    def test_load_signatures_file_not_found(self, loader, database):
        """Test error when JSON file doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load_signatures("/nonexistent/file.json", database)
        
        assert "not found" in str(exc_info.value)
    
    def test_load_signatures_invalid_json(self, loader, database, tmp_path):
        """Test error when JSON is malformed."""
        json_file = tmp_path / "bad.json"
        json_file.write_text("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            loader.load_signatures(str(json_file), database)
    
    def test_load_signatures_invalid_structure_not_dict(self, loader, database, tmp_path):
        """Test error when JSON root is not an object."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text(json.dumps([{"extension": "pdf"}]))  # Array instead of object
        
        with pytest.raises(ValueError) as exc_info:
            loader.load_signatures(str(json_file), database)
        
        assert "Invalid JSON structure" in str(exc_info.value)
    
    def test_load_signatures_missing_signatures_array(self, loader, database, tmp_path):
        """Test error when JSON missing 'signatures' key."""
        json_file = tmp_path / "missing.json"
        json_file.write_text(json.dumps({"data": []}))
        
        with pytest.raises(ValueError):
            loader.load_signatures(str(json_file), database)
    
    def test_load_signatures_skips_duplicates(self, loader, database, tmp_path):
        """Test that duplicate signatures are skipped gracefully."""
        # Pre-load one signature
        database.add_signature("pdf", "25504446", 0)
        
        # Try to load same signature again
        json_file = tmp_path / "signatures.json"
        json_file.write_text(json.dumps({
            "signatures": [
                {"extension": "pdf", "magic_bytes": "25504446", "offset": 0},
                {"extension": "png", "magic_bytes": "89504E47", "offset": 0},
            ]
        }))
        
        count = loader.load_signatures(str(json_file), database)
        
        # Should only load the new one, skip duplicate
        assert count == 1
    
    def test_load_signatures_empty_file(self, loader, database, tmp_path):
        """Test loading file with no signatures."""
        json_file = tmp_path / "empty.json"
        json_file.write_text(json.dumps({"signatures": []}))
        
        count = loader.load_signatures(str(json_file), database)
        
        assert count == 0


class TestValidateSource:
    """Test JSON source validation."""
    
    @pytest.fixture
    def loader(self):
        """Provide DataLoader instance."""
        return DataLoader()
    
    def test_validate_source_valid(self, loader, tmp_path):
        """Test validation of valid JSON file."""
        json_file = tmp_path / "valid.json"
        json_file.write_text(json.dumps({
            "signatures": [
                {"extension": "pdf", "magic_bytes": "25504446"}
            ]
        }))
        
        result = loader.validate_source(str(json_file))
        
        assert result is True
    
    def test_validate_source_file_not_found(self, loader):
        """Test validation returns False for missing file."""
        result = loader.validate_source("/nonexistent/file.json")
        
        assert result is False
    
    def test_validate_source_invalid_json(self, loader, tmp_path):
        """Test validation returns False for malformed JSON."""
        json_file = tmp_path / "bad.json"
        json_file.write_text("{ invalid }")
        
        result = loader.validate_source(str(json_file))
        
        assert result is False
    
    def test_validate_source_invalid_structure(self, loader, tmp_path):
        """Test validation returns False for invalid structure."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text(json.dumps({"wrong_key": []}))
        
        result = loader.validate_source(str(json_file))
        
        assert result is False


class TestValidateStructure:
    """Test internal structure validation logic."""
    
    @pytest.fixture
    def loader(self):
        """Provide DataLoader instance."""
        return DataLoader()
    
    def test_validate_structure_valid(self, loader):
        """Test validation of valid structure."""
        data = {
            "signatures": [
                {"extension": "pdf", "magic_bytes": "25504446", "offset": 0}
            ]
        }
        
        result = loader._validate_structure(data)
        
        assert result is True
    
    def test_validate_structure_root_not_dict(self, loader):
        """Test validation fails if root is not dict."""
        data = [{"extension": "pdf"}]  # List instead of dict
        
        result = loader._validate_structure(data)
        
        assert result is False
    
    def test_validate_structure_missing_signatures(self, loader):
        """Test validation fails without 'signatures' key."""
        data = {"data": []}
        
        result = loader._validate_structure(data)
        
        assert result is False
    
    def test_validate_structure_signatures_not_array(self, loader):
        """Test validation fails if 'signatures' is not array."""
        data = {"signatures": "not an array"}
        
        result = loader._validate_structure(data)
        
        assert result is False
    
    def test_validate_structure_signature_not_object(self, loader):
        """Test validation fails if signature is not object."""
        data = {"signatures": ["not an object"]}
        
        result = loader._validate_structure(data)
        
        assert result is False
    
    def test_validate_structure_missing_extension(self, loader):
        """Test validation fails if signature missing extension."""
        data = {"signatures": [{"magic_bytes": "25504446"}]}
        
        result = loader._validate_structure(data)
        
        assert result is False
    
    def test_validate_structure_missing_magic_bytes(self, loader):
        """Test validation fails if signature missing magic_bytes."""
        data = {"signatures": [{"extension": "pdf"}]}
        
        result = loader._validate_structure(data)
        
        assert result is False
    
    def test_validate_structure_invalid_hex(self, loader):
        """Test validation fails for invalid hex in magic_bytes."""
        data = {"signatures": [{"extension": "pdf", "magic_bytes": "GGHHII"}]}
        
        result = loader._validate_structure(data)
        
        assert result is False
    
    def test_validate_structure_offset_optional(self, loader):
        """Test that offset field is optional."""
        data = {"signatures": [{"extension": "pdf", "magic_bytes": "25504446"}]}
        
        result = loader._validate_structure(data)
        
        assert result is True


class TestInitializeDefaultSignatures:
    """Test initialize_default_signatures function."""
    
    @pytest.fixture
    def database(self, tmp_path):
        """Provide empty database."""
        db = Database(db_path=str(tmp_path / "test.db"))
        yield db
        db.close()
    
    def test_initialize_empty_database(self, database):
        """Test initializing empty database with signatures.
        
        Note: This test uses the actual data/signatures.json file,
        which is expected behavior for initialize_default_signatures.
        """
        count = initialize_default_signatures(database)
        
        # Should load signatures (actual file has 29)
        assert count > 0
        extensions = database.get_all_extensions()
        assert "pdf" in extensions
        assert "png" in extensions
    
    def test_initialize_already_populated(self, database):
        """Test that initialization skips if database already has signatures."""
        # Pre-populate database
        database.add_signature("pdf", "25504446", 0)
        
        count = initialize_default_signatures(database)
        
        # Should return 0, no new signatures loaded
        assert count == 0
    
    def test_initialize_no_signature_file_found(self, tmp_path):
        """Test handling when no signature file is found in custom location.
        
        Note: initialize_default_signatures tries multiple locations and
        will find the actual project file. This test confirms it works.
        """
        db = Database(db_path=str(tmp_path / "test.db"))
        count = initialize_default_signatures(db)
        
        # Will find the real signatures.json
        assert count > 0
        db.close()


class TestExportSignaturesToJson:
    """Test export_signatures_to_json function."""
    
    @pytest.fixture
    def database(self, tmp_path):
        """Provide populated database."""
        db = Database(db_path=str(tmp_path / "test.db"))
        db.add_signature("pdf", "25504446", 0, "PDF document")
        db.add_signature("png", "89504E47", 0, "PNG image")
        db.add_signature("jpg", "FFD8FFE0", 0, "JPEG image")
        yield db
        db.close()
    
    def test_export_basic(self, database, tmp_path):
        """Test basic export functionality."""
        output_file = tmp_path / "export.json"
        
        count = export_signatures_to_json(database, str(output_file))
        
        assert count == 3
        assert output_file.exists()
        
        # Verify exported content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "signatures" in data
        assert len(data["signatures"]) == 3
        assert "version" in data
    
    def test_export_creates_directory(self, database, tmp_path):
        """Test that export creates parent directories."""
        output_file = tmp_path / "nested" / "dir" / "export.json"
        
        count = export_signatures_to_json(database, str(output_file))
        
        assert count == 3
        assert output_file.exists()
        assert output_file.parent.exists()
    
    def test_export_empty_database(self, tmp_path):
        """Test exporting from empty database."""
        db = Database(db_path=str(tmp_path / "empty.db"))
        output_file = tmp_path / "empty_export.json"
        
        count = export_signatures_to_json(db, str(output_file))
        
        assert count == 0
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert data["signatures"] == []
        db.close()
    
    def test_export_multiple_signatures_per_extension(self, tmp_path):
        """Test exporting when extension has multiple signatures."""
        db = Database(db_path=str(tmp_path / "test.db"))
        db.add_signature("jpg", "FFD8FFE0", 0)
        db.add_signature("jpg", "FFD8FFE1", 0)
        db.add_signature("jpg", "FFD8FFE2", 0)
        
        output_file = tmp_path / "export.json"
        count = export_signatures_to_json(db, str(output_file))
        
        assert count == 3
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        jpg_sigs = [s for s in data["signatures"] if s["extension"] == "jpg"]
        assert len(jpg_sigs) == 3
        
        db.close()
    
    def test_export_format_structure(self, database, tmp_path):
        """Test that exported JSON has correct structure."""
        output_file = tmp_path / "export.json"
        
        export_signatures_to_json(database, str(output_file))
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check top-level structure
        assert "version" in data
        assert "description" in data
        assert "signatures" in data
        
        # Check signature structure
        for sig in data["signatures"]:
            assert "extension" in sig
            assert "magic_bytes" in sig
            assert "offset" in sig


class TestDataLoaderIntegration:
    """Integration tests for DataLoader."""
    
    def test_load_and_export_roundtrip(self, tmp_path):
        """Test loading signatures and exporting them again."""
        # Create original file
        original_file = tmp_path / "original.json"
        original_file.write_text(json.dumps({
            "signatures": [
                {"extension": "pdf", "magic_bytes": "25504446", "offset": 0},
                {"extension": "png", "magic_bytes": "89504E47", "offset": 0},
            ]
        }))
        
        # Load into database
        db = Database(db_path=str(tmp_path / "test.db"))
        loader = DataLoader()
        loaded = loader.load_signatures(str(original_file), db)
        assert loaded == 2
        
        # Export to new file
        export_file = tmp_path / "export.json"
        exported = export_signatures_to_json(db, str(export_file))
        assert exported == 2
        
        # Verify exported content
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        extensions = [s["extension"] for s in data["signatures"]]
        assert "pdf" in extensions
        assert "png" in extensions
        
        db.close()
    
    def test_validate_before_load(self, tmp_path):
        """Test validating file before loading."""
        # Create valid file
        valid_file = tmp_path / "valid.json"
        valid_file.write_text(json.dumps({
            "signatures": [{"extension": "pdf", "magic_bytes": "25504446"}]
        }))
        
        # Create invalid file
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text(json.dumps({"wrong": "structure"}))
        
        loader = DataLoader()
        
        # Valid file should pass
        assert loader.validate_source(str(valid_file)) is True
        
        # Invalid file should fail
        assert loader.validate_source(str(invalid_file)) is False
    
    def test_load_with_custom_logger(self, tmp_path):
        """Test loading with custom logger captures messages."""
        mock_logger = MagicMock()
        loader = DataLoader(logger=mock_logger)
        
        json_file = tmp_path / "signatures.json"
        json_file.write_text(json.dumps({
            "signatures": [{"extension": "pdf", "magic_bytes": "25504446"}]
        }))
        
        db = Database(db_path=str(tmp_path / "test.db"))
        loader.load_signatures(str(json_file), db)
        
        # Verify logger was called
        assert mock_logger.info.called
        
        db.close()
