# MagicGuard Docker Deployment Guide

This guide covers deploying MagicGuard in Docker containers with multi-architecture support and comprehensive security hardening options.

## Table of Contents

- [Quick Start](#quick-start)
- [Building Images](#building-images)
- [Running Containers](#running-containers)
- [Docker Compose](#docker-compose)
- [Security Hardening](#security-hardening)
- [Multi-Architecture Support](#multi-architecture-support)
- [Environment Variables](#environment-variables)
- [Volume Mounts](#volume-mounts)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone and navigate to project
cd magicguard

# Scan a single file
docker-compose run --rm scanner scan /scan/document.pdf

# Scan a directory
docker-compose run --rm batch-scanner scan-dir --recursive /scan

# List supported file types
docker-compose run --rm list-sigs list-signatures

# Check status
docker-compose run --rm status status
```

### Using Docker Directly

```bash
# Build the image
docker build -t magicguard:latest -f docker/Dockerfile .

# Scan a file
docker run --rm -v "$PWD/samples:/scan:ro" magicguard:latest scan /scan/test.pdf

# Interactive shell
docker run --rm -it -v "$PWD/samples:/scan:ro" magicguard:latest /bin/sh
```

## Building Images

### Single Architecture Build

Build for your current platform:

```bash
docker build -t magicguard:latest -f docker/Dockerfile .
```

### Multi-Architecture Build

Use the provided build script for cross-platform images:

```bash
# Build for all platforms (amd64, arm64, arm/v7)
./docker/build-multiarch.sh

# Build and push to registry
PUSH=true IMAGE_NAME=myregistry/magicguard ./docker/build-multiarch.sh

# Build with custom tag
IMAGE_TAG=v1.0.0 ./docker/build-multiarch.sh

# Build for specific platforms only
PLATFORMS="linux/amd64,linux/arm64" ./docker/build-multiarch.sh

# Build and load into local Docker (single platform only)
./docker/build-multiarch.sh --load
```

### Manual Multi-Architecture Build

```bash
# Create buildx builder (first time only)
docker buildx create --name magicguard-builder --use
docker buildx inspect --bootstrap

# Build and push
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag myregistry/magicguard:latest \
  --file docker/Dockerfile \
  --push \
  .

# Build and load locally (single platform)
docker buildx build \
  --platform linux/amd64 \
  --tag magicguard:latest \
  --file docker/Dockerfile \
  --load \
  .
```

### Build Arguments

Customize the build with build arguments:

```bash
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  -t magicguard:python312 \
  -f docker/Dockerfile \
  .
```

Available build arguments:
- `PYTHON_VERSION` - Python version to use (default: 3.11)

## Running Containers

### Basic Usage

```bash
# Show help
docker run --rm magicguard:latest --help

# Scan a single file
docker run --rm \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan /scan/document.pdf

# Scan with verbose output
docker run --rm \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan --verbose /scan/document.pdf

# Scan directory recursively
docker run --rm \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan-dir --recursive /scan

# Filter by extensions
docker run --rm \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan-dir --extensions pdf,jpg,png /scan

# List supported signatures
docker run --rm magicguard:latest list-signatures

# Check container status
docker run --rm magicguard:latest status
```

### Persistent Data

Use a named volume for persistent signature database:

```bash
# Create volume
docker volume create magicguard-data

# Run with persistent data
docker run --rm \
  -v magicguard-data:/data \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan /scan/file.pdf

# Run with custom logs directory
docker run --rm \
  -v magicguard-data:/data \
  -v "$PWD/logs:/logs" \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan --verbose /scan/file.pdf
```

### Interactive Mode

```bash
docker run --rm -it \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest /bin/sh

# Inside container:
magicguard scan /scan/test.pdf
magicguard list-signatures
exit
```

## Docker Compose

### Service Configurations

The `docker-compose.yml` provides four pre-configured services:

#### 1. Scanner Service (Interactive)

For scanning individual files:

```bash
docker-compose run --rm scanner scan /scan/document.pdf
docker-compose run --rm scanner scan --verbose /scan/suspicious.exe
```

#### 2. Batch Scanner Service (Automated)

For recursive directory scanning with full security:

```bash
# Scan all files
docker-compose run --rm batch-scanner

# Override command
docker-compose run --rm batch-scanner scan-dir --extensions pdf,docx /scan
```

#### 3. Status Service

Quick health check:

```bash
docker-compose run --rm status
```

#### 4. List Signatures Service

View supported file types:

```bash
docker-compose run --rm list-sigs
```

### Customizing Compose Services

Edit `docker-compose.yml` to:

1. **Change scan directory**: Update `volumes` section
   ```yaml
   volumes:
     - /path/to/your/files:/scan:ro
   ```

2. **Enable logging to host**: Uncomment logs volume
   ```yaml
   volumes:
     - ./logs:/logs
   ```

3. **Adjust security level**: See [Security Hardening](#security-hardening)

4. **Set resource limits**: Uncomment `deploy.resources`
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 256M
   ```

## Security Hardening

The Docker configuration supports **four levels of security hardening**. Choose based on your threat model:

### Level 1: Basic Security (Default)

Minimal hardening suitable for trusted environments:

```yaml
security_opt:
  - no-new-privileges:true
```

```bash
docker run --rm \
  --security-opt=no-new-privileges:true \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan /scan/file.pdf
```

**Features:**
- Non-root user (UID 1000)
- No privilege escalation
- Read-only volume mounts where possible

### Level 2: Moderate Security

Enhanced security for production environments:

```yaml
read_only: true
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
tmpfs:
  - /tmp:size=10M,mode=1777
  - /data:size=50M,mode=0755
```

```bash
docker run --rm \
  --read-only \
  --security-opt=no-new-privileges:true \
  --cap-drop=ALL \
  --tmpfs=/tmp:size=10M,mode=1777 \
  --tmpfs=/data:size=50M,mode=0755 \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan /scan/file.pdf
```

**Features:**
- Read-only root filesystem
- All capabilities dropped
- Temporary filesystems for writable directories
- Limited tmpfs sizes

### Level 3: High Security

Strict security for sensitive operations:

```yaml
read_only: true
security_opt:
  - no-new-privileges:true
  - seccomp=/path/to/seccomp-profile.json
cap_drop:
  - ALL
tmpfs:
  - /tmp:size=10M,mode=1777,noexec,nosuid,nodev
  - /data:size=50M,mode=0755,nosuid,nodev
pids_limit: 50
network_mode: "none"
```

```bash
docker run --rm \
  --read-only \
  --security-opt=no-new-privileges:true \
  --security-opt=seccomp=docker/seccomp-profile.json \
  --cap-drop=ALL \
  --tmpfs=/tmp:size=10M,mode=1777,noexec,nosuid,nodev \
  --tmpfs=/data:size=50M,mode=0755,nosuid,nodev \
  --pids-limit=50 \
  --network=none \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan /scan/file.pdf
```

**Features:**
- Seccomp profile (custom syscall filtering)
- No network access
- Process limit enforcement
- Hardened tmpfs mounts (noexec, nosuid, nodev)

### Level 4: Maximum Security

Paranoid security for untrusted file scanning:

```yaml
read_only: true
security_opt:
  - no-new-privileges:true
  - seccomp=/path/to/seccomp-profile.json
  - apparmor=docker-default
cap_drop:
  - ALL
tmpfs:
  - /tmp:size=5M,mode=1777,noexec,nosuid,nodev
  - /data:size=25M,mode=0755,nosuid,nodev
pids_limit: 20
network_mode: "none"
deploy:
  resources:
    limits:
      cpus: '0.25'
      memory: 128M
```

```bash
docker run --rm \
  --read-only \
  --security-opt=no-new-privileges:true \
  --security-opt=seccomp=docker/seccomp-profile.json \
  --security-opt=apparmor=docker-default \
  --cap-drop=ALL \
  --tmpfs=/tmp:size=5M,mode=1777,noexec,nosuid,nodev \
  --tmpfs=/data:size=25M,mode=0755,nosuid,nodev \
  --pids-limit=20 \
  --network=none \
  --cpus=0.25 \
  --memory=128m \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan /scan/file.pdf
```

**Features:**
- All Level 3 features
- AppArmor profile enforcement
- Aggressive resource limits (CPU, memory)
- Minimal tmpfs sizes
- Strict process limits

### Creating Custom Seccomp Profile

See `docker/seccomp-profile.json` for a custom seccomp profile that restricts system calls to the minimum required for file validation.

## Multi-Architecture Support

MagicGuard supports three architectures:

- **linux/amd64** - x86_64 systems (Intel/AMD)
- **linux/arm64** - ARM 64-bit (Apple Silicon, AWS Graviton, Raspberry Pi 4)
- **linux/arm/v7** - ARM 32-bit (Raspberry Pi 3, older ARM boards)

### Building Multi-Arch Images

```bash
# Using the build script (recommended)
./docker/build-multiarch.sh

# Push to Docker Hub
PUSH=true IMAGE_NAME=yourusername/magicguard ./docker/build-multiarch.sh

# Push to private registry
PUSH=true IMAGE_NAME=registry.example.com/magicguard ./docker/build-multiarch.sh
```

### Pulling Multi-Arch Images

Docker automatically pulls the correct architecture:

```bash
# On amd64 system
docker pull yourusername/magicguard:latest  # pulls linux/amd64

# On ARM system
docker pull yourusername/magicguard:latest  # pulls linux/arm64 or linux/arm/v7
```

### Testing Different Architectures

Use QEMU for cross-architecture testing:

```bash
# Install QEMU (if not already installed)
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Test ARM image on x86_64
docker run --rm --platform linux/arm64 magicguard:latest --version
```

## Environment Variables

Configure MagicGuard behavior via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MAGICGUARD_DB_PATH` | Path to signature database | `/data/signatures.db` |
| `MAGICGUARD_LOG_DIR` | Directory for log files | `/logs` |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `PYTHONUNBUFFERED` | Disable Python output buffering | `1` |
| `PYTHONDONTWRITEBYTECODE` | Disable .pyc file creation | `1` |

### Setting Environment Variables

```bash
# Docker run
docker run --rm \
  -e LOG_LEVEL=DEBUG \
  -e MAGICGUARD_DB_PATH=/data/custom.db \
  -v "$PWD/samples:/scan:ro" \
  magicguard:latest scan --verbose /scan/file.pdf

# Docker Compose
services:
  scanner:
    environment:
      - LOG_LEVEL=DEBUG
      - MAGICGUARD_DB_PATH=/data/custom.db
```

## Volume Mounts

### Required Volumes

1. **Scan Directory** (`/scan`):
   ```bash
   -v /path/to/files:/scan:ro
   ```
   - Mount files to be scanned
   - **Always use read-only (`:ro`)** when scanning untrusted files

2. **Data Directory** (`/data`):
   ```bash
   -v magicguard-data:/data
   ```
   - Stores signature database
   - Use named volume for persistence

3. **Logs Directory** (`/logs`):
   ```bash
   -v ./logs:/logs
   ```
   - Optional: persist logs to host
   - Useful for debugging and auditing

### Volume Permissions

The container runs as UID 1000. Ensure host directories are accessible:

```bash
# Make directories accessible
sudo chown -R 1000:1000 /path/to/scan
sudo chmod -R 755 /path/to/scan

# Or use current user
chown -R $(id -u):$(id -g) ./samples
```

## Health Checks

### Built-in Health Check

The Dockerfile includes a health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD magicguard status || exit 1
```

### Checking Container Health

```bash
# Docker
docker inspect --format='{{.State.Health.Status}}' container_name

# Docker Compose
docker-compose ps
```

### Custom Health Checks

Override the health check:

```bash
docker run --rm -d \
  --health-cmd="magicguard list-signatures | grep -q 'pdf'" \
  --health-interval=60s \
  magicguard:latest
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs container_name

# Run with debug logging
docker run --rm -e LOG_LEVEL=DEBUG magicguard:latest status
```

### Permission Denied Errors

```bash
# Fix volume permissions
sudo chown -R 1000:1000 /path/to/volume

# Or run as root (NOT RECOMMENDED)
docker run --rm --user=root magicguard:latest scan /scan/file.pdf
```

### Database Errors

```bash
# Reset database (deletes all data!)
docker volume rm magicguard-data

# Re-initialize
docker run --rm -v magicguard-data:/data magicguard:latest status
```

### Out of Memory

```bash
# Increase memory limit
docker run --rm --memory=512m magicguard:latest scan-dir /scan

# Or in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 512M
```

### Multi-Arch Build Fails

```bash
# Ensure buildx is installed
docker buildx version

# Create new builder
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# Install QEMU
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

## CI/CD Integration

### Jenkins

```groovy
pipeline {
    agent any
    stages {
        stage('Build Multi-Arch') {
            steps {
                sh './docker/build-multiarch.sh'
            }
        }
        stage('Test') {
            steps {
                sh 'docker run --rm magicguard:latest scan /scan/test.pdf'
            }
        }
        stage('Push') {
            steps {
                sh 'PUSH=true IMAGE_NAME=registry/magicguard ./docker/build-multiarch.sh'
            }
        }
    }
}
```

### GitHub Actions

```yaml
name: Build and Push
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      - name: Login to Registry
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - name: Build and Push
        run: |
          PUSH=true IMAGE_NAME=${{ secrets.DOCKER_USERNAME }}/magicguard ./docker/build-multiarch.sh
```

### GitLab CI

```yaml
build:
  stage: build
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - PUSH=true IMAGE_NAME=$CI_REGISTRY_IMAGE ./docker/build-multiarch.sh
```

## Best Practices

### Security

1. **Always mount scan directories read-only**: `-v /path:/scan:ro`
2. **Use named volumes for data**: `docker volume create magicguard-data`
3. **Run with security hardening**: Start with Level 2, increase as needed
4. **Keep images updated**: Rebuild regularly to get security patches
5. **Scan untrusted files in isolated containers**: Use `--network=none`
6. **Limit resources**: Set CPU and memory limits for untrusted workloads
7. **Use seccomp profiles**: Restrict system calls to minimum required

### Performance

1. **Use multi-stage builds**: Already implemented in Dockerfile
2. **Minimize image size**: Alpine base keeps image ~50MB
3. **Cache build dependencies**: Layer ordering optimized
4. **Use .dockerignore**: Reduces build context (already configured)
5. **Batch scanning**: Use `scan-dir` for multiple files
6. **Persistent volumes**: Avoid re-initializing database on each run

### Monitoring

1. **Enable health checks**: Built-in, monitor with orchestrator
2. **Collect logs**: Mount `/logs` volume to host
3. **Set DEBUG level for troubleshooting**: `-e LOG_LEVEL=DEBUG`
4. **Monitor resource usage**: `docker stats container_name`
5. **Track scan results**: Parse JSON output for metrics

### Production Deployment

1. **Use specific version tags**: `:v1.0.0` not `:latest`
2. **Implement restart policies**: `--restart=unless-stopped`
3. **Set up log rotation**: Configure Docker logging driver
4. **Use orchestration**: Docker Compose, Swarm, or Kubernetes
5. **Automate builds**: CI/CD pipeline for updates
6. **Test across architectures**: Validate ARM builds if deploying to ARM
7. **Document configuration**: Track security level and customizations

### Development

1. **Use docker-compose for local testing**: Simplified workflow
2. **Mount source code for live updates**: Add volume during dev
3. **Override entrypoint for debugging**: `--entrypoint=/bin/sh`
4. **Keep development and production configs separate**: Use profiles
5. **Test multi-arch locally with QEMU**: Catch platform-specific issues

## Additional Resources

- [MagicGuard README](../README.md) - Project overview and usage
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Multi-Platform Images](https://docs.docker.com/build/building/multi-platform/)
- [Seccomp Profiles](https://docs.docker.com/engine/security/seccomp/)

## Support

For issues specific to Docker deployment, please:

1. Check [Troubleshooting](#troubleshooting) section
2. Review Docker logs: `docker logs container_name`
3. Enable debug logging: `-e LOG_LEVEL=DEBUG`
4. Open an issue with logs and configuration details

---

**Version**: 1.0.0  
**Last Updated**: 2024
