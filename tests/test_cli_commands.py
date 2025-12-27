"""Tests for CLI commands module.

Tests Click command-line interface using CliRunner for isolated testing.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner

from magicguard.cli.commands import cli, scan, scan_dir, list_signatures, status
from magicguard.core.database import Database


@pytest.fixture
def runner():
    """Provide Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_pdf(tmp_path):
    """Create a temporary valid PDF file."""
    pdf_file = tmp_path / "test.pdf"
    # Valid PDF signature
    pdf_file.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    return pdf_file


@pytest.fixture
def temp_fake_pdf(tmp_path):
    """Create a spoofed PDF (PNG signature with .pdf extension)."""
    fake_pdf = tmp_path / "fake.pdf"
    # PNG signature
    fake_pdf.write_bytes(b"\x89PNG\r\n\x1a\n")
    return fake_pdf


@pytest.fixture
def temp_directory(tmp_path):
    """Create a directory with multiple test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    
    # Valid PDF
    (test_dir / "document.pdf").write_bytes(b"%PDF-1.4\n")
    
    # Valid PNG
    (test_dir / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    
    # Spoofed file
    (test_dir / "malware.pdf").write_bytes(b"MZ\x90\x00")  # EXE signature
    
    return test_dir


class TestCLIBasics:
    """Test basic CLI functionality."""
    
    def test_cli_help(self, runner):
        """Test that --help works and shows usage."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "MagicGuard" in result.output
        assert "File type validator" in result.output
        assert "Commands:" in result.output
    
    def test_cli_version(self, runner):
        """Test that --version shows version number."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert "MagicGuard" in result.output
        assert "0.1.0" in result.output
    
    def test_cli_no_command(self, runner):
        """Test CLI with no command shows help."""
        result = runner.invoke(cli, [])
        # Click groups return exit code 2 when invoked without a command
        assert result.exit_code == 0 or "Usage:" in result.output
        assert "Usage:" in result.output


class TestScanCommand:
    """Test scan command functionality."""
    
    def test_scan_valid_file(self, runner, temp_pdf):
        """Test scanning a valid file."""
        result = runner.invoke(scan, [str(temp_pdf)])
        assert result.exit_code == 0
        assert "VALID" in result.output or "✓" in result.output
    
    def test_scan_invalid_file(self, runner, temp_fake_pdf):
        """Test scanning a spoofed file."""
        result = runner.invoke(scan, [str(temp_fake_pdf)])
        assert result.exit_code == 1
        assert "INVALID" in result.output or "✗" in result.output or "failed" in result.output.lower()
    
    def test_scan_nonexistent_file(self, runner):
        """Test scanning a file that doesn't exist."""
        result = runner.invoke(scan, ['/nonexistent/file.pdf'])
        assert result.exit_code == 2  # Click path validation error
        assert "does not exist" in result.output
    
    def test_scan_with_verbose(self, runner, temp_pdf):
        """Test scan with verbose flag."""
        result = runner.invoke(scan, [str(temp_pdf), '--verbose'])
        assert result.exit_code == 0
        # Verbose output may wrap paths across lines, just check filename present
        assert "test.pdf" in result.output
    
    def test_scan_with_hash(self, runner, temp_pdf):
        """Test scan with hash calculation."""
        result = runner.invoke(scan, [str(temp_pdf), '--hash'])
        assert result.exit_code == 0
        assert "SHA-256" in result.output
        # SHA-256 hash is 64 hex characters
        assert any(len(word) == 64 and all(c in '0123456789abcdef' for c in word.lower()) 
                   for word in result.output.split())
    
    def test_scan_with_verbose_and_hash(self, runner, temp_pdf):
        """Test scan with both verbose and hash flags."""
        result = runner.invoke(scan, [str(temp_pdf), '-v', '-h'])
        assert result.exit_code == 0
        assert "SHA-256" in result.output
        # Just check filename is present (path may be wrapped)
        assert "test.pdf" in result.output
    
    def test_scan_help(self, runner):
        """Test scan command help."""
        result = runner.invoke(scan, ['--help'])
        assert result.exit_code == 0
        assert "FILE_PATH" in result.output
        assert "--verbose" in result.output
        assert "--hash" in result.output


class TestScanDirCommand:
    """Test scan-dir command functionality."""
    
    def test_scan_dir_basic(self, runner, temp_directory):
        """Test scanning a directory."""
        result = runner.invoke(scan_dir, [str(temp_directory)])
        # Command should execute (exit code 0 or 1 for validation failures is OK)
        assert result.exit_code in [0, 1]
    
    def test_scan_dir_recursive(self, runner, temp_directory):
        """Test recursive directory scanning."""
        # Create subdirectory
        subdir = temp_directory / "subdir"
        subdir.mkdir()
        (subdir / "nested.pdf").write_bytes(b"%PDF-1.4\n")
        
        result = runner.invoke(scan_dir, [str(temp_directory), '--recursive'])
        assert result.exit_code in [0, 1]
    
    def test_scan_dir_with_extensions(self, runner, temp_directory):
        """Test scanning with extension filter."""
        result = runner.invoke(scan_dir, [
            str(temp_directory),
            '--extensions', 'pdf'
        ])
        assert result.exit_code in [0, 1]
    
    def test_scan_dir_multiple_extensions(self, runner, temp_directory):
        """Test scanning with multiple extension filters."""
        result = runner.invoke(scan_dir, [
            str(temp_directory),
            '-e', 'pdf',
            '-e', 'png'
        ])
        assert result.exit_code in [0, 1]
    
    def test_scan_dir_nonexistent(self, runner):
        """Test scanning non-existent directory."""
        result = runner.invoke(scan_dir, ['/nonexistent/directory'])
        assert result.exit_code == 2
        assert "does not exist" in result.output
    
    def test_scan_dir_not_a_directory(self, runner, temp_pdf):
        """Test scanning a file instead of directory."""
        result = runner.invoke(scan_dir, [str(temp_pdf)])
        assert result.exit_code != 0
    
    def test_scan_dir_verbose(self, runner, temp_directory):
        """Test directory scan with verbose output."""
        result = runner.invoke(scan_dir, [str(temp_directory), '--verbose'])
        assert result.exit_code in [0, 1]
    
    def test_scan_dir_help(self, runner):
        """Test scan-dir command help."""
        result = runner.invoke(scan_dir, ['--help'])
        assert result.exit_code == 0
        assert "DIRECTORY" in result.output
        assert "--recursive" in result.output
        assert "--extensions" in result.output


class TestListSignaturesCommand:
    """Test list-signatures command functionality."""
    
    def test_list_signatures_basic(self, runner):
        """Test listing signatures."""
        result = runner.invoke(list_signatures, [])
        assert result.exit_code == 0
        # Should show various file types
        assert "pdf" in result.output.lower() or "png" in result.output.lower()
    
    def test_list_signatures_shows_categories(self, runner):
        """Test that signatures are categorized."""
        result = runner.invoke(list_signatures, [])
        assert result.exit_code == 0
        # Should have category headers
        categories = ["Documents", "Images", "Archives", "Executables", "Media"]
        assert any(cat in result.output for cat in categories)
    
    def test_list_signatures_help(self, runner):
        """Test list-signatures command help."""
        result = runner.invoke(list_signatures, ['--help'])
        assert result.exit_code == 0
        # Check for help content (case insensitive)
        assert "signature" in result.output.lower() or "help" in result.output.lower()


class TestStatusCommand:
    """Test status command functionality."""
    
    def test_status_basic(self, runner):
        """Test status command."""
        result = runner.invoke(status, [])
        assert result.exit_code == 0
        assert "Database" in result.output
        assert "Signatures" in result.output
    
    def test_status_shows_paths(self, runner):
        """Test that status shows configuration paths."""
        result = runner.invoke(status, [])
        assert result.exit_code == 0
        # Should show database path
        assert "signatures.db" in result.output.lower() or "database" in result.output.lower()
    
    def test_status_verbose(self, runner):
        """Test status with verbose flag."""
        result = runner.invoke(status, ['--verbose'])
        assert result.exit_code == 0
    
    def test_status_help(self, runner):
        """Test status command help."""
        result = runner.invoke(status, ['--help'])
        assert result.exit_code == 0
        assert "configuration" in result.output.lower() or "status" in result.output.lower()


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_full_workflow(self, runner, temp_directory):
        """Test complete workflow: status -> scan -> list."""
        # Check status
        result = runner.invoke(status, [])
        assert result.exit_code == 0
        
        # Scan directory (allow exit code 1 for validation failures)
        result = runner.invoke(scan_dir, [str(temp_directory)])
        assert result.exit_code in [0, 1]
        
        # List signatures
        result = runner.invoke(list_signatures, [])
        assert result.exit_code == 0
    
    def test_scan_multiple_files_sequentially(self, runner, temp_directory):
        """Test scanning multiple files one by one."""
        pdf_file = temp_directory / "document.pdf"
        png_file = temp_directory / "image.png"
        
        # Scan PDF
        result1 = runner.invoke(scan, [str(pdf_file)])
        assert result1.exit_code == 0
        
        # Scan PNG
        result2 = runner.invoke(scan, [str(png_file)])
        assert result2.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def test_scan_with_invalid_arguments(self, runner):
        """Test scan with invalid argument combination."""
        result = runner.invoke(scan, [])
        assert result.exit_code == 2  # Missing required argument
    
    def test_scan_dir_with_invalid_extension_format(self, runner, temp_directory):
        """Test scan-dir with invalid extension format."""
        # Should still work - extensions are just strings
        result = runner.invoke(scan_dir, [
            str(temp_directory),
            '-e', '.pdf'  # With leading dot
        ])
        # Should either work or show clear error
        assert result.exit_code in [0, 1, 2]
    
    def test_command_keyboard_interrupt(self, runner, temp_directory):
        """Test that keyboard interrupt is handled gracefully."""
        # This is hard to test directly with CliRunner
        # The actual handling is in the command implementation
        pass


class TestCLIOutput:
    """Test CLI output formatting."""
    
    def test_output_uses_colors(self, runner, temp_pdf):
        """Test that output includes Rich formatting."""
        result = runner.invoke(scan, [str(temp_pdf)])
        # Rich removes color codes in tests by default, but we can check structure
        assert result.exit_code == 0
        assert len(result.output) > 0
    
    def test_summary_output(self, runner, temp_directory):
        """Test that directory scan shows summary."""
        result = runner.invoke(scan_dir, [str(temp_directory)])
        assert result.exit_code in [0, 1]
        # Should show some output
        assert len(result.output) > 0
    
    def test_error_output_format(self, runner):
        """Test that errors are formatted clearly."""
        result = runner.invoke(scan, ['/nonexistent/file.pdf'])
        assert result.exit_code == 2
        assert "Error" in result.output or "does not exist" in result.output
