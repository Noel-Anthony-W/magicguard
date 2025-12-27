"""Display utilities for CLI output.

This module provides Rich-based formatting for CLI output.
Keeps presentation logic separate from business logic.
"""

from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def display_validation_result(file_path: str, is_valid: bool, verbose: bool = False):
    """Display file validation result.
    
    Args:
        file_path: Path to the validated file
        is_valid: Whether file passed validation
        verbose: Whether to show detailed output
    """
    file_name = Path(file_path).name
    
    if is_valid:
        icon = "[green]✓[/green]"
        status = "[green]VALID[/green]"
        message = f"{icon} {file_name} - {status}"
    else:
        icon = "[red]✗[/red]"
        status = "[red]INVALID[/red]"
        message = f"{icon} {file_name} - {status}"
    
    if verbose:
        console.print(f"{message} ({file_path})")
    else:
        console.print(message)


def display_file_hash(file_path: str, file_hash: str):
    """Display file SHA-256 hash.
    
    Args:
        file_path: Path to the file
        file_hash: SHA-256 hash hex string
    """
    file_name = Path(file_path).name
    console.print(f"\n[bold]SHA-256:[/bold] {file_hash}")
    console.print(f"[dim]({file_name})[/dim]")


def display_error(message: str):
    """Display error message.
    
    Args:
        message: Error message to display
    """
    console.print(f"[red]✗ {message}[/red]", style="bold")


def display_warning(message: str):
    """Display warning message.
    
    Args:
        message: Warning message to display
    """
    console.print(f"[yellow]⚠ {message}[/yellow]")


def display_info(message: str):
    """Display informational message.
    
    Args:
        message: Info message to display
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def display_success(message: str):
    """Display success message.
    
    Args:
        message: Success message to display
    """
    console.print(f"[green]✓ {message}[/green]")


def display_scan_summary(
    total: int,
    valid: int,
    invalid: int,
    errors: int,
    title: str = "Scan Summary"
):
    """Display scan summary table.
    
    Args:
        total: Total files scanned
        valid: Number of valid files
        invalid: Number of invalid files
        errors: Number of errors encountered
        title: Title for the summary table
    """
    table = Table(title=title, show_header=False, box=None)
    
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right")
    
    table.add_row("Total Files", str(total))
    table.add_row("Valid", f"[green]{valid}[/green]")
    table.add_row("Invalid", f"[red]{invalid}[/red]")
    
    if errors > 0:
        table.add_row("Errors", f"[yellow]{errors}[/yellow]")
    
    console.print()
    console.print(table)
    console.print()


def display_signature_info(extension: str, signatures: list[tuple[str, int]]):
    """Display signature information for a file type.
    
    Args:
        extension: File extension
        signatures: List of (magic_bytes, offset) tuples
    """
    console.print(f"\n[bold].{extension}[/bold] ({len(signatures)} signature{'s' if len(signatures) > 1 else ''})")
    
    for magic_bytes, offset in signatures:
        console.print(f"  Magic Bytes: {magic_bytes}")
        console.print(f"  Offset: {offset}")
        if len(signatures) > 1:
            console.print()
