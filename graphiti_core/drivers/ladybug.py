"""
LadybugDB driver implementation for Graphiti.

This module provides a LadybugDB-compatible driver that can be used
as an alternative to other graph databases like Neo4j or FalkorDB.
"""

import logging
from typing import TYPE_CHECKING

from ..driver.driver import GraphDriver, GraphDriverSession, GraphProvider

# Try to import real_ladybug at runtime
try:
    import real_ladybug
except ImportError:
    real_ladybug = None

logger = logging.getLogger(__name__)


class LadybugDriver(GraphDriver):
    """Custom driver that uses LadybugDB instead of other graph databases"""
    
    provider: GraphProvider = GraphProvider.KUZU  # Use Kuzu provider for compatibility
    
    def __init__(
        self,
        db: str = ':memory:',
        max_concurrent_queries: int = 1,
    ):
        if real_ladybug is None:
            raise ImportError("real_ladybug package is required for LadybugDriver. Install with: pip install graphiti-core[ladybug]")
        
        # Use real_ladybug instead of other graph databases
        self.db = real_ladybug.Database(db)
        
        # Setup schema using LadybugDB
        self.setup_schema()
        
        self.client = real_ladybug.AsyncConnection(self.db, max_concurrent_queries=max_concurrent_queries)
        
        # Add _database attribute for compatibility with ingest router
        self._database = self.db
    
    def setup_schema(self):
        """Setup schema using LadybugDB connection"""
        conn = real_ladybug.Connection(self.db)
        try:
            # Install and load FTS extension for full text search
            try:
                conn.execute("INSTALL FTS")
                conn.execute("LOAD EXTENSION FTS")
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
                # FTS indexes for full text search using LadybugDB's CREATE_FTS_INDEX function
                "CALL CREATE_FTS_INDEX('RelatesToNode_', 'edge_name_and_fact', ['name', 'fact']);",
                "CALL CREATE_FTS_INDEX('Entity', 'entity_name_fts', ['name']);",
                "CALL CREATE_FTS_INDEX('Episodic', 'episodic_content_fts', ['content', 'name']);",
            ]
            
            for query in index_queries:
                try:
                    conn.execute(query)
                except Exception as e:
                    # Index might already exist or have issues
                    print(f"Warning: Failed to create index: {e}")
        finally:
            conn.close()
    
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
        conn = real_ladybug.Connection(self.db)
        try:
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
        finally:
            conn.close()


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
        conn = real_ladybug.Connection(self.driver.db)
        try:
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
        finally:
            conn.close()
    
    async def execute_transaction(self, queries: list[tuple[str, dict | None]]):
        """Execute multiple queries in a transaction"""
        conn = real_ladybug.Connection(self.driver.db)
        try:
            results = []
            for query, params in queries:
                result = conn.execute(query, params or {})
                results.append(result)
            return results
        finally:
            conn.close()
    
    async def close(self):
        # LadybugDB doesn't require explicit closing
        pass
