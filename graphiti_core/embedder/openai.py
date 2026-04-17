"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from collections.abc import Iterable
import httpx
import os

from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types import EmbeddingModel

from .client import EmbedderClient, EmbedderConfig

DEFAULT_EMBEDDING_MODEL = 'text-embedding-3-small'


class OpenAIEmbedderConfig(EmbedderConfig):
    embedding_model: EmbeddingModel | str = DEFAULT_EMBEDDING_MODEL
    api_key: str | None = None
    base_url: str | None = None


class OpenAIEmbedder(EmbedderClient):
    """
    OpenAI Embedder Client

    This client supports both AsyncOpenAI and AsyncAzureOpenAI clients.
    """

    def __init__(
        self,
        config: OpenAIEmbedderConfig | None = None,
        client: AsyncOpenAI | AsyncAzureOpenAI | None = None,
    ):
        if config is None:
            config = OpenAIEmbedderConfig()
        self.config = config

        if client is not None:
            self.client = client
        else:
            self.client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    async def create(
        self, input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]]
    ) -> list[float]:
        # Check if using Ollama schema via environment variable
        if os.getenv('OLLAMA_SCHEMA', '').lower() == 'true':
            # Use Ollama's native API
            # Handle different input types - Ollama expects a string for prompt
            if isinstance(input_data, list):
                prompt = input_data[0] if input_data else ""
            elif isinstance(input_data, str):
                prompt = input_data
            else:
                # Convert other types to string
                prompt = str(input_data)
            
            async with httpx.AsyncClient() as client:
                # Check if using Ollama schema and adjust endpoint accordingly
                if os.getenv('OLLAMA_SCHEMA', '').lower() == 'true':
                    # Use Ollama's native API endpoint without /v1 prefix
                    endpoint = f"{self.config.base_url.replace('/v1', '')}/api/embeddings"
                else:
                    # Use standard OpenAI endpoint with /v1 prefix
                    endpoint = f"{self.config.base_url}/api/embeddings"
                
                response = await client.post(
                    endpoint,
                    json={
                        "model": self.config.embedding_model,
                        "prompt": prompt
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["embedding"][: self.config.embedding_dim]
        else:
            # Use standard OpenAI API
            result = await self.client.embeddings.create(
                input=input_data, model=self.config.embedding_model
            )
            return result.data[0].embedding[: self.config.embedding_dim]

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        # Check if using Ollama schema via environment variable
        if os.getenv('OLLAMA_SCHEMA', '').lower() == 'true':
            # Use Ollama's native API for each input
            embeddings = []
            async with httpx.AsyncClient() as client:
                for input_data in input_data_list:
                    response = await client.post(
                        f"{self.config.base_url}/api/embeddings",
                        json={
                            "model": self.config.embedding_model,
                            "prompt": input_data
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    embeddings.append(result["embedding"][: self.config.embedding_dim])
            return embeddings
        else:
            # Use standard OpenAI API
            result = await self.client.embeddings.create(
                input=input_data_list, model=self.config.embedding_model
            )
            return [embedding.embedding[: self.config.embedding_dim] for embedding in result.data]
