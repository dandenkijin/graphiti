#!/bin/bash

# LadybugDB Setup Script
# This script helps configure the environment for LadybugDB with local models

echo "=== LadybugDB Setup ==="
echo ""

# Check if .env file exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
    echo ""
fi

echo "Configuration Options:"
echo "1. For OpenAI API:"
echo "   OPENAI_API_KEY=your_openai_api_key"
echo "   MODEL_NAME=gpt-3.5-turbo"
echo ""
echo "2. For Local Models (Ollama):"
echo "   OPENAI_API_KEY=not-needed"
echo "   OPENAI_BASE_URL=http://localhost:11434/v1"
echo "   MODEL_NAME=llama2"
echo ""
echo "3. For Other OpenAI-Compatible APIs:"
echo "   OPENAI_API_KEY=your_api_key"
echo "   OPENAI_BASE_URL=your_api_endpoint"
echo "   MODEL_NAME=your_model_name"
echo ""

# Check if Ollama is running (for local models)
if command -v ollama &> /dev/null; then
    echo "Checking Ollama status..."
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is running!"
        echo "Available models:"
        curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "Could not fetch models"
    else
        echo "Ollama is not running. Start with: ollama serve"
    fi
else
    echo "Ollama not found. Install with: curl -fsSL https://ollama.ai/install.sh | sh"
fi

echo ""
echo "Next steps:"
echo "1. Edit .env file with your preferred configuration"
echo "2. Start your local model server (if using local models)"
echo "3. Run: docker-compose -f docker/docker-compose.ladybugdb.yml up -d"
echo "4. Test: curl http://localhost:8000/healthcheck"
echo ""
echo "For API documentation, visit: http://localhost:8000/docs"
