#
# MagicGuard Installation Script for Windows PowerShell
#
# This script automates the installation of MagicGuard including:
# - Python version verification (3.11+)
# - Virtual environment creation
# - Dependency installation
# - Development tools setup (optional)
# - Docker verification (optional)
#
# Usage:
#   .\install.ps1              # Standard installation
#   .\install.ps1 -Dev         # Install with development dependencies
#   .\install.ps1 -Docker      # Verify Docker setup
#   .\install.ps1 -Help        # Show help message
#

[CmdletBinding()]
param(
    [switch]$Dev,
    [switch]$Docker,
    [switch]$Help
)

# Configuration
$PythonMinVersion = "3.11"
$VenvDir = ".venv"

# Color functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    switch ($Type) {
        "Info"    { Write-Host "[INFO] " -ForegroundColor Blue -NoNewline; Write-Host $Message }
        "Success" { Write-Host "[SUCCESS] " -ForegroundColor Green -NoNewline; Write-Host $Message }
        "Warning" { Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline; Write-Host $Message }
        "Error"   { Write-Host "[ERROR] " -ForegroundColor Red -NoNewline; Write-Host $Message }
    }
}

# Print banner
function Show-Banner {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║                                               ║" -ForegroundColor Blue
    Write-Host "║           MagicGuard Installation             ║" -ForegroundColor Blue
    Write-Host "║                                               ║" -ForegroundColor Blue
    Write-Host "║   File Type Validator using Magic Bytes       ║" -ForegroundColor Blue
    Write-Host "║                                               ║" -ForegroundColor Blue
    Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""
}

# Show help message
function Show-Help {
    Write-Host "MagicGuard Installation Script for Windows"
    Write-Host ""
    Write-Host "Usage: .\install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "    -Dev        Install with development dependencies"
    Write-Host "    -Docker     Verify Docker setup after installation"
    Write-Host "    -Help       Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "    .\install.ps1           # Standard installation"
    Write-Host "    .\install.ps1 -Dev      # Install with dev tools"
    Write-Host "    .\install.ps1 -Docker   # Install and verify Docker"
    Write-Host ""
    Write-Host "After installation, activate the virtual environment:"
    Write-Host "    .\.venv\Scripts\Activate.ps1"
    Write-Host ""
    Write-Host "Then run MagicGuard:"
    Write-Host "    magicguard --help"
}

# Check Python version
function Test-PythonVersion {
    Write-ColorOutput "Checking Python version..." "Info"
    
    try {
        $pythonCmd = Get-Command python -ErrorAction Stop
    } catch {
        Write-ColorOutput "Python is not installed or not in PATH." "Error"
        Write-ColorOutput "Please install Python $PythonMinVersion or higher from https://www.python.org/downloads/" "Info"
        exit 1
    }
    
    $pythonVersionOutput = python --version 2>&1
    $pythonVersion = [regex]::Match($pythonVersionOutput, '\d+\.\d+\.\d+').Value
    
    if (-not $pythonVersion) {
        Write-ColorOutput "Could not determine Python version." "Error"
        exit 1
    }
    
    $version = [version]$pythonVersion
    $minVersion = [version]$PythonMinVersion
    
    if ($version -lt $minVersion) {
        Write-ColorOutput "Python $PythonMinVersion+ is required. Found: $pythonVersion" "Error"
        Write-ColorOutput "Please install Python $PythonMinVersion or higher from https://www.python.org/downloads/" "Info"
        exit 1
    }
    
    Write-ColorOutput "Python $pythonVersion detected" "Success"
}

# Create virtual environment
function New-VirtualEnvironment {
    Write-ColorOutput "Creating virtual environment..." "Info"
    
    if (Test-Path $VenvDir) {
        Write-ColorOutput "Virtual environment already exists at $VenvDir" "Warning"
        $response = Read-Host "Do you want to remove and recreate it? [y/N]"
        if ($response -match '^[Yy]$') {
            Remove-Item -Recurse -Force $VenvDir
            Write-ColorOutput "Removed existing virtual environment" "Info"
        } else {
            Write-ColorOutput "Using existing virtual environment" "Info"
            return
        }
    }
    
    python -m venv $VenvDir
    Write-ColorOutput "Virtual environment created at $VenvDir" "Success"
}

# Activate virtual environment
function Enable-VirtualEnvironment {
    Write-ColorOutput "Activating virtual environment..." "Info"
    
    $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    
    if (-not (Test-Path $activateScript)) {
        Write-ColorOutput "Activation script not found: $activateScript" "Error"
        exit 1
    }
    
    . $activateScript
    Write-ColorOutput "Virtual environment activated" "Success"
}

# Upgrade pip
function Update-Pip {
    Write-ColorOutput "Upgrading pip..." "Info"
    python -m pip install --upgrade pip --quiet
    $pipVersion = (pip --version).Split()[1]
    Write-ColorOutput "pip upgraded to $pipVersion" "Success"
}

# Install MagicGuard
function Install-MagicGuard {
    Write-ColorOutput "Installing MagicGuard..." "Info"
    
    if ($Dev) {
        Write-ColorOutput "Installing with development dependencies..." "Info"
        pip install -e ".[dev]"
    } else {
        pip install -e .
    }
    
    Write-ColorOutput "MagicGuard installed successfully" "Success"
}

# Initialize database
function Initialize-Database {
    Write-ColorOutput "Initializing signature database..." "Info"
    
    # Run a simple command to trigger database initialization
    magicguard status 2>$null | Out-Null
    
    Write-ColorOutput "Database initialized" "Success"
}

# Verify installation
function Test-Installation {
    Write-ColorOutput "Verifying installation..." "Info"
    
    try {
        $null = Get-Command magicguard -ErrorAction Stop
    } catch {
        Write-ColorOutput "MagicGuard command not found. Installation may have failed." "Error"
        exit 1
    }
    
    $versionOutput = magicguard --version 2>&1
    $version = [regex]::Match($versionOutput, '\d+\.\d+\.\d+').Value
    if (-not $version) { $version = "unknown" }
    
    Write-ColorOutput "MagicGuard v$version is ready to use" "Success"
    
    # Show status
    Write-Host ""
    Write-ColorOutput "Running status check..." "Info"
    magicguard status --verbose
}

# Check Docker setup
function Test-DockerSetup {
    Write-ColorOutput "Checking Docker setup..." "Info"
    
    try {
        $dockerCmd = Get-Command docker -ErrorAction Stop
        $dockerVersion = (docker --version).Split()[2].TrimEnd(',')
        Write-ColorOutput "Docker $dockerVersion detected" "Success"
    } catch {
        Write-ColorOutput "Docker is not installed" "Warning"
        Write-ColorOutput "To use MagicGuard with Docker, install Docker Desktop from https://docs.docker.com/desktop/install/windows-install/" "Info"
        return
    }
    
    # Check docker-compose
    try {
        $composeVersion = (docker-compose --version).Split()[2].TrimEnd(',')
        Write-ColorOutput "Docker Compose $composeVersion detected" "Success"
    } catch {
        Write-ColorOutput "Docker Compose not found." "Warning"
    }
    
    # Offer to build Docker image
    Write-Host ""
    $response = Read-Host "Do you want to build the MagicGuard Docker image? [y/N]"
    if ($response -match '^[Yy]$') {
        Write-ColorOutput "Building Docker image..." "Info"
        docker build -t magicguard:latest -f docker/Dockerfile .
        Write-ColorOutput "Docker image built successfully" "Success"
    }
}

# Print next steps
function Show-NextSteps {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "Installation completed successfully!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host ""
    Write-Host "1. Activate the virtual environment:"
    Write-Host "   .\.venv\Scripts\Activate.ps1" -ForegroundColor Blue
    Write-Host ""
    Write-Host "2. Try scanning a file:"
    Write-Host "   magicguard scan <file_path>" -ForegroundColor Blue
    Write-Host ""
    Write-Host "3. List supported file types:"
    Write-Host "   magicguard list-signatures" -ForegroundColor Blue
    Write-Host ""
    Write-Host "4. View help for all commands:"
    Write-Host "   magicguard --help" -ForegroundColor Blue
    Write-Host ""
    
    if ($Dev) {
        Write-Host "Development tools installed:"
        Write-Host "  - Run tests: pytest" -ForegroundColor Blue
        Write-Host "  - Format code: black src/ tests/" -ForegroundColor Blue
        Write-Host "  - Lint code: ruff check src/ tests/" -ForegroundColor Blue
        Write-Host "  - Type check: mypy src/" -ForegroundColor Blue
        Write-Host ""
    }
    
    if ($Docker) {
        Write-Host "Docker commands:"
        Write-Host '  - Scan with Docker: docker run --rm -v "$PWD/samples:/scan:ro" magicguard:latest scan /scan/file.pdf' -ForegroundColor Blue
        Write-Host ""
    }
    
    Write-Host "Documentation: https://github.com/anthonynoelw/magicguard#readme"
    Write-Host ""
}

# Main installation flow
function Start-Installation {
    Show-Banner
    
    if ($Help) {
        Show-Help
        exit 0
    }
    
    # Pre-flight checks
    Test-PythonVersion
    
    # Installation steps
    New-VirtualEnvironment
    Enable-VirtualEnvironment
    Update-Pip
    Install-MagicGuard
    Initialize-Database
    Test-Installation
    
    # Optional Docker check
    if ($Docker) {
        Test-DockerSetup
    }
    
    # Print success message and next steps
    Show-NextSteps
}

# Run main function
Start-Installation
