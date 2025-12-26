# GitHub Copilot Instructions for MagicGuard

## Project Overview

MagicGuard is a Python-based file type validator using magic bytes (file signatures) to detect file type spoofing and validate file integrity. The project provides robust file validation capabilities to ensure files match their declared extensions.

### Key Features
- Magic bytes validation (file signature verification)
- SHA-256 hashing for file integrity
- CLI interface for easy file scanning
- Docker support for containerized deployment
- Jenkins CI/CD integration

### Tech Stack
- **Python**: 3.11+
- **Database**: SQLite3 for signature database
- **CLI Libraries**: Click + Rich for terminal interface
- **Testing**: Pytest with coverage reporting
- **Containerization**: Docker + Docker Compose
- **CI/CD**: Jenkins pipeline

## Code Style & Standards

### General Standards
- **PEP 8 Compliance**: All code must adhere to PEP 8 standards
- **Formatter**: Use Black formatter for consistent code formatting
- **Type Hints**: Required for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions, classes, and methods
- **Line Length**: Maximum 100 characters per line

### Naming Conventions

#### Classes
Use **PascalCase** for class names:
```python
class FileValidator:
    pass

class SignatureDatabase:
    pass
```

#### Functions and Methods
Use **snake_case** for function and method names:
```python
def check_magic_bytes(file_path: str) -> bool:
    pass

def get_signature(extension: str) -> str:
    pass
```

#### Constants
Use **UPPER_SNAKE_CASE** for constants:
```python
DEFAULT_OFFSET = 0
MAX_FILE_SIZE = 104857600  # 100MB in bytes
SUPPORTED_EXTENSIONS = ["pdf", "jpg", "png", "exe"]
```

#### Private Methods
Prefix with single underscore for private/internal methods:
```python
def _validate_internal(self, data: bytes) -> bool:
    pass

def _parse_signature(self, raw_bytes: str) -> bytes:
    pass
```

## Function Documentation Template

Use this template for all function documentation:

```python
def function_name(param1: Type1, param2: Type2 = default) -> ReturnType:
    """One-line summary of what the function does.
    
    Detailed description of the function's behavior, if needed.
    Explain complex logic or important implementation details.
    
    Args:
        param1: Description of param1 and its expected values
        param2: Description of param2 with default value explanation
        
    Returns:
        Description of the return value and its structure
        
    Raises:
        SpecificError: When this specific condition occurs
        AnotherError: When another condition is met
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        Expected output
    """
    pass
```

## Project Architecture

### Directory Structure
```
src/magicguard/
├── core/           # Business logic (no UI dependencies)
│   ├── validator.py
│   ├── database.py
│   └── exceptions.py
├── cli/            # CLI interface (uses core/)
│   ├── commands.py
│   └── display.py
└── utils/          # Shared utilities (logging, config)
    ├── logger.py
    └── config.py
```

### Layer Separation Rules

**Critical architectural constraints:**

1. **Core Layer** (`src/magicguard/core/`)
   - Contains all business logic
   - **MUST NOT** import from `cli/`
   - Should be UI-agnostic and reusable
   - Can import from `utils/`

2. **CLI Layer** (`src/magicguard/cli/`)
   - Handles user interface and interaction
   - Can import from `core/` and `utils/`
   - Responsible for output formatting and user experience

3. **Utils Layer** (`src/magicguard/utils/`)
   - Must be standalone
   - Cannot import from `core/` or `cli/`
   - Provides general-purpose utilities

**Example:**
```python
# ✅ CORRECT: CLI imports from core
from magicguard.core.validator import FileValidator

# ❌ WRONG: Core imports from cli
from magicguard.cli.display import format_output  # Never do this in core!
```

## Database Schema

### Signatures Table
```sql
CREATE TABLE signatures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    extension TEXT NOT NULL,
    magic_bytes TEXT NOT NULL,
    offset INTEGER DEFAULT 0,
    description TEXT,
    mime_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(extension, offset)
);
```

### Column Descriptions
- **id**: Auto-incrementing primary key
- **extension**: File extension (e.g., 'pdf', 'jpg', 'exe')
- **magic_bytes**: Hex string of the file signature (e.g., '25504446' for PDF)
- **offset**: Byte offset where magic bytes appear (default: 0)
- **description**: Human-readable description of file type
- **mime_type**: MIME type (e.g., 'application/pdf', 'image/jpeg')
- **created_at**: Timestamp when signature was added

## Error Handling Standards

### Custom Exceptions
All exceptions must inherit from the base exception hierarchy in `magicguard.core.exceptions`:

```python
# Base exception
class MagicGuardError(Exception):
    """Base exception for all MagicGuard errors."""
    pass

# Specific exceptions
class ValidationError(MagicGuardError):
    """Raised when file validation fails."""
    pass

class SignatureNotFoundError(MagicGuardError):
    """Raised when signature not found in database."""
    pass

class DatabaseError(MagicGuardError):
    """Raised when database operations fail."""
    pass
```

### Error Message Guidelines
- Always provide **specific, actionable** error messages
- Include relevant context (file path, extension, expected vs actual)
- Avoid generic messages like "Error occurred"

**Examples:**
```python
# ❌ Bad
raise ValidationError("Validation failed")

# ✅ Good
raise ValidationError(
    f"File '{file_path}' has extension '.pdf' but contains PNG signature. "
    f"Expected magic bytes: {expected_sig}, Found: {actual_sig}"
)

# ✅ Good
raise SignatureNotFoundError(
    f"No signature found for extension '.{extension}'. "
    f"Supported extensions: {', '.join(supported_exts)}"
)
```

## Testing Guidelines

### Testing Framework
- Use **pytest** for all tests
- Use fixtures for common test setup
- Organize tests in `tests/` directory mirroring `src/` structure

### Coverage Requirements
- **Overall Coverage**: Minimum 80%
- **Core Logic**: Minimum 95% coverage (critical business logic)
- **CLI Layer**: Standard 80% coverage
- **Utils Layer**: Minimum 90% coverage

### Test Naming Convention
Test names should describe the behavior being tested:

```python
# ✅ Good - Descriptive names
def test_detects_spoofed_extension():
    pass

def test_returns_true_for_valid_pdf():
    pass

def test_raises_error_when_signature_missing():
    pass

# ❌ Bad - Vague names
def test_validator():
    pass

def test_case_1():
    pass
```

### Test Structure
```python
import pytest
from magicguard.core.validator import FileValidator
from magicguard.core.exceptions import ValidationError

@pytest.fixture
def validator():
    """Fixture providing a configured FileValidator instance."""
    return FileValidator()

@pytest.fixture
def sample_pdf_file(tmp_path):
    """Fixture creating a temporary PDF file."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")
    return pdf_file

def test_detects_spoofed_extension(validator, tmp_path):
    """Test that validator detects when file extension doesn't match content."""
    # Arrange: Create PNG file with .pdf extension
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"\x89PNG\r\n\x1a\n")
    
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(fake_pdf)
    
    assert "PNG signature" in str(exc_info.value)
    assert "expected .pdf" in str(exc_info.value).lower()
```

## Logging Standards

### Logger Setup
Use the centralized logger from `magicguard.utils.logger`:

```python
from magicguard.utils.logger import get_logger

logger = get_logger(__name__)
```

### Log Levels and Usage

#### DEBUG
Diagnostic information for development and troubleshooting:
```python
logger.debug(f"Reading magic bytes from offset {offset}")
logger.debug(f"SQL Query: {query} with params {params}")
logger.debug(f"Raw bytes read: {raw_bytes.hex()}")
```

#### INFO
General progress and operational messages:
```python
logger.info(f"Starting validation of file: {file_path}")
logger.info(f"Database initialized with {count} signatures")
logger.info(f"Scan completed successfully")
```

#### WARNING
Validation mismatches and recoverable issues:
```python
logger.warning(f"Extension mismatch: file has .pdf but contains {detected_type}")
logger.warning(f"Signature for .{ext} not found in database, skipping validation")
```

#### ERROR
Exceptions and operation failures:
```python
logger.error(f"Failed to read file {file_path}: {str(e)}")
logger.error(f"Database connection failed: {str(e)}")
```

#### CRITICAL
System-level failures requiring immediate attention:
```python
logger.critical(f"Database file corrupted: {db_path}")
logger.critical(f"Unable to initialize core validator: {str(e)}")
```

## CLI Design

### Command Structure
```bash
# Scan a single file
magicguard scan <file>

# Scan a directory
magicguard scan --directory <path>

# Additional options
magicguard scan <file> --verbose      # Detailed output
magicguard scan <file> --output json  # JSON format output
```

### CLI Implementation Pattern
```python
import click
from rich.console import Console
from magicguard.core.validator import FileValidator
from magicguard.core.exceptions import MagicGuardError

console = Console()

@click.group()
def cli():
    """MagicGuard - File type validator using magic bytes."""
    pass

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def scan(file: str, verbose: bool):
    """Scan a file to validate its type matches the extension."""
    try:
        validator = FileValidator()
        result = validator.validate(file)
        
        if result:
            console.print(f"[green]✓[/green] {file} is valid")
        else:
            console.print(f"[red]✗[/red] {file} failed validation")
            
    except MagicGuardError as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()
```

### Output Formatting Guidelines
- Use Rich library for colored and formatted output
- **Success**: Green checkmark with file path
- **Failure**: Red X with specific reason
- **Errors**: Red "Error:" prefix with clear message
- **Verbose mode**: Include magic bytes, offsets, and detailed diagnostics

## Development Workflow

### Before Committing
1. Run Black formatter: `black src/ tests/`
2. Run type checker: `mypy src/`
3. Run linter: `ruff check src/ tests/`
4. Run tests: `pytest tests/ -v --cov`
5. Ensure coverage meets requirements

### Creating New Features
1. Start with core business logic in `core/`
2. Add comprehensive tests with 95%+ coverage
3. Add CLI interface in `cli/` if user-facing
4. Update documentation
5. Add example usage to README if applicable

### Pull Request Guidelines
- Keep changes focused and atomic
- Include tests for new functionality
- Update docstrings and type hints
- Ensure CI pipeline passes
- Request review from maintainers

## Common Patterns

### Reading Magic Bytes
```python
def read_magic_bytes(file_path: str, length: int = 8, offset: int = 0) -> bytes:
    """Read magic bytes from a file.
    
    Args:
        file_path: Path to the file to read
        length: Number of bytes to read
        offset: Byte offset to start reading from
        
    Returns:
        Bytes read from the file
        
    Raises:
        IOError: If file cannot be read
    """
    with open(file_path, 'rb') as f:
        f.seek(offset)
        return f.read(length)
```

### Database Queries
```python
def get_signature(self, extension: str) -> list[tuple]:
    """Get signature(s) for a file extension.
    
    Args:
        extension: File extension without dot (e.g., 'pdf')
        
    Returns:
        List of tuples containing (magic_bytes, offset)
        
    Raises:
        SignatureNotFoundError: If no signature found for extension
    """
    cursor = self.conn.cursor()
    cursor.execute(
        "SELECT magic_bytes, offset FROM signatures WHERE extension = ?",
        (extension,)
    )
    results = cursor.fetchall()
    
    if not results:
        raise SignatureNotFoundError(
            f"No signature found for extension '.{extension}'"
        )
    
    return results
```

## Security Considerations

### File Handling
- Always validate file paths to prevent directory traversal
- Set maximum file size limits to prevent memory exhaustion
- Use context managers for file operations to ensure cleanup
- Never execute or eval file contents

### Input Validation
- Sanitize all user inputs (file paths, extensions)
- Validate command-line arguments
- Use parameterized SQL queries to prevent injection
- Escape special characters in output

### Database Security
- Use parameterized queries exclusively
- Set appropriate file permissions on database file
- Regular backups of signature database
- Validate database schema on initialization

## Additional Resources

- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Remember**: When generating code for MagicGuard, always prioritize clarity, type safety, and comprehensive error handling. The goal is to create reliable, maintainable code that accurately validates file types and protects users from file type spoofing attacks.
