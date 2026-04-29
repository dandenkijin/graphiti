#!/bin/bash

# Build script for LadybugDB MCP Server Docker image
# Usage: ./build-ladybugdb.sh [tag] [version]

set -e

# Default values
TAG=${1:-"latest"}
GRAPHITI_CORE_VERSION=${2:-"0.28.1"}
MCP_SERVER_VERSION=${3:-"1.0.0"}
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=${4:-$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")}

# Build arguments
BUILD_ARGS=(
    "--build-arg" "GRAPHITI_CORE_VERSION=${GRAPHITI_CORE_VERSION}"
    "--build-arg" "MCP_SERVER_VERSION=${MCP_SERVER_VERSION}"
    "--build-arg" "BUILD_DATE=${BUILD_DATE}"
    "--build-arg" "VCS_REF=${VCS_REF}"
)

echo "Building LadybugDB MCP Server Docker image..."
echo "Tag: ${TAG}"
echo "Graphiti Core Version: ${GRAPHITI_CORE_VERSION}"
echo "MCP Server Version: ${MCP_SERVER_VERSION}"
echo "Build Date: ${BUILD_DATE}"
echo "VCS Ref: ${VCS_REF}"
echo ""

# Build Docker image (from parent directory to access graphiti_core)
cd ..
docker build \
    "${BUILD_ARGS[@]}" \
    -t "graphiti-mcp-ladybugdb:${TAG}" \
    -f "mcp_server/docker/Dockerfile.ladybugdb" \
    .

echo "✅ LadybugDB MCP Server Docker image built successfully!"
echo "Image: graphiti-mcp-ladybugdb:${TAG}"
echo ""
echo "To run with Docker Compose:"
echo "  docker compose -f mcp_server/docker/docker-compose-ladybugdb.yml up"
echo ""
echo "To run manually:"
echo "  docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here graphiti-mcp-ladybugdb:${TAG}"
