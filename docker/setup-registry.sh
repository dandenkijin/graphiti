#!/bin/bash

# Automated Docker registry setup for dhi.io
# This script handles login and configuration for the private registry

set -e

echo "Setting up Docker registry access for dhi.io..."

# Check if user is already logged in to dhi.io
if docker info 2>/dev/null | grep -q "Username: "; then
    echo "Checking existing registry access..."
fi

# Prompt for registry credentials if not already configured
if ! grep -q "dhi.io" "$HOME/.docker/config.json" 2>/dev/null; then
    echo "Please enter your dhi.io registry credentials:"
    echo "Note: These will be stored securely in your Docker config"
    echo ""
    
    # Read credentials
    read -p "Username: " DOCKER_USERNAME
    read -s -p "Password/Token: " DOCKER_PASSWORD
    echo ""
    
    # Login to the registry
    echo "Logging into dhi.io registry..."
    echo "$DOCKER_PASSWORD" | docker login dhi.io --username "$DOCKER_USERNAME" --password-stdin
    
    if [ $? -eq 0 ]; then
        echo "Successfully logged into dhi.io registry"
    else
        echo "Failed to login to dhi.io registry"
        exit 1
    fi
else
    echo "Already configured for dhi.io registry"
fi

# Test pull of the base image
echo "Testing access to dhi.io/python:3.12-debian13-dev..."
if docker pull dhi.io/python:3.12-debian13-dev --dry-run 2>/dev/null || \
   docker manifest inspect dhi.io/python:3.12-debian13-dev >/dev/null 2>&1; then
    echo "Registry access confirmed"
else
    echo "Warning: Cannot verify access to the image. Build may fail."
fi

echo "Registry setup complete!"
echo "You can now build with: docker-compose -f docker/docker-compose.ladybugdb.yml up -d"
