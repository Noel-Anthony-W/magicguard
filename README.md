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
- **26+ File Types Supported**: 29 signatures across documents, images, archives, executables, media

## 📦 Installation

### Automated Installation (Recommended)

The easiest way to install MagicGuard is using the provided installation scripts:

**Linux/macOS:**
```bash
# Clone the repository
git clone https://github.com/anthonynoelw/magicguard.git
cd magicguard

# Make the script executable
chmod +x install.sh

# Run the installation script
./install.sh

# For development installation with all dev tools
./install.sh --dev

# With Docker verification
./install.sh --docker
```

**Windows PowerShell:**
```powershell
# Clone the repository
git clone https://github.com/anthonynoelw/magicguard.git
cd magicguard

# Run the installation script
.\install.ps1

# For development installation with all dev tools
.\install.ps1 -Dev

# With Docker verification
.\install.ps1 -Docker
```

The installation scripts will:
- ✓ Verify Python 3.11+ is installed
- ✓ Create and activate a virtual environment
- ✓ Install MagicGuard and all dependencies
- ✓ Initialize the signature database
- ✓ Verify the installation
- ✓ Optionally install development tools
- ✓ Optionally verify Docker setup

### Manual Installation

If you prefer to install manually:

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

``` folder
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

MagicGuard includes production-ready Docker support with multi-architecture images and comprehensive security hardening.

### Quick Start

```bash
# Build the image
docker build -t magicguard:latest -f docker/Dockerfile .

# Scan a file
docker run --rm \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan /scan/document.pdf

# Scan directory recursively
docker run --rm \
  -v "$PWD/files:/scan:ro" \
  magicguard:latest scan-dir --recursive /scan

# List supported file types
docker run --rm magicguard:latest list-signatures
```

### Using Docker Compose

```bash
# Scan a single file
SCAN_DIR="$PWD/samples" docker-compose -f docker/docker-compose.yml run --rm scanner scan /scan/file.pdf

# Scan directory with batch scanner
SCAN_DIR="$PWD/samples" docker-compose -f docker/docker-compose.yml run --rm batch-scanner

# Check status
docker-compose -f docker/docker-compose.yml run --rm status
```

### Multi-Architecture Support

Build for multiple platforms (amd64, arm64, arm/v7):

```bash
# Using the build script
./docker/build-multiarch.sh

# Build and push to registry
PUSH=true IMAGE_NAME=yourusername/magicguard ./docker/build-multiarch.sh
```

### Security Features

- **Multi-stage Alpine build** - Minimal 91MB image
- **Non-root user** (UID 1000) for enhanced security
- **4 security hardening levels** - From basic to maximum paranoid
- **Read-only filesystem** support with tmpfs
- **Capability dropping** - Remove all unnecessary Linux capabilities
- **Seccomp profiles** - Restrict system calls
- **Network isolation** - Optional no-network mode

For comprehensive Docker documentation, see **[docker/README.md](docker/README.md)** (400+ lines covering deployment, security, CI/CD, and troubleshooting).

## 🔧 Configuration

### Local Installation

MagicGuard stores data in `~/.magicguard/`:

``` folder
~/.magicguard/
├── data/
│   └── signatures.db    # Signature database
└── log/
    └── YYYY-MM-DD.log   # Daily rotating logs
```

### Docker Deployment

When running in Docker, paths are:

- Database: `/data/signatures.db` (use named volumes for persistence)
- Logs: `/logs/` (mount as volume or use tmpfs)
- Scan files: `/scan/` (mount read-only)

See [docker/README.md](docker/README.md) for volume configuration details.

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

### Anthony Weiß

- Email: [weissanthony.code@gmail.com](weissanthony.code@gmail.com)
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
