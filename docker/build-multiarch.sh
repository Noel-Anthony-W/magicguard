#!/usr/bin/env bash
# =============================================================================
# Multi-Architecture Build Script for MagicGuard
# =============================================================================
# Builds Docker images for multiple CPU architectures
# Requires: Docker Buildx
# =============================================================================

set -euo pipefail

# Configuration
IMAGE_NAME="${IMAGE_NAME:-magicguard}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64,linux/arm/v7}"
DOCKERFILE="${DOCKERFILE:-docker/Dockerfile}"
PUSH="${PUSH:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_buildx() {
    if ! docker buildx version &> /dev/null; then
        log_error "Docker Buildx is not installed"
        log_info "Install with: docker buildx install"
        exit 1
    fi
    log_info "Docker Buildx found"
}

# Create or use existing builder
setup_builder() {
    local BUILDER_NAME="magicguard-multiarch"
    
    if docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
        log_info "Using existing builder: $BUILDER_NAME"
        docker buildx use "$BUILDER_NAME"
    else
        log_info "Creating new builder: $BUILDER_NAME"
        docker buildx create --name "$BUILDER_NAME" --use
        docker buildx inspect --bootstrap
    fi
}

# Build the image
build_image() {
    log_info "Building image: $IMAGE_NAME:$IMAGE_TAG"
    log_info "Platforms: $PLATFORMS"
    log_info "Dockerfile: $DOCKERFILE"
    
    local BUILD_ARGS=(
        "buildx" "build"
        "--platform" "$PLATFORMS"
        "--file" "$DOCKERFILE"
        "--tag" "$IMAGE_NAME:$IMAGE_TAG"
        "."
    )
    
    if [ "$PUSH" = "true" ]; then
        BUILD_ARGS+=("--push")
        log_warn "Image will be pushed to registry"
    else
        BUILD_ARGS+=("--load")
        log_info "Image will be loaded locally (single platform only)"
    fi
    
    log_info "Running build command..."
    docker "${BUILD_ARGS[@]}"
    
    if [ $? -eq 0 ]; then
        log_info "✓ Build successful!"
    else
        log_error "✗ Build failed"
        exit 1
    fi
}

# Main execution
main() {
    log_info "=== MagicGuard Multi-Architecture Build ==="
    
    # Change to project root
    cd "$(dirname "$0")/.."
    
    check_buildx
    setup_builder
    build_image
    
    log_info "=== Build Complete ==="
    log_info "Image: $IMAGE_NAME:$IMAGE_TAG"
    
    if [ "$PUSH" = "false" ]; then
        log_info ""
        log_info "To push to registry, run:"
        log_info "  PUSH=true $0"
    fi
}

# Run main
main "$@"
