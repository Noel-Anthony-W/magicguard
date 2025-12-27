# =============================================================================
# MagicGuard - Secure Multi-Architecture Docker Image
# =============================================================================
# Supports: linux/amd64, linux/arm64, linux/arm/v7
# Base: Python 3.11 Alpine (minimal attack surface)
# Security: Non-root user, read-only rootfs compatible, minimal privileges
# =============================================================================

# Build argument for Python version (allows easy upgrades)
ARG PYTHON_VERSION=3.11

# =============================================================================
# Stage 1: Builder - Install dependencies and build wheel
# =============================================================================
FROM python:${PYTHON_VERSION}-alpine AS builder

# Install build dependencies (removed after build to reduce image size)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    && rm -rf /var/cache/apk/*

# Create virtual environment for isolated dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only dependency files first (better layer caching)
COPY pyproject.toml /tmp/
COPY README.md /tmp/

# Install Python dependencies directly from pyproject.toml
WORKDIR /tmp
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir "click>=8.1.0" "rich>=13.0.0"

# Copy source code directly into site-packages
# This avoids the setuptools .egg-info conflict issue
# Copy all Python files including __init__.py
COPY src/magicguard/__init__.py /opt/venv/lib/python3.11/site-packages/magicguard/
COPY src/magicguard/cli/ /opt/venv/lib/python3.11/site-packages/magicguard/cli/
COPY src/magicguard/core/ /opt/venv/lib/python3.11/site-packages/magicguard/core/
COPY src/magicguard/utils/ /opt/venv/lib/python3.11/site-packages/magicguard/utils/
COPY data/ /opt/venv/lib/python3.11/site-packages/magicguard/data/

# Create entry point script
RUN echo '#!/opt/venv/bin/python' > /opt/venv/bin/magicguard && \
    echo 'import sys' >> /opt/venv/bin/magicguard && \
    echo 'from magicguard.cli.commands import cli' >> /opt/venv/bin/magicguard && \
    echo 'if __name__ == "__main__":' >> /opt/venv/bin/magicguard && \
    echo '    sys.exit(cli())' >> /opt/venv/bin/magicguard && \
    chmod +x /opt/venv/bin/magicguard

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:${PYTHON_VERSION}-alpine

# Metadata labels (OCI standard)
LABEL org.opencontainers.image.title="MagicGuard"
LABEL org.opencontainers.image.description="File type validator using magic bytes"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="Anthony Weiß <weiss.anthonynoel@gmail.com>"
LABEL org.opencontainers.image.licenses="GPL-3.0"
LABEL org.opencontainers.image.source="https://github.com/anthonynoelw/magicguard"

# Install runtime dependencies only (no build tools)
RUN apk add --no-cache \
    libffi \
    && rm -rf /var/cache/apk/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MAGICGUARD_DB_PATH=/data/signatures.db \
    MAGICGUARD_LOG_DIR=/logs

# Create non-root user for security
# UID/GID 1000 is common for first user, making it easy to match host permissions
RUN addgroup -g 1000 magicguard && \
    adduser -D -u 1000 -G magicguard -h /home/magicguard magicguard

# Create application directories with proper permissions
RUN mkdir -p /data /logs /scan && \
    chown -R magicguard:magicguard /data /logs /scan /home/magicguard

# Switch to non-root user
USER magicguard

# Set working directory
WORKDIR /home/magicguard

# Health check (verifies CLI is working)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD magicguard status || exit 1

# Default entrypoint - allows easy command override
ENTRYPOINT ["magicguard"]

# Default command - shows help if no command provided
CMD ["--help"]

# =============================================================================
# Build Instructions:
# =============================================================================
# Single architecture:
#   docker build -t magicguard:latest -f docker/Dockerfile .
#
# Multi-architecture (requires buildx):
#   docker buildx create --name multiarch --use
#   docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 \
#     -t magicguard:latest -f docker/Dockerfile . --load
#
# =============================================================================
# Security Hardening Options (configure in docker-compose.yml or run command):
# =============================================================================
# --read-only                    # Read-only root filesystem
# --tmpfs /tmp:noexec,nosuid     # Writable temp with restrictions
# --cap-drop=ALL                 # Drop all capabilities
# --security-opt=no-new-privileges # Prevent privilege escalation
# --pids-limit 100               # Limit number of processes
# --memory 512m                  # Memory limit
# --cpus 1.0                     # CPU limit
# =============================================================================
