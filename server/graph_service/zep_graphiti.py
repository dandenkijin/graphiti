import logging
from typing import Annotated

from fastapi import Depends, HTTPException
from graphiti_core import Graphiti  # type: ignore
# Import real_ladybug since LadybugDB is a Kuzu fork
import real_ladybug  # type: ignore
from graphiti_core.driver.driver import GraphDriver, GraphDriverSession, GraphProvider  # type: ignore
from graphiti_core.edges import EntityEdge  # type: ignore
from graphiti_core.errors import EdgeNotFoundError, GroupsEdgesNotFoundError, NodeNotFoundError
from graphiti_core.llm_client import LLMClient  # type: ignore
from graphiti_core.nodes import EntityNode, EpisodicNode  # type: ignore

from graph_service.config import ZepEnvDep
from graph_service.dto import FactResult

logger = logging.getLogger(__name__)


class LadybugDriver(GraphDriver):
    """Custom driver that uses LadybugDB instead of kuzu"""
    
    provider: GraphProvider = GraphProvider.KUZU  # Use Kuzu provider for compatibility
    
    def __init__(
        self,
        db: str = ':memory:',
        max_concurrent_queries: int = 1,
    ):
        # Use real_ladybug instead of kuzu
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


class ZepGraphiti(Graphiti):
    def __init__(self, uri: str, user: str, password: str, llm_client: LLMClient | None = None):
        # Initialize without calling super() to avoid Neo4j driver setup
        self.llm_client = llm_client
        self.driver = None  # Will be set by the calling functions
        self.embedder = None  # Will be set by the calling functions
        
        # Initialize embedder if llm_client is available
        if llm_client:
            self.embedder = llm_client
        
        # Initialize other required attributes
        self.store_raw_episode_content = True
        self.max_coroutines = None
        self.cross_encoder = None
        self.tracer = None
        
        # Initialize clients and namespaces as None - will be set when driver is available
        self.clients = None
        self.nodes = None
        self.edges = None
    
    def _initialize_clients_and_namespaces(self, settings):
        """Initialize clients and namespaces after driver is set"""
        if self.driver is None:
            raise ValueError("Driver must be set before initializing clients")
        
        # Create proper cross_encoder instance
        from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
        cross_encoder = OpenAIRerankerClient()
        
        # Create proper embedder instance
        from graphiti_core.embedder import OpenAIEmbedder, OpenAIEmbedderConfig
        # Check if using local model (Ollama or other local model)
        is_local_model = (
            hasattr(settings, 'openai_base_url') and 
            settings.openai_base_url and 
            settings.openai_base_url != 'https://api.openai.com/v1'
        )
        if is_local_model:
            config = OpenAIEmbedderConfig(
                api_key="not-needed",
                base_url=settings.openai_base_url,
                embedding_model=settings.model_name
            )
            embedder = OpenAIEmbedder(config)
        else:
            embedder = OpenAIEmbedder()
        
        # Create proper tracer instance
        from graphiti_core.tracer import create_tracer
        tracer = create_tracer(None, 'graphiti')
        
        # Initialize clients attribute
        from graphiti_core.graphiti_types import GraphitiClients
        self.clients = GraphitiClients(
            driver=self.driver,
            llm_client=self.llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder,
            tracer=tracer,
        )
        
        # Initialize namespace API
        from graphiti_core.namespaces import NodeNamespace, EdgeNamespace
        self.nodes = NodeNamespace(self.driver, embedder)
        self.edges = EdgeNamespace(self.driver, embedder)
        
        # Store instances for reference
        self.embedder = embedder
        self.cross_encoder = cross_encoder
        self.tracer = tracer

    async def save_entity_node(self, name: str, uuid: str, group_id: str, summary: str = ''):
        new_node = EntityNode(
            name=name,
            uuid=uuid,
            group_id=group_id,
            summary=summary,
        )
        await new_node.generate_name_embedding(self.embedder)
        await new_node.save(self.driver)
        return new_node

    async def get_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            return edge
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def delete_group(self, group_id: str):
        try:
            edges = await EntityEdge.get_by_group_ids(self.driver, [group_id])
        except GroupsEdgesNotFoundError:
            logger.warning(f'No edges found for group {group_id}')
            edges = []

        nodes = await EntityNode.get_by_group_ids(self.driver, [group_id])

        episodes = await EpisodicNode.get_by_group_ids(self.driver, [group_id])

        for edge in edges:
            await edge.delete(self.driver)

        for node in nodes:
            await node.delete(self.driver)

        for episode in episodes:
            await episode.delete(self.driver)

    async def delete_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            await edge.delete(self.driver)
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e

    async def delete_episodic_node(self, uuid: str):
        try:
            episode = await EpisodicNode.get_by_uuid(self.driver, uuid)
            await episode.delete(self.driver)
        except NodeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e


def _create_graphiti_client(settings: ZepEnvDep) -> ZepGraphiti:
    """Shared helper function to create and configure ZepGraphiti client"""
    # Use LadybugDriver if Neo4j settings are not provided
    if settings.neo4j_uri is None:
        # Use LadybugDriver
        driver = LadybugDriver(db=settings.graph_db_path)
        
        # Create LLM client
        from graphiti_core.llm_client import OpenAIClient, LLMConfig
        llm_config = LLMConfig(
            model=settings.model_name or "gpt-3.5-turbo",
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        llm_client = OpenAIClient(llm_config)
        
        client = ZepGraphiti(
            uri=settings.graph_db_path,  # Use graph_db_path as uri for compatibility
            user="",  # Not used for LadybugDB
            password="",  # Not used for LadybugDB
            llm_client=llm_client,
        )
        client.driver = driver  # Override the driver with LadybugDriver
        
        # Initialize clients and namespaces properly
        client._initialize_clients_and_namespaces(settings)
    else:
        # Use Neo4j driver (original behavior)
        client = ZepGraphiti(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
        )
    
    return client


async def get_graphiti(settings: ZepEnvDep):
    client = _create_graphiti_client(settings)
    
    try:
        yield client
    finally:
        await client.close()


async def initialize_graphiti(settings: ZepEnvDep):
    client = _create_graphiti_client(settings)
    await client.build_indices_and_constraints()


def get_fact_result_from_edge(edge: EntityEdge):
    return FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
        valid_at=edge.valid_at,
        invalid_at=edge.invalid_at,
        created_at=edge.created_at,
        expired_at=edge.expired_at,
    )


ZepGraphitiDep = Annotated[ZepGraphiti, Depends(get_graphiti)]
