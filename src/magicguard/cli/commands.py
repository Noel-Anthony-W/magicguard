"""CLI commands for MagicGuard file validator.

This module provides command-line interface functionality using Click.
Commands are kept UI-focused while business logic remains in core/.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from magicguard.core.validator import FileValidator
from magicguard.core.database import Database
from magicguard.core.readers import ReaderFactory
from magicguard.core.exceptions import (
    MagicGuardError,
    ValidationError,
    FileReadError,
    SignatureNotFoundError,
)
from magicguard.utils.data_loader import initialize_default_signatures
from magicguard.utils.logger import get_logger
from magicguard.cli.display import (
    display_validation_result,
    display_file_hash,
    display_error,
    display_info,
)

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0", prog_name="MagicGuard")
def cli():
    """MagicGuard - File type validator using magic bytes.
    
    Detects file type spoofing by verifying magic bytes match file extensions.
    Protects against malicious files disguised with incorrect extensions.
    """
    pass


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--hash', '-h', is_flag=True, help='Display file SHA-256 hash')
def scan(file_path: str, verbose: bool, hash: bool):
    """Scan a file to validate its type matches the extension.
    
    Examples:
        magicguard scan document.pdf
        magicguard scan image.jpg --verbose
        magicguard scan file.exe --hash
    """
    try:
        if verbose:
            display_info(f"Scanning: {file_path}")
        
        # Initialize validator
        validator = FileValidator()
        
        # Ensure database has signatures
        if validator.database.signature_count() == 0:
            display_info("Initializing signature database...")
            count = initialize_default_signatures(validator.database)
            if count > 0:
                display_info(f"Loaded {count} file signatures")
        
        # Validate file
        result = validator.validate(file_path)
        
        # Display result
        display_validation_result(file_path, result, verbose=verbose)
        
        # Display hash if requested
        if hash:
            file_hash = validator.get_file_hash(file_path)
            display_file_hash(file_path, file_hash)
        
        validator.close()
        sys.exit(0 if result else 1)
        
    except ValidationError as e:
        display_error(f"Validation failed: {str(e)}")
        sys.exit(1)
    except FileReadError as e:
        display_error(f"File error: {str(e)}")
        sys.exit(1)
    except SignatureNotFoundError as e:
        display_error(f"Unknown file type: {str(e)}")
        sys.exit(1)
    except MagicGuardError as e:
        display_error(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error during scan")
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--recursive', '-r', is_flag=True, help='Scan subdirectories recursively')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--extensions', '-e', multiple=True, help='Only scan files with these extensions')
def scan_dir(directory: str, recursive: bool, verbose: bool, extensions: tuple):
    """Scan all files in a directory.
    
    Examples:
        magicguard scan-dir /path/to/folder
        magicguard scan-dir /path/to/folder --recursive
        magicguard scan-dir /path/to/folder -e pdf -e jpg
    """
    try:
        dir_path = Path(directory)
        
        # Initialize validator
        validator = FileValidator()
        
        # Ensure database has signatures
        if validator.database.signature_count() == 0:
            display_info("Initializing signature database...")
            count = initialize_default_signatures(validator.database)
            if count > 0:
                display_info(f"Loaded {count} file signatures")
        
        # Collect files to scan
        pattern = "**/*" if recursive else "*"
        files = [f for f in dir_path.glob(pattern) if f.is_file()]
        
        # Filter by extensions if specified
        if extensions:
            ext_set = {ext.lower().lstrip('.') for ext in extensions}
            files = [f for f in files if f.suffix.lower().lstrip('.') in ext_set]
        
        if not files:
            display_info(f"No files found in {directory}")
            validator.close()
            sys.exit(0)
        
        display_info(f"Scanning {len(files)} files...")
        
        # Scan each file
        valid_count = 0
        invalid_count = 0
        error_count = 0
        
        for file_path in files:
            try:
                result = validator.validate(str(file_path))
                
                if result:
                    valid_count += 1
                    if verbose:
                        display_validation_result(str(file_path), result, verbose=False)
                else:
                    invalid_count += 1
                    display_validation_result(str(file_path), result, verbose=False)
                    
            except (ValidationError, SignatureNotFoundError) as e:
                invalid_count += 1
                if verbose:
                    display_error(f"{file_path.name}: {str(e)}")
            except Exception as e:
                error_count += 1
                if verbose:
                    display_error(f"{file_path.name}: {str(e)}")
        
        # Display summary
        console.print()
        console.print(f"[bold]Scan Summary:[/bold]")
        console.print(f"  [green]Valid:[/green] {valid_count}")
        console.print(f"  [red]Invalid:[/red] {invalid_count}")
        if error_count > 0:
            console.print(f"  [yellow]Errors:[/yellow] {error_count}")
        
        validator.close()
        sys.exit(0 if invalid_count == 0 and error_count == 0 else 1)
        
    except MagicGuardError as e:
        display_error(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error during directory scan")
        sys.exit(1)


@cli.command()
def list_signatures():
    """List all supported file signatures.
    
    Displays all file types that MagicGuard can validate.
    """
    try:
        database = Database()
        
        # Ensure database has signatures
        if database.signature_count() == 0:
            display_info("Initializing signature database...")
            count = initialize_default_signatures(database)
            if count > 0:
                display_info(f"Loaded {count} file signatures")
        
        extensions = database.get_all_extensions()
        
        if not extensions:
            display_info("No signatures loaded")
            database.close()
            sys.exit(0)
        
        console.print(f"\n[bold]Supported File Types ({len(extensions)}):[/bold]\n")
        
        # Group by category
        categories = {
            "Documents": ["pdf", "docx", "xlsx", "pptx", "xml"],
            "Images": ["jpg", "jpeg", "png", "gif", "bmp", "ico", "webp"],
            "Archives": ["zip", "rar", "7z", "tar", "gz"],
            "Executables": ["exe", "dll", "elf"],
            "Media": ["mp3", "mp4", "avi", "mkv", "wav", "flac"],
            "Databases": ["sqlite"],
        }
        
        for category, exts in categories.items():
            matching = [ext for ext in extensions if ext in exts]
            if matching:
                console.print(f"[bold cyan]{category}:[/bold cyan]")
                for ext in sorted(matching):
                    sigs = database.get_signatures(ext)
                    console.print(f"  .{ext} ({len(sigs)} signature{'s' if len(sigs) > 1 else ''})")
        
        # Show uncategorized
        categorized = set()
        for exts in categories.values():
            categorized.update(exts)
        uncategorized = [ext for ext in extensions if ext not in categorized]
        
        if uncategorized:
            console.print(f"\n[bold cyan]Other:[/bold cyan]")
            for ext in sorted(uncategorized):
                sigs = database.get_signatures(ext)
                console.print(f"  .{ext} ({len(sigs)} signature{'s' if len(sigs) > 1 else ''})")
        
        console.print()
        database.close()
        sys.exit(0)
        
    except MagicGuardError as e:
        display_error(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        logger.exception("Unexpected error listing signatures")
        sys.exit(1)


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed status')
def status(verbose: bool):
    """Show MagicGuard status and configuration.
    
    Displays database location, signature count, and configuration.
    """
    try:
        from magicguard.utils.config import get_database_path, get_log_dir
        
        database = Database()
        
        console.print("\n[bold]MagicGuard Status:[/bold]\n")
        
        # Database info
        db_path = get_database_path()
        console.print(f"[cyan]Database:[/cyan] {db_path}")
        
        sig_count = database.signature_count()
        console.print(f"[cyan]Signatures:[/cyan] {sig_count}")
        
        if sig_count == 0:
            console.print("  [yellow]⚠[/yellow]  Database is empty. Run any scan command to initialize.")
        
        # Log directory
        log_dir = get_log_dir()
        console.print(f"[cyan]Logs:[/cyan] {log_dir}")
        
        if verbose and sig_count > 0:
            extensions = database.get_all_extensions()
            console.print(f"\n[bold]Supported Extensions:[/bold]")
            console.print(f"  {', '.join(sorted(extensions))}")
        
        console.print()
        database.close()
        sys.exit(0)
        
    except Exception as e:
        display_error(f"Error: {str(e)}")
        sys.exit(1)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
