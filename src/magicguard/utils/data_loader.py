"""Data loading utilities for file signatures.

This module provides functionality to load file signatures from JSON format
into the signature database. Supports the DataLoaderProtocol for dependency
injection.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from magicguard.utils.logger import get_logger


class DataLoader:
    """Loads file signatures from JSON into database.
    
    Implements the DataLoaderProtocol. Supports validation of JSON
    structure before loading and handles duplicate signatures gracefully.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize data loader.
        
        Args:
            logger: Logger instance. If None, creates logger for this module.
        """
        self.logger = logger or get_logger(__name__)
    
    def load_signatures(self, source_path: str, database) -> int:
        """Load signatures from JSON file into database.
        
        Args:
            source_path: Path to JSON file containing signatures
            database: DatabaseProtocol instance to load into
            
        Returns:
            Number of signatures successfully loaded
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValueError: If JSON structure is invalid
        """
        self.logger.info(f"Loading signatures from: {source_path}")
        
        source = Path(source_path)
        if not source.exists():
            error_msg = f"Signature file not found: {source_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Load and parse JSON
        with open(source, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if not self._validate_structure(data):
            error_msg = f"Invalid JSON structure in {source_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Load signatures
        signatures = data.get('signatures', [])
        loaded_count = 0
        skipped_count = 0
        
        for sig_data in signatures:
            try:
                database.add_signature(
                    extension=sig_data['extension'],
                    magic_bytes=sig_data['magic_bytes'],
                    offset=sig_data.get('offset', 0),
                    description=sig_data.get('description'),
                    mime_type=sig_data.get('mime_type'),
                )
                loaded_count += 1
                
            except Exception as e:
                # Skip duplicates and other errors
                self.logger.debug(
                    f"Skipped signature for '.{sig_data.get('extension', '?')}': {e}"
                )
                skipped_count += 1
        
        self.logger.info(
            f"Loaded {loaded_count} signatures, skipped {skipped_count} duplicates"
        )
        return loaded_count
    
    def validate_source(self, source_path: str) -> bool:
        """Validate JSON file structure.
        
        Args:
            source_path: Path to JSON file
            
        Returns:
            True if file has valid structure
        """
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._validate_structure(data)
        except (json.JSONDecodeError, FileNotFoundError, IOError):
            return False
    
    def _validate_structure(self, data: dict) -> bool:
        """Validate JSON data structure.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            True if structure is valid
        """
        # Check top-level structure
        if not isinstance(data, dict):
            self.logger.error("JSON root must be an object")
            return False
        
        if 'signatures' not in data:
            self.logger.error("JSON must have 'signatures' array")
            return False
        
        signatures = data['signatures']
        if not isinstance(signatures, list):
            self.logger.error("'signatures' must be an array")
            return False
        
        # Validate each signature entry
        for i, sig in enumerate(signatures):
            if not isinstance(sig, dict):
                self.logger.error(f"Signature {i} must be an object")
                return False
            
            required_fields = ['extension', 'magic_bytes']
            for field in required_fields:
                if field not in sig:
                    self.logger.error(
                        f"Signature {i} missing required field: {field}"
                    )
                    return False
            
            # Validate magic_bytes is hex string
            try:
                bytes.fromhex(sig['magic_bytes'])
            except ValueError:
                self.logger.error(
                    f"Signature {i} has invalid magic_bytes (must be hex): "
                    f"{sig['magic_bytes']}"
                )
                return False
        
        return True


def initialize_default_signatures(database, logger: Optional[logging.Logger] = None):
    """Initialize database with default signatures if empty.
    
    Loads signatures from bundled data/signatures.json file if the database
    is empty. This is typically called on first run or when database is reset.
    
    Args:
        database: DatabaseProtocol instance
        logger: LoggerProtocol instance. If None, creates logger for this module.
        
    Returns:
        Number of signatures loaded, or 0 if database already populated
    """
    logger = logger or get_logger(__name__)
    
    # Check if database already has signatures
    try:
        count = database.signature_count()
        if count > 0:
            logger.info(f"Database already contains {count} signatures")
            return 0
    except Exception as e:
        logger.warning(f"Could not check signature count: {e}")
    
    # Load from bundled file
    # Try multiple possible locations
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "data" / "signatures.json",
        Path.cwd() / "data" / "signatures.json",
        Path.home() / ".magicguard" / "data" / "signatures.json",
    ]
    
    for sig_path in possible_paths:
        if sig_path.exists():
            logger.info(f"Found signature file at: {sig_path}")
            loader = DataLoader(logger=logger)
            loaded = loader.load_signatures(str(sig_path), database)
            return loaded
    
    logger.warning("No signature file found. Database will be empty.")
    return 0


def export_signatures_to_json(database, output_path: str, logger: Optional[logging.Logger] = None) -> int:
    """Export database signatures to JSON file.
    
    Useful for backup, sharing, or migrating signatures.
    
    Args:
        database: DatabaseProtocol instance
        output_path: Path where JSON file will be saved
        logger: LoggerProtocol instance
        
    Returns:
        Number of signatures exported
    """
    logger = logger or get_logger(__name__)
    
    logger.info(f"Exporting signatures to: {output_path}")
    
    # Get all extensions
    extensions = database.get_all_extensions()
    
    signatures_data = []
    for ext in extensions:
        sigs = database.get_signatures(ext)
        for magic_hex, offset in sigs:
            signatures_data.append({
                "extension": ext,
                "magic_bytes": magic_hex,
                "offset": offset,
            })
    
    # Create export data
    export_data = {
        "version": "1.0",
        "description": "Exported signatures from MagicGuard",
        "signatures": signatures_data
    }
    
    # Write to file
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    count = len(signatures_data)
    logger.info(f"Exported {count} signatures to {output_path}")
    return count
