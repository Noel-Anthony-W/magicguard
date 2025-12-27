# MagicGuard 🛡️

**File type validator using magic bytes to detect file type spoofing and malware disguised with incorrect extensions.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code Coverage](https://img.shields.io/badge/coverage-82.64%25-green.svg)](htmlcov/index.html)

## 🎯 Overview

MagicGuard validates files by checking their **magic bytes** (file signatures) against their declared file extensions. This detects file type spoofing attacks where malicious files are disguised with incorrect extensions (e.g., an executable masquerading as a PDF).

### Key Features

- **Magic Bytes Validation**: Verifies file signatures match extensions
- **Office Document Validation**: Deep structure validation for DOCX, XLSX, PPTX
- **SHA-256 Hashing**: Calculate file integrity hashes
- **CLI Interface**: Easy-to-use command-line tools
- **Extensible Architecture**: Protocol-based design with dependency injection
- **29 File Types Supported**: Documents, images, archives, executables, media files

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/anthonynoelw/magicguard.git
cd magicguard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

## 🚀 Quick Start

### Command Line Usage

```bash
# Scan a single file
magicguard scan document.pdf

# Scan with verbose output
magicguard scan image.jpg --verbose

# Scan with SHA-256 hash
magicguard scan file.exe --hash

# Scan entire directory
magicguard scan-dir /path/to/folder

# Scan directory recursively
magicguard scan-dir /path/to/folder --recursive

# Scan only specific extensions
magicguard scan-dir /path/to/folder -e pdf -e docx

# List supported file types
magicguard list-signatures

# Show status
magicguard status --verbose
```

### Python API Usage

```python
from magicguard.core.validator import FileValidator

# Initialize validator
validator = FileValidator()

# Validate a file
try:
    is_valid = validator.validate("document.pdf")
    if is_valid:
        print("✓ File is valid")
    else:
        print("✗ File validation failed")
except Exception as e:
    print(f"Error: {e}")

# Get file hash
file_hash = validator.get_file_hash("document.pdf")
print(f"SHA-256: {file_hash}")

# Clean up
validator.close()
```

## 🛠️ Architecture

MagicGuard follows a clean, layered architecture:

```
src/magicguard/
├── core/               # Business logic (UI-independent)
│   ├── validator.py    # File validation orchestration
│   ├── database.py     # Signature database management
│   ├── readers.py      # File signature reading strategies
│   ├── exceptions.py   # Custom exception hierarchy
│   └── interfaces.py   # Protocol definitions
├── cli/                # Command-line interface
│   ├── commands.py     # CLI commands
│   └── display.py      # Output formatting
└── utils/              # Shared utilities
    ├── config.py       # Configuration management
    ├── data_loader.py  # Signature loading
    └── logger.py       # Logging configuration
```

### Design Principles

- **Protocol-Based**: Uses Python protocols for type safety and testability
- **Dependency Injection**: Components are loosely coupled
- **Strategy Pattern**: Multiple reader types for different file formats
- **Separation of Concerns**: Core logic independent of UI layer

## 📋 Supported File Types

### Documents
- PDF, DOCX, XLSX, PPTX, XML

### Images
- PNG, JPG/JPEG, GIF, BMP, ICO, WebP

### Archives
- ZIP, RAR, 7Z, TAR, GZ

### Executables
- EXE, DLL, ELF

### Media
- MP3, MP4, AVI, MKV, WAV, FLAC

### Databases
- SQLite

## 🧪 Testing

MagicGuard has comprehensive test coverage:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/magicguard --cov-report=html

# Run specific test file
pytest tests/test_validator.py -v
```

**Test Coverage**: 82.64% overall
- Core modules: 85%+
- Validator: 96.58%
- Readers: 87.30%
- Database: 79.35%

## 🔒 Security Use Cases

### Malware Detection
Detect executables disguised as documents:
```bash
magicguard scan suspicious.pdf
# ✗ suspicious.pdf - INVALID
# File has .pdf extension but contains EXE signature
```

### Email Attachment Scanning
Validate attachments before opening:
```bash
magicguard scan-dir ~/Downloads/email-attachments --recursive
```

### Upload Validation
Integrate into file upload workflows:
```python
from magicguard.core.validator import FileValidator

def validate_upload(file_path):
    validator = FileValidator()
    try:
        if not validator.validate(file_path):
            raise SecurityError("File type spoofing detected!")
    finally:
        validator.close()
```

## 🐳 Docker Support

```bash
# Build image
docker build -f docker/Dockerfile -t magicguard:latest .

# Run scan
docker run --rm -v /path/to/files:/data magicguard:latest scan /data/file.pdf

# Run with docker-compose
docker-compose -f docker/docker-compose.yml up
```

## 🔧 Configuration

MagicGuard stores data in `~/.magicguard/`:

```
~/.magicguard/
├── data/
│   └── signatures.db    # Signature database
└── log/
    └── YYYY-MM-DD.log   # Daily rotating logs
```

## 📝 Development

### Code Style

- **PEP 8 compliant**
- **Black formatter** (100 char line length)
- **Type hints required** for all functions
- **Google-style docstrings**

### Running Quality Checks

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Run all checks
pre-commit run --all-files
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Anthony Weiß**
- Email: weiss.anthonynoel@gmail.com
- GitHub: [@anthonynoelw](https://github.com/anthonynoelw)

## 🙏 Acknowledgments

- Magic bytes signatures from [Gary Kessler's File Signatures Table](https://www.garykessler.net/library/file_sigs.html)
- Inspired by the `file` command and libmagic library

## 📚 Documentation

For detailed documentation:
- [Architecture Guide](docs/architecture.md) (coming soon)
- [API Reference](docs/api.md) (coming soon)
- [CLI Guide](docs/cli.md) (coming soon)

---

**⚠️ Security Note**: MagicGuard is a validation tool, not a complete security solution. Always use multiple layers of security when handling untrusted files.
