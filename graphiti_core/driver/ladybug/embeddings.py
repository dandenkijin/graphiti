"""
LadybugDB embeddings module for handling different embedding providers.

This module provides a unified interface for creating embeddings using:
LadybugDB's native LLM extension with support for multiple providers.
"""

import logging
import os
from typing import Any


logger = logging.getLogger(__name__)


class LadybugEmbeddings:
    """
    Embeddings interface for LadybugDB using the native LLM extension.
    Supports multiple providers (Ollama, OpenAI, Gemini, Voyage AI, etc.).
    """
    
    def __init__(self, driver: Any):
        self.driver = driver
        self._native_available = self._check_native_availability()
        
    def _check_native_availability(self) -> bool:
        """Check if LadybugDB's native LLM extension is available."""
        return os.getenv('OLLAMA_SCHEMA', '').lower() == 'true'
    
    async def create_embedding(
        self,
        text: str,
        model: str | None = None,
        dimensions: int = 768,
        endpoint: str | None = None
    ) -> list[float]:
        """
        Create embeddings using the provider specified by EMBEDDING_MODEL_NAME.
        
        Args:
            text: Text to embed
            model: Model name (optional, uses EMBEDDING_MODEL_NAME from env)
            dimensions: Embedding dimensions
            endpoint: Custom endpoint (for Ollama)
            
        Returns:
            List of embedding values
        """
        # Determine provider from EMBEDDING_MODEL_NAME environment variable
        embedding_model = model or os.getenv('EMBEDDING_MODEL_NAME')
        if not embedding_model:
            raise ValueError("EMBEDDING_MODEL_NAME environment variable must be set")
        
        # Determine provider based on model name
        if embedding_model.startswith('nomic-embed-text'):
            provider = 'ollama'
        elif embedding_model.startswith('text-embedding-'):
            provider = 'openai'
        elif embedding_model.startswith('voyage-'):
            provider = 'voyageai'
        elif 'gemini' in embedding_model.lower():
            provider = 'google-gemini'
        else:
            # Default to ollama for unknown models
            provider = 'ollama' if self._native_available else 'openai'
        
        # Use LadybugDB's native LLM extension
        if not self._native_available:
            raise RuntimeError("LadybugDB LLM extension not available. Set OLLAMA_SCHEMA=true to enable.")
        
        return await self._create_native_embedding(text, provider, embedding_model, dimensions, endpoint)
    
        
        
    async def _create_native_embedding(
        self,
        text: str,
        provider: str,
        model: str | None,
        dimensions: int,
        endpoint: str | None
    ) -> list[float]:
        """Create embedding using LadybugDB's native LLM extension."""
        embedding_model = model or os.getenv('EMBEDDING_MODEL_NAME', 'nomic-embed-text')
        
        with self.driver.get_connection() as conn:
            if provider == "ollama":
                if endpoint:
                    query = "RETURN CREATE_EMBEDDING($text, 'ollama', $model, $dimensions, $endpoint);"
                    params = {"text": text, "model": embedding_model, "dimensions": dimensions, "endpoint": endpoint}
                else:
                    query = "RETURN CREATE_EMBEDDING($text, 'ollama', $model, $dimensions);"
                    params = {"text": text, "model": embedding_model, "dimensions": dimensions}
            else:
                # For other providers supported by LadybugDB
                query = "RETURN CREATE_EMBEDDING($text, $provider, $model, $dimensions);"
                params = {"text": text, "provider": provider, "model": embedding_model, "dimensions": dimensions}
            
            result = conn.execute(query, params)
            if result and len(result) > 0:
                embedding = result[0][0]  # Extract the LIST[FLOAT] result
                return [float(x) for x in embedding]
            else:
                raise ValueError(f"Failed to create embedding for text: {text}")
    
        
    async def create_batch_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.create_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    
