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

import asyncio
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder
else:
    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        raise ImportError(
            'sentence-transformers is required for BGERerankerClient. '
            'Install it with: pip install graphiti-core[sentence-transformers]'
        ) from None

from graphiti_core.cross_encoder.client import CrossEncoderClient

# Check for local mode
LOCAL_MODE = os.getenv('GRAPHITI_LOCAL_MODE', 'false').lower() in ('true', '1', 'yes')


class BGERerankerClient(CrossEncoderClient):
    def __init__(self, reranker_model: str | None = None):
        # Get reranker model name from environment variable or use default
        self.reranker_model = reranker_model or os.getenv('RERANKER_MODEL', 'BAAI/bge-reranker-v2-m3')
        
        if not LOCAL_MODE:
            import time
            import threading
            
            print(f"Loading reranker model '{self.reranker_model}'...")
            print("This may take a moment if the model needs to be downloaded...")
            
            # Show countdown while loading
            def countdown():
                for i in range(60, 0, -1):
                    time.sleep(1)
                    if i % 10 == 0 or i <= 5:
                        print(f"Still loading... {i}s remaining")
            
            # Start countdown in background thread
            countdown_thread = threading.Thread(target=countdown, daemon=True)
            countdown_thread.start()
            
            self.model = CrossEncoder(self.reranker_model)
            print(f"BGE reranker model '{self.reranker_model}' loaded successfully!")
        else:
            # In local mode, don't load the model at all
            self.model = None

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        if not passages:
            return []

        # Use mock data in local mode to avoid model loading
        if LOCAL_MODE or self.model is None:
            # Simple scoring: first passage gets highest score
            return [(passage, 1.0 - i * 0.1) for i, passage in enumerate(passages)]

        input_pairs = [[query, passage] for passage in passages]

        # Run the synchronous predict method in an executor
        loop = asyncio.get_running_loop()
        scores = await loop.run_in_executor(None, self.model.predict, input_pairs)

        ranked_passages = sorted(
            [(passage, float(score)) for passage, score in zip(passages, scores, strict=False)],
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked_passages
