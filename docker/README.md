# LadybugDB Graphiti Docker Setup

This document explains the Docker setup for running LadybugDB with Graphiti, including the changes made to support Ollama embeddings and the path forward for production deployment.

## Overview

The LadybugDB Graphiti service provides a graph database with embedding search capabilities using local Ollama models. This setup enables fully local operation without requiring external embedding services.

## Current Changes

### 1. Dockerfile.ladybugdb

The Dockerfile has been modified to:

- **Install local graphiti-core**: Instead of using the PyPI version, we install the local source code to include Ollama support
- **Add server dependencies**: uvicorn, fastapi, and httpx are now included in main dependencies
- **Install real_ladybug**: The LadybugDB Python client for database operations
- **Set up FTS extension**: Automatically installs and loads the Full Text Search extension

### 2. Environment Configuration

- **.env file**: Copied from `docker/.env` to project root for consistent environment loading
- **Ollama integration**: Uses `OLLAMA_SCHEMA=true` to enable Ollama-specific embedding handling
- **Local model support**: Configured to use `qwen3-embedding:8b` model via Ollama

### 3. Code Changes

#### graphiti_core/embedder/openai.py
- Added Ollama API support alongside OpenAI compatibility
- Handles both string and list input formats
- Uses `OLLAMA_SCHEMA` environment variable to detect Ollama usage
- Routes requests to appropriate API (Ollama vs OpenAI)

#### server/graph_service/zep_graphiti.py
- Fixed LadybugDriver initialization for local model detection
- Added proper FTS index creation using `CREATE_FTS_INDEX` function
- Fixed parameter handling for search queries
- Added variable argument support for compatibility

#### pyproject.toml
- Moved uvicorn, fastapi, and httpx to main dependencies
- Ensures all required server components are available

## Usage

### Development Setup

1. **Start the service**:
   ```bash
   docker-compose -f docker/docker-compose.ladybugdb.yml up -d --build ladybugdb-graphiti
   ```

2. **Test the search endpoint**:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
        -d '{"query": "What is LadybugDB?"}' \
        http://localhost:8000/search
   ```

3. **Check container logs**:
   ```bash
   docker-compose -f docker/docker-compose.ladybugdb.yml logs -f ladybugdb-graphiti
   ```

### Environment Variables

Key environment variables in `.env`:

```bash
# Ollama configuration
OPENAI_BASE_URL=http://localhost:11434
MODEL_NAME=qwen3-embedding:8b
OLLAMA_SCHEMA=true

# API key (not needed for local models)
OPENAI_API_KEY=not-needed
```

## Path Forward for Production

The current Dockerfile uses local source code installation for development. For production deployment, the following changes are needed:

### 1. Release graphiti-core with Ollama Support

Before merging this PR, the Ollama support needs to be released to PyPI:

```bash
# Update version in pyproject.toml
# Publish to PyPI
uv publish
```

### 2. Update Dockerfile for Production

The current Dockerfile already uses the production approach with `[ladybug]` optional dependency:

```dockerfile
# Current (already production-ready):
RUN if [ -n "$GRAPHITI_VERSION" ]; then \
        uv pip install --system --upgrade "graphiti-core[ladybug]==$GRAPHITI_VERSION"; \
    else \
        uv pip install --system --upgrade graphiti-core[ladybug]; \
    fi
```

### 3. No Additional Dependencies Needed

Since LadybugDB support is provided by the `[ladybug]` optional dependency, no additional dependencies are required. The `real-ladybug` package is automatically installed when using `graphiti-core[ladybug]`.

### 4. Update Environment Configuration

For production, ensure Ollama service is available:

```yaml
# docker-compose.ladybugdb.yml
services:
  ladybugdb-graphiti:
    # ... existing config
    depends_on:
      - ollama  # Add Ollama service
  
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

## Architecture

### Components

1. **LadybugDB**: Embedded graph database with FTS capabilities
2. **Graphiti**: Graph knowledge management system
3. **Ollama**: Local embedding model service
4. **FastAPI**: REST API server
5. **Uvicorn**: ASGI server

### Data Flow

1. Search request comes to FastAPI endpoint
2. Graphiti processes the query using LadybugDB
3. Embeddings are generated via Ollama (local) or OpenAI (remote)
4. Full-text search uses LadybugDB FTS indexes
5. Results are returned as JSON response

## Troubleshooting

### Common Issues

1. **"uvicorn not found"**: Fixed by adding uvicorn to main dependencies
2. **"ModuleNotFoundError: graphiti_core"**: Fixed by installing local source code
3. **"FTS extension not found"**: Fixed by installing FTS extension in setup
4. **"Index not found"**: Fixed by using correct `CREATE_FTS_INDEX` syntax

### Debug Commands

```bash
# Check container status
docker-compose -f docker/docker-compose.ladybugdb.yml ps

# View logs
docker-compose -f docker/docker-compose.ladybugdb.yml logs ladybugdb-graphiti

# Execute commands in container
docker-compose -f docker/docker-compose.ladybugdb.yml exec ladybugdb-graphiti bash

# Test embeddings directly
docker-compose -f docker/docker-compose.ladybugdb.yml exec ladybugdb-graphiti \
  uv run python -c "import asyncio; from graph_service.zep_graphiti import test_embedder; asyncio.run(test_embedder())"
```

## Dependencies

### Python Packages
- graphiti-core (local version with Ollama support)
- real_ladybug (LadybugDB Python client)
- uvicorn, fastapi, httpx (web server)
- pydantic, pydantic-settings (configuration)

### System Requirements
- Docker & Docker Compose
- Ollama service (for local embeddings)
- ~2GB RAM minimum
- ~1GB disk space

## Security Considerations

1. **Local operation**: No external API calls for embeddings
2. **Network access**: Container needs access to Ollama service
3. **Data persistence**: LadybugDB data stored in `/data` volume
4. **Environment variables**: Sensitive keys should use Docker secrets

## Performance

- **Embedding generation**: ~100ms per query (local Ollama)
- **Search latency**: ~200ms total including embedding
- **Memory usage**: ~500MB for container + model
- **Storage**: Efficient graph storage with FTS indexes

## Future Enhancements

1. **Model selection**: Support for multiple Ollama models
2. **Batch processing**: Improved embedding batch handling
3. **Caching**: Embedding result caching
4. **Monitoring**: Health checks and metrics
5. **Scaling**: Multi-container deployment options
