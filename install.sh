#!/usr/bin/env bash
#
# MagicGuard Installation Script for Linux/macOS
# 
# This script automates the installation of MagicGuard including:
# - Python version verification (3.11+)
# - Virtual environment creation
# - Dependency installation
# - Development tools setup (optional)
# - Docker verification (optional)
#
# Usage:
#   ./install.sh              # Standard installation
#   ./install.sh --dev        # Install with development dependencies
#   ./install.sh --docker     # Verify Docker setup
#   ./install.sh --help       # Show help message
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.11"
VENV_DIR=".venv"
DEV_MODE=false
DOCKER_CHECK=false

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════╗
║                                               ║
║           MagicGuard Installation             ║
║                                               ║
║   File Type Validator using Magic Bytes       ║
║                                               ║
╚═══════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Show help message
show_help() {
    cat << EOF
MagicGuard Installation Script

Usage: $0 [OPTIONS]

Options:
    --dev           Install with development dependencies
    --docker        Verify Docker setup after installation
    --help, -h      Show this help message

Examples:
    $0              # Standard installation
    $0 --dev        # Install with dev tools (pytest, black, mypy, etc.)
    $0 --docker     # Install and verify Docker setup

After installation, activate the virtual environment:
    source .venv/bin/activate

Then run MagicGuard:
    magicguard --help
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev)
                DEV_MODE=true
                shift
                ;;
            --docker)
                DOCKER_CHECK=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check if Python version is sufficient
check_python_version() {
    log_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python ${PYTHON_MIN_VERSION} or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    MIN_MAJOR=$(echo $PYTHON_MIN_VERSION | cut -d. -f1)
    MIN_MINOR=$(echo $PYTHON_MIN_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt "$MIN_MAJOR" ] || \
       ([ "$PYTHON_MAJOR" -eq "$MIN_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$MIN_MINOR" ]); then
        log_error "Python ${PYTHON_MIN_VERSION}+ is required. Found: ${PYTHON_VERSION}"
        log_info "Please install Python ${PYTHON_MIN_VERSION} or higher from https://www.python.org/downloads/"
        exit 1
    fi
    
    log_success "Python ${PYTHON_VERSION} detected"
}

# Create virtual environment
create_venv() {
    log_info "Creating virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        log_warning "Virtual environment already exists at ${VENV_DIR}"
        read -p "Do you want to remove and recreate it? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
            log_info "Removed existing virtual environment"
        else
            log_info "Using existing virtual environment"
            return 0
        fi
    fi
    
    python3 -m venv "$VENV_DIR"
    log_success "Virtual environment created at ${VENV_DIR}"
}

# Activate virtual environment
activate_venv() {
    log_info "Activating virtual environment..."
    source "${VENV_DIR}/bin/activate"
    log_success "Virtual environment activated"
}

# Upgrade pip
upgrade_pip() {
    log_info "Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    log_success "pip upgraded to $(pip --version | awk '{print $2}')"
}

# Install MagicGuard
install_magicguard() {
    log_info "Installing MagicGuard..."
    
    if [ "$DEV_MODE" = true ]; then
        log_info "Installing with development dependencies..."
        pip install -e ".[dev]"
    else
        pip install -e .
    fi
    
    log_success "MagicGuard installed successfully"
}

# Initialize database
initialize_database() {
    log_info "Initializing signature database..."
    
    # Run a simple command to trigger database initialization
    magicguard status > /dev/null 2>&1 || true
    
    log_success "Database initialized"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    if ! command -v magicguard &> /dev/null; then
        log_error "MagicGuard command not found. Installation may have failed."
        exit 1
    fi
    
    MAGICGUARD_VERSION=$(magicguard --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
    log_success "MagicGuard v${MAGICGUARD_VERSION} is ready to use"
    
    # Show status
    echo ""
    log_info "Running status check..."
    magicguard status --verbose
}

# Check Docker setup
check_docker() {
    log_info "Checking Docker setup..."
    
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed"
        log_info "To use MagicGuard with Docker, install Docker from https://docs.docker.com/get-docker/"
        return 0
    fi
    
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
    log_success "Docker ${DOCKER_VERSION} detected"
    
    # Check if docker-compose is available
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | tr -d ',')
        log_success "Docker Compose ${COMPOSE_VERSION} detected"
    else
        log_warning "Docker Compose not found. Install it for full Docker functionality."
    fi
    
    # Offer to build Docker image
    echo ""
    read -p "Do you want to build the MagicGuard Docker image? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Building Docker image..."
        docker build -t magicguard:latest -f docker/Dockerfile .
        log_success "Docker image built successfully"
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo -e "   ${BLUE}source ${VENV_DIR}/bin/activate${NC}"
    echo ""
    echo "2. Try scanning a file:"
    echo -e "   ${BLUE}magicguard scan <file_path>${NC}"
    echo ""
    echo "3. List supported file types:"
    echo -e "   ${BLUE}magicguard list-signatures${NC}"
    echo ""
    echo "4. View help for all commands:"
    echo -e "   ${BLUE}magicguard --help${NC}"
    echo ""
    
    if [ "$DEV_MODE" = true ]; then
        echo "Development tools installed:"
        echo "  - Run tests: ${BLUE}pytest${NC}"
        echo "  - Format code: ${BLUE}black src/ tests/${NC}"
        echo "  - Lint code: ${BLUE}ruff check src/ tests/${NC}"
        echo "  - Type check: ${BLUE}mypy src/${NC}"
        echo ""
    fi
    
    if [ "$DOCKER_CHECK" = true ]; then
        echo "Docker commands:"
        echo "  - Scan with Docker: ${BLUE}docker run --rm -v \"\$PWD/samples:/scan:ro\" magicguard:latest scan /scan/file.pdf${NC}"
        echo ""
    fi
    
    echo "Documentation: https://github.com/anthonynoelw/magicguard#readme"
    echo ""
}

# Main installation flow
main() {
    print_banner
    parse_args "$@"
    
    # Pre-flight checks
    check_python_version
    
    # Installation steps
    create_venv
    activate_venv
    upgrade_pip
    install_magicguard
    initialize_database
    verify_installation
    
    # Optional Docker check
    if [ "$DOCKER_CHECK" = true ]; then
        check_docker
    fi
    
    # Print success message and next steps
    print_next_steps
}

# Run main function
main "$@"
