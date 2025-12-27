"""Tests for CLI display module.

Tests Rich-based output formatting functions.
"""

import pytest
from unittest.mock import patch

from magicguard.cli.display import (
    display_validation_result,
    display_file_hash,
    display_error,
    display_info,
    display_success,
    display_warning,
    display_scan_summary,
    display_signature_info,
)


@pytest.fixture
def mock_console():
    """Mock Rich console for testing output."""
    with patch('magicguard.cli.display.console') as mock:
        yield mock


class TestDisplayValidationResult:
    """Test display_validation_result function."""
    
    def test_display_valid_file(self, mock_console):
        """Test displaying valid file result."""
        display_validation_result("/path/to/file.pdf", True)
        
        # Check that console.print was called
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "VALID" in call_args or "✓" in call_args
    
    def test_display_invalid_file(self, mock_console):
        """Test displaying invalid file result."""
        display_validation_result("/path/to/fake.pdf", False)
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "INVALID" in call_args or "✗" in call_args
    
    def test_display_with_verbose(self, mock_console):
        """Test verbose output includes full path."""
        display_validation_result("/full/path/to/file.pdf", True, verbose=True)
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "/full/path/to/file.pdf" in call_args
    
    def test_display_without_verbose(self, mock_console):
        """Test non-verbose output shows only filename."""
        display_validation_result("/full/path/to/file.pdf", True, verbose=False)
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        # Should show filename, not full path
        assert "file.pdf" in call_args


class TestDisplayFileHash:
    """Test display_file_hash function."""
    
    def test_display_hash(self, mock_console):
        """Test displaying file hash."""
        test_hash = "a" * 64  # Mock SHA-256 hash
        display_file_hash("/path/to/file.pdf", test_hash)
        
        assert mock_console.print.called
        # Should be called at least twice (hash and filename)
        assert mock_console.print.call_count >= 2
        
        # Check that hash appears in output
        all_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any(test_hash in call for call in all_calls)
        assert any("SHA-256" in call for call in all_calls)


class TestDisplayError:
    """Test display_error function."""
    
    def test_display_error_message(self, mock_console):
        """Test displaying error message."""
        display_error("Test error message")
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "Test error message" in call_args


class TestDisplayInfo:
    """Test display_info function."""
    
    def test_display_info_message(self, mock_console):
        """Test displaying info message."""
        display_info("Test info message")
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "Test info message" in call_args


class TestDisplaySuccess:
    """Test display_success function."""
    
    def test_display_success_message(self, mock_console):
        """Test displaying success message."""
        display_success("Operation completed")
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "Operation completed" in call_args


class TestDisplayWarning:
    """Test display_warning function."""
    
    def test_display_warning_message(self, mock_console):
        """Test displaying warning message."""
        display_warning("Test warning")
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "Test warning" in call_args


class TestDisplayScanSummary:
    """Test display_scan_summary function."""
    
    def test_display_summary(self, mock_console):
        """Test displaying scan summary."""
        display_scan_summary(total=10, valid=7, invalid=2, errors=1)
        
        # Just verify console.print was called (Rich tables are opaque objects)
        assert mock_console.print.called
        assert mock_console.print.call_count >= 2  # At least table + newlines
    
    def test_display_summary_no_errors(self, mock_console):
        """Test displaying summary with no errors."""
        display_scan_summary(total=10, valid=10, invalid=0, errors=0)
        
        assert mock_console.print.called


class TestDisplaySignatureInfo:
    """Test display_signature_info function."""
    
    def test_display_single_signature(self, mock_console):
        """Test displaying single signature."""
        signatures = [("25504446", 0)]
        display_signature_info("pdf", signatures)
        
        assert mock_console.print.called
        all_calls = [str(call) for call in mock_console.print.call_args_list]
        output_str = " ".join(all_calls)
        assert "pdf" in output_str
        assert "25504446" in output_str
    
    def test_display_multiple_signatures(self, mock_console):
        """Test displaying multiple signatures."""
        signatures = [("89504E47", 0), ("0A1A0A00", 4)]
        display_signature_info("png", signatures)
        
        assert mock_console.print.called
        all_calls = [str(call) for call in mock_console.print.call_args_list]
        output_str = " ".join(all_calls)
        assert "png" in output_str
        assert "89504E47" in output_str
        assert "0A1A0A00" in output_str


class TestDisplayFormatting:
    """Test output formatting and colors."""
    
    def test_valid_uses_green(self, mock_console):
        """Test valid results use green color."""
        display_validation_result("/test.pdf", True)
        
        call_args = str(mock_console.print.call_args)
        assert "green" in call_args.lower()
    
    def test_invalid_uses_red(self, mock_console):
        """Test invalid results use red color."""
        display_validation_result("/test.pdf", False)
        
        call_args = str(mock_console.print.call_args)
        assert "red" in call_args.lower()
    
    def test_error_uses_red(self, mock_console):
        """Test errors use red color."""
        display_error("Test error")
        
        call_args = str(mock_console.print.call_args)
        assert "red" in call_args.lower()


class TestDisplayEdgeCases:
    """Test edge cases and special characters."""
    
    def test_unicode_filename(self, mock_console):
        """Test handling unicode characters in filenames."""
        display_validation_result("/path/to/文件.pdf", True)
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "文件.pdf" in call_args
    
    def test_very_long_path(self, mock_console):
        """Test handling very long file paths."""
        long_path = "/very/long/path/" + "a" * 200 + "/file.pdf"
        display_validation_result(long_path, True)
        
        assert mock_console.print.called
    
    def test_special_characters(self, mock_console):
        """Test handling special characters in filenames."""
        display_validation_result("/path/to/file (copy).pdf", True)
        
        assert mock_console.print.called
        call_args = str(mock_console.print.call_args)
        assert "file (copy).pdf" in call_args
    
    def test_empty_hash(self, mock_console):
        """Test displaying empty hash."""
        display_file_hash("/test.pdf", "")
        
        assert mock_console.print.called
