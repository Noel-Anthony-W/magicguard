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

MagicGuard is highly configurable via environment variables, allowing flexible deployment across development, testing, and production environments.

### Configuration Files

MagicGuard supports environment-based configuration:

1. **`.env.example`** - Template with all available configuration options (safe to commit)
2. **`.env`** - Your local configuration (automatically ignored by git)

```bash
# Create your local configuration
cp .env.example .env

# Edit with your preferred values
vim .env  # or nano, code, etc.
```

### Environment Variables

All configuration variables are **optional** with sensible defaults:

#### Core Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MAGICGUARD_DB_PATH` | SQLite database file location | `~/.magicguard/data/signatures.db` | `/var/lib/magicguard/signatures.db` |
| `MAGICGUARD_LOG_LEVEL` | Logging verbosity | `DEBUG` (dev), `INFO` (prod) | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `MAGICGUARD_LOG_DIR` | Directory for log files | `~/.magicguard/log` | `/var/log/magicguard` |
| `MAGICGUARD_DATA_DIR` | Application data directory | `~/.magicguard/data` | `/var/lib/magicguard/data` || `MAGICGUARD_MAX_FILE_SIZE` | Maximum file size in bytes | `104857600` (100MB) | `209715200` (200MB), `52428800` (50MB) |
#### Docker-Specific Variables

| Variable | Description | Default | Used In |
|----------|-------------|---------|---------|
| `SCAN_DIR` | Directory to mount as `/scan` | `./scan` | docker-compose.yml |
| `LOG_DIR` | Directory to mount as `/logs` | `./logs` | docker-compose.yml |
| `LOG_LEVEL` | Container log level | `INFO` | docker-compose.yml |

### Configuration Examples

#### Development Setup

```bash
# .env for local development
MAGICGUARD_LOG_LEVEL=DEBUG
MAGICGUARD_DB_PATH=/tmp/magicguard-dev/signatures.db
MAGICGUARD_LOG_DIR=/tmp/magicguard-dev/logs
MAGICGUARD_MAX_FILE_SIZE=52428800  # 50MB for testing
```

```bash
# Use development settings
magicguard scan document.pdf --verbose
```

#### Production Setup

```bash
# .env for production deployment
MAGICGUARD_LOG_LEVEL=WARNING
MAGICGUARD_DB_PATH=/var/lib/magicguard/signatures.db
MAGICGUARD_LOG_DIR=/var/log/magicguard
MAGICGUARD_DATA_DIR=/var/lib/magicguard/data
MAGICGUARD_MAX_FILE_SIZE=209715200  # 200MB for production
```

#### Testing/CI Setup

```bash
# Isolated testing environment
export MAGICGUARD_DB_PATH=/tmp/test-magicguard/signatures.db
export MAGICGUARD_LOG_DIR=/tmp/test-magicguard/logs
export MAGICGUARD_LOG_LEVEL=DEBUG

pytest tests/ --cov
```

#### Docker Configuration

```bash
# docker-compose configuration
SCAN_DIR="$PWD/samples"
LOG_DIR="$PWD/logs"
LOG_LEVEL=INFO

docker-compose -f docker/docker-compose.yml run --rm scanner scan /scan/file.pdf
```

### Application Limits

#### Configurable Limits

These can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAGICGUARD_MAX_FILE_SIZE` | 104857600 (100MB) | Maximum file size to process |

#### Fixed Limits

These constants are defined in [`src/magicguard/utils/config.py`](src/magicguard/utils/config.py) and **cannot** be overridden:

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_SIGNATURE_LENGTH` | 64 bytes | Maximum magic byte signature length |
| `MAX_LOG_FILES` | 30 files | Keep 30 days of daily log files |

### Directory Structure

#### Local Installation

MagicGuard stores data in `~/.magicguard/`:

```
~/.magicguard/
├── data/
│   └── signatures.db    # SQLite signature database
└── log/
    └── 2025-12-28.log   # Daily rotating logs (YYYY-MM-DD.log)
```

#### Docker Deployment

When running in Docker, paths are:

- **Database**: `/data/signatures.db` (use named volumes for persistence)
- **Logs**: `/logs/` (mount as volume or use tmpfs)
- **Scan files**: `/scan/` (mount read-only for security)

See [docker/README.md](docker/README.md) for comprehensive volume configuration.

### Code Usage

The configuration system is used throughout the codebase:

```python
from magicguard.utils.config import (
    get_database_path,  # Gets DB path (env or default)
    get_log_level,      # Gets log level (env or default)
    get_log_dir,        # Gets log directory (env or default)
    get_max_file_size,  # Gets max file size (env or default)
)

# Database automatically uses configured path
from magicguard.core.database import Database
db = Database()  # Uses MAGICGUARD_DB_PATH or default

# Logger respects MAGICGUARD_LOG_LEVEL
from magicguard.utils.logger import get_logger
logger = get_logger(__name__)  # Uses configured log level

# Validator respects MAGICGUARD_MAX_FILE_SIZE
from magicguard.core.validator import FileValidator
validator = FileValidator()  # Uses MAGICGUARD_MAX_FILE_SIZE or default
logger = get_logger(__name__)  # Uses configured log level
```

### Security Considerations

⚠️ **Important Security Notes:**

1. **Never commit `.env`** - Already in `.gitignore`
2. **Use restrictive permissions**: `chmod 600 .env`
3. **Use absolute paths** in production
4. **Validate user-provided paths** before using
5. **Avoid storing secrets** in environment variables when possible

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
