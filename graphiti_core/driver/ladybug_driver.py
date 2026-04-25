"""
LadybugDB driver implementation for Graphiti.

This module provides a LadybugDB-compatible driver that can be used
as an alternative to other graph databases like Neo4j or FalkorDB.
"""

import logging
from typing import TYPE_CHECKING
from contextlib import contextmanager

from ..driver.driver import GraphDriver, GraphDriverSession, GraphProvider
from ..driver.search_interface.search_interface import SearchInterface

# Try to import real_ladybug at runtime
try:
    import real_ladybug
except ImportError:
    real_ladybug = None

# Import LadybugDB-specific components
try:
    from .search_interface import LadybugSearchInterface
    from .algorithms import LadybugGraphAlgorithms
    from .embeddings import LadybugEmbeddings
except ImportError:
    LadybugSearchInterface = None
    LadybugGraphAlgorithms = None
    LadybugEmbeddings = None

logger = logging.getLogger(__name__)


class LadybugDriver(GraphDriver):
    """Custom driver that uses LadybugDB instead of other graph databases"""
    
    provider: GraphProvider = GraphProvider.LADYBUG  # Use native LadybugDB provider
    
    def __init__(
        self,
        db: str = ':memory:',
        max_concurrent_queries: int = 1,
    ):
        if real_ladybug is None:
            raise ImportError("real_ladybug package is required for LadybugDriver. Install with: pip install graphiti-core[ladybug]")
        
        # Use real_ladybug instead of other graph databases
        self.db = real_ladybug.Database(db)
        
        # Connection pooling to reduce connection creation overhead
        self._connection_pool = []
        self._max_pool_size = 5
        
        # Add _database attribute for compatibility with ingest router
        self._database = self.db
        
        # Setup schema using LadybugDB
        self.setup_schema()
        
        # Initialize LadybugDB-specific search interface
        if LadybugSearchInterface is not None:
            self.search_interface = LadybugSearchInterface()
        else:
            self.search_interface = None
        
        # Initialize embeddings module
        if LadybugEmbeddings is not None:
            self.embeddings = LadybugEmbeddings(self)
        else:
            self.embeddings = None
    
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
        if self.embeddings is None:
            raise RuntimeError("Embeddings module not available")
        
        return await self.embeddings.create_embedding(text, model, dimensions, endpoint)
    
    async def create_batch_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts."""
        if self.embeddings is None:
            raise RuntimeError("Embeddings module not available")
        
        return await self.embeddings.create_batch_embeddings(texts)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from pool or create new one"""
        if self._connection_pool:
            conn = self._connection_pool.pop()
        else:
            conn = real_ladybug.Connection(self.db)
        
        try:
            yield conn
        finally:
            # Return connection to pool if not full
            if len(self._connection_pool) < self._max_pool_size:
                self._connection_pool.append(conn)
            else:
                conn.close()
    
    def setup_schema(self):
        """Setup schema using LadybugDB connection"""
        with self.get_connection() as conn:
            try:
                # Install and load FTS extension for full text search
                try:
                    conn.execute("INSTALL FTS")
                    conn.execute("LOAD EXTENSION FTS")
                except Exception:
                    # Extension might already be installed
                    pass
                
                # Install and load VECTOR extension for HNSW vector search
                try:
                    conn.execute("INSTALL VECTOR")
                    conn.execute("LOAD EXTENSION VECTOR")
                except Exception:
                    # Extension might already be installed
                    pass
                
                # Install and load LLM extension for Ollama embeddings
                try:
                    conn.execute("INSTALL LLM")
                    conn.execute("LOAD EXTENSION LLM")
                except Exception:
                    # Extension might already be installed
                    pass
                
                # Basic schema setup - simplified version
                schema_queries = [
                    "CREATE NODE TABLE IF NOT EXISTS Episodic(uuid STRING PRIMARY KEY, name STRING, group_id STRING, created_at TIMESTAMP, source STRING, source_description STRING, content STRING, valid_at TIMESTAMP, entity_edges STRING[])",
                    "CREATE NODE TABLE IF NOT EXISTS Entity(uuid STRING PRIMARY KEY, name STRING, group_id STRING, labels STRING[], created_at TIMESTAMP, name_embedding FLOAT[], summary STRING, attributes STRING)",
                    "CREATE NODE TABLE IF NOT EXISTS Community(uuid STRING PRIMARY KEY, name STRING, group_id STRING, created_at TIMESTAMP, name_embedding FLOAT[], summary STRING)",
                    "CREATE NODE TABLE IF NOT EXISTS RelatesToNode_(uuid STRING PRIMARY KEY, group_id STRING, created_at TIMESTAMP, name STRING, fact STRING, fact_embedding FLOAT[], episodes STRING[], expired_at TIMESTAMP, valid_at TIMESTAMP, invalid_at TIMESTAMP, attributes STRING)",
                    "CREATE REL TABLE IF NOT EXISTS RELATES_TO(FROM Entity TO RelatesToNode_, FROM RelatesToNode_ TO Entity)"
                ]
                
                for query in schema_queries:
                    conn.execute(query)
                
                # Create required indexes for search functionality
                index_queries = [
                    # BM25 indexes for full text search using LadybugDB's native BM25
                    ("CALL CREATE_FTS_INDEX('RelatesToNode_', 'edge_name_and_fact_bm25', ['name', 'fact']);", 'edge_name_and_fact_bm25'),
                    ("CALL CREATE_FTS_INDEX('Entity', 'entity_name_bm25', ['name']);", 'entity_name_bm25'),
                    ("CALL CREATE_FTS_INDEX('Episodic', 'episodic_content_bm25', ['content', 'name']);", 'episodic_content_bm25'),
                ]
                
                # Try to create vector indexes after some data is inserted
                # Vector indexes need actual data to understand the column type
                vector_index_queries = [
                    ("CALL CREATE_VECTOR_INDEX('Entity', 'entity_name_embedding_hnsw', 'name_embedding', metric := 'cosine');", 'entity_name_embedding_hnsw'),
                    ("CALL CREATE_VECTOR_INDEX('RelatesToNode_', 'fact_embedding_hnsw', 'fact_embedding', metric := 'cosine');", 'fact_embedding_hnsw'),
                    ("CALL CREATE_VECTOR_INDEX('Community', 'community_name_embedding_hnsw', 'name_embedding', metric := 'cosine');", 'community_name_embedding_hnsw'),
                ]
                
                for query, index_name in index_queries:
                    try:
                        conn.execute(query)
                        logger.info(f"Created index: {index_name}")
                    except Exception as e:
                        # Check if index already exists (common case)
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ['already exists', 'duplicate', 'exists']):
                            logger.debug(f"Index {index_name} already exists, skipping")
                        else:
                            # Log unexpected errors but don't fail schema setup
                            logger.warning(f"Failed to create index {index_name}: {e}")
                
                # Try to create vector indexes - these may fail if no embedding data exists yet
                for query, index_name in vector_index_queries:
                    try:
                        conn.execute(query)
                        logger.info(f"Created vector index: {index_name}")
                    except Exception as e:
                        # Vector indexes may fail if no data exists yet, that's OK
                        error_msg = str(e).lower()
                        if 'float/double array' in error_msg or 'vector_index only supports' in error_msg:
                            logger.info(f"Vector index {index_name} will be created when embedding data is available")
                        elif any(keyword in error_msg for keyword in ['already exists', 'duplicate', 'exists']):
                            logger.debug(f"Vector index {index_name} already exists, skipping")
                        else:
                            logger.warning(f"Failed to create vector index {index_name}: {e}")
            except Exception as e:
                logger.error(f"Schema setup failed: {e}")
                raise
    
    def session(self, _database: str | None = None) -> GraphDriverSession:
        return LadybugDriverSession(self)
    
    async def close(self):
        # LadybugDB doesn't require explicit closing
        pass
    
    async def build_indices_and_constraints(self, delete_existing: bool = False):
        """Build indices and constraints - simplified implementation"""
        # LadybugDB handles indices automatically
        pass
    
    async def delete_all_indexes(self):
        """Delete all indexes - simplified implementation"""
        # LadybugDB handles indices automatically
        pass
    
    async def execute_query(self, *args, **kwargs):
        """Execute a query using LadybugDB"""
        with self.get_connection() as conn:
            # Handle variable arguments for compatibility with search code
            if args:
                # First argument is the query string
                query = args[0]
                # Keep all kwargs as parameters (including 'query' if present)
                if kwargs:
                    result = conn.execute(query, kwargs)
                else:
                    result = conn.execute(query)
            else:
                # No positional arguments, use kwargs
                if 'query' in kwargs:
                    query = kwargs.pop('query')
                    if kwargs:
                        result = conn.execute(query, kwargs)
                    else:
                        result = conn.execute(query)
                else:
                    raise ValueError("No query provided")
            return result, None, None


class LadybugDriverSession(GraphDriverSession):
    provider = GraphProvider.KUZU
    
    def __init__(self, driver: LadybugDriver):
        self.driver = driver
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def execute_query(self, *args, **kwargs):
        """Execute a query using LadybugDB"""
        with self.driver.get_connection() as conn:
            # Handle variable arguments for compatibility with search code
            if args:
                # First argument is the query string
                query = args[0]
                # Keep all kwargs as parameters (including 'query' if present)
                if kwargs:
                    result = conn.execute(query, kwargs)
                else:
                    result = conn.execute(query)
            else:
                # No positional arguments, use kwargs
                if 'query' in kwargs:
                    query = kwargs.pop('query')
                    if kwargs:
                        result = conn.execute(query, kwargs)
                    else:
                        result = conn.execute(query)
                else:
                    raise ValueError("No query provided")
            return result, None, None
    
    async def execute_transaction(self, queries: list[tuple[str, dict | None]]):
        """Execute multiple queries in a transaction"""
        with self.driver.get_connection() as conn:
            results = []
            for query, params in queries:
                result = conn.execute(query, params or {})
                results.append(result)
            return results
    
    async def close(self):
        # LadybugDB doesn't require explicit closing
        pass
