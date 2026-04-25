"""
LadybugDB Search Interface Implementation.

This module provides a SearchInterface implementation that leverages LadybugDB's
native capabilities for HNSW vector indexes, Cypher queries, graph algorithms,
and BM25 full-text search.
"""

import logging
from typing import Any

from graphiti_core.driver.search_interface.search_interface import SearchInterface
from graphiti_core.driver.driver import GraphDriver

logger = logging.getLogger(__name__)

# Import LadybugDB algorithm components
try:
    from .algorithms import LadybugGraphAlgorithms, LadybugAlgorithmRerankers
except ImportError:
    LadybugGraphAlgorithms = None
    LadybugAlgorithmRerankers = None


class LadybugSearchInterface(SearchInterface):
    """
    LadybugDB-specific search interface that uses native LadybugDB capabilities.
    
    This interface maps Graphiti's search methods to LadybugDB's native functions:
    - Vector similarity search -> HNSW vector indexes
    - Full-text search -> BM25 indexes  
    - Graph traversal -> Cypher queries
    - Graph algorithms -> Native algorithm calls
    """
    
    async def edge_fulltext_search(
        self,
        driver: Any,
        query: str,
        search_filter: Any,
        group_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """
        Perform BM25 full-text search over edge facts and names using LadybugDB's native BM25.
        """
        # Use LadybugDB's native FTS search
        fts_query = f"""
        CALL QUERY_FTS_INDEX('RelatesToNode_', 'edge_name_and_fact_bm25', $query, TOP := $limit) 
        YIELD node, score
        MATCH (n:Entity)-[:RELATES_TO]->(e:RelatesToNode_ {{uuid: node.uuid}})-[:RELATES_TO]->(m:Entity)
        RETURN e, n, m, score
        """
        
        if group_ids:
            fts_query += " WHERE e.group_id IN $group_ids"
        
        result, _, _ = await driver.execute_query(
            fts_query, 
            query=query, 
            limit=limit, 
            group_ids=group_ids
        )
        
        return self._parse_entity_edges(result, search_filter)

    async def edge_similarity_search(
        self,
        driver: Any,
        search_vector: list[float],
        source_node_uuid: str | None,
        target_node_uuid: str | None,
        search_filter: Any,
        group_ids: list[str] | None = None,
        limit: int = 100,
        min_score: float = 0.7,
    ) -> list[Any]:
        """
        Perform HNSW vector similarity search over edge fact embeddings.
        """
        # Use LadybugDB's native HNSW vector search
        vector_query = f"""
        CALL QUERY_VECTOR_INDEX('RelatesToNode_', 'fact_embedding_hnsw', $search_vector, $limit) 
        WITH node AS result_node, distance
        MATCH (n:Entity)-[:RELATES_TO]->(e:RelatesToNode_ {{uuid: result_node.uuid}})-[:RELATES_TO]->(m:Entity)
        WHERE distance <= $max_distance
        """
        
        filter_conditions = []
        if source_node_uuid:
            filter_conditions.append("n.uuid = $source_uuid")
        if target_node_uuid:
            filter_conditions.append("m.uuid = $target_uuid")
        if group_ids:
            filter_conditions.append("e.group_id IN $group_ids")
            
        if filter_conditions:
            vector_query += " WHERE " + " AND ".join(filter_conditions)
        
        vector_query += " RETURN e, n, m, score"
        
        params = {
            'search_vector': search_vector,
            'limit': limit,
            'min_score': min_score,
            'source_uuid': source_node_uuid,
            'target_uuid': target_node_uuid,
            'group_ids': group_ids
        }
        
        # Convert min_score to max_distance (inverse relationship)
        max_distance = 1.0 - min_score  # Higher score = lower distance
        
        result, _, _ = await driver.execute_query(
            vector_query, 
            search_vector=search_vector,
            limit=limit,
            max_distance=max_distance,
            source_node_uuid=source_node_uuid,
            target_node_uuid=target_node_uuid,
            group_ids=group_ids
        )
        
        return self._parse_entity_edges(result, search_filter)

    async def node_fulltext_search(
        self,
        driver: Any,
        query: str,
        search_filter: Any,
        group_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """
        Perform BM25 full-text search over node names and summaries.
        """
        fts_query = """
        CALL QUERY_FTS_INDEX('Entity', 'entity_name_bm25', $query, TOP := $limit) 
        YIELD node, score
        MATCH (n:Entity {uuid: node.uuid})
        """
        
        if group_ids:
            fts_query += " WHERE n.group_id IN $group_ids"
        
        fts_query += " RETURN n, score"
        
        result, _, _ = await driver.execute_query(
            fts_query, 
            query=query, 
            limit=limit, 
            group_ids=group_ids
        )
        
        return self._parse_entity_nodes(result, search_filter)

    async def node_similarity_search(
        self,
        driver: Any,
        search_vector: list[float],
        search_filter: Any,
        group_ids: list[str] | None = None,
        limit: int = 100,
        min_score: float = 0.7,
    ) -> list[Any]:
        """
        Perform HNSW vector similarity search over node name embeddings.
        """
        vector_query = """
        CALL QUERY_VECTOR_INDEX('Entity', 'entity_name_embedding_hnsw', $search_vector, $limit) 
        WITH node AS result_node, distance
        MATCH (n:Entity {uuid: result_node.uuid})
        WHERE distance <= $max_distance
        """
        
        if group_ids:
            vector_query += " WHERE n.group_id IN $group_ids"
        
        vector_query += " RETURN n, distance as score"
        
        # Convert min_score to max_distance (inverse relationship)
        max_distance = 1.0 - min_score  # Higher score = lower distance
        
        result, _, _ = await driver.execute_query(
            vector_query, 
            search_vector=search_vector, 
            limit=limit, 
            max_distance=max_distance, 
            group_ids=group_ids
        )
        
        return self._parse_entity_nodes(result, search_filter)

    async def episode_fulltext_search(
        self,
        driver: Any,
        query: str,
        search_filter: Any,
        group_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """
        Perform BM25 full-text search over episode content.
        """
        fts_query = """
        CALL QUERY_FTS_INDEX('Episodic', 'episodic_content_bm25', $query, TOP := $limit) 
        YIELD node, score
        MATCH (e:Episodic {uuid: node.uuid})
        """
        
        if group_ids:
            fts_query += " WHERE e.group_id IN $group_ids"
        
        fts_query += " RETURN e, score"
        
        result, _, _ = await driver.execute_query(
            fts_query, 
            query=query, 
            limit=limit, 
            group_ids=group_ids
        )
        
        return self._parse_episodic_nodes(result, search_filter)

    async def edge_bfs_search(
        self,
        driver: Any,
        bfs_origin_node_uuids: list[str] | None,
        bfs_max_depth: int,
        search_filter: Any,
        group_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """
        Perform breadth-first search using LadybugDB's native Cypher traversal.
        """
        if not bfs_origin_node_uuids:
            return []
        
        # Use LadybugDB's native Cypher for graph traversal
        cypher_query = f"""
        UNWIND $bfs_origin_node_uuids AS origin_uuid
        MATCH path = (origin {{uuid: origin_uuid}})-[:RELATES_TO|MENTIONS*1..{bfs_max_depth}]->(n:Entity)
        UNWIND relationships(path) AS rel
        MATCH (source:Entity)-[e:RELATES_TO {{uuid: rel.uuid}}]-(target:Entity)
        """
        
        if group_ids:
            cypher_query += " WHERE e.group_id IN $group_ids"
        
        cypher_query += """
        RETURN e, source, target, length(path) AS distance
        ORDER BY distance, e.created_at DESC
        LIMIT $limit
        """
        
        result, _, _ = await driver.execute_query(
            cypher_query,
            bfs_origin_node_uuids=bfs_origin_node_uuids,
            bfs_max_depth=bfs_max_depth,
            group_ids=group_ids,
            limit=limit
        )
        
        return self._parse_entity_edges(result, search_filter)

    async def node_bfs_search(
        self,
        driver: Any,
        bfs_origin_node_uuids: list[str] | None,
        search_filter: Any,
        bfs_max_depth: int,
        group_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """
        Perform breadth-first search for nodes using native Cypher traversal.
        """
        if not bfs_origin_node_uuids or bfs_max_depth < 1:
            return []
        
        cypher_query = f"""
        UNWIND $bfs_origin_node_uuids AS origin_uuid
        MATCH path = (origin {{uuid: origin_uuid}})-[:RELATES_TO|MENTIONS*1..{bfs_max_depth}]->(n:Entity)
        """
        
        if group_ids:
            cypher_query += " WHERE n.group_id IN $group_ids"
        
        cypher_query += """
        RETURN n, length(path) AS distance
        ORDER BY distance, n.created_at DESC
        LIMIT $limit
        """
        
        result, _, _ = await driver.execute_query(
            cypher_query,
            bfs_origin_node_uuids=bfs_origin_node_uuids,
            bfs_max_depth=bfs_max_depth,
            group_ids=group_ids,
            limit=limit
        )
        
        return self._parse_entity_nodes(result, search_filter)

    async def community_fulltext_search(
        self,
        driver: Any,
        query: str,
        group_ids: list[str] | None = None,
        limit: int = 100,
    ) -> list[Any]:
        """
        Perform BM25 full-text search over community names.
        """
        # Note: Communities would need their own BM25 index setup
        # For now, use basic name matching
        match_query = """
        MATCH (c:Community)
        WHERE toLower(c.name) CONTAINS toLower($query)
        """
        
        if group_ids:
            match_query += " AND c.group_id IN $group_ids"
        
        match_query += " RETURN c, 1.0 as score ORDER BY score DESC LIMIT $limit"
        
        result, _, _ = await driver.execute_query(
            match_query, 
            query=query, 
            group_ids=group_ids, 
            limit=limit
        )
        
        return self._parse_community_nodes(result)

    async def community_similarity_search(
        self,
        driver: Any,
        search_vector: list[float],
        group_ids: list[str] | None = None,
        limit: int = 100,
        min_score: float = 0.6,
    ) -> list[Any]:
        """
        Perform HNSW vector similarity search over community name embeddings.
        """
        vector_query = """
        CALL QUERY_VECTOR_INDEX('Community', 'community_name_embedding_hnsw', $search_vector, $limit) 
        WITH node AS result_node, distance
        MATCH (c:Community {uuid: result_node.uuid})
        WHERE distance <= $max_distance
        """
        
        if group_ids:
            vector_query += " WHERE c.group_id IN $group_ids"
        
        vector_query += " RETURN c, distance as score"
        
        # Convert min_score to max_distance (inverse relationship)
        max_distance = 1.0 - min_score  # Higher score = lower distance
        
        result, _, _ = await driver.execute_query(
            vector_query, 
            search_vector=search_vector, 
            limit=limit, 
            max_distance=max_distance, 
            group_ids=group_ids
        )
        
        return self._parse_community_nodes(result)

    async def get_embeddings_for_communities(
        self,
        driver: Any,
        communities: list[Any],
    ) -> dict[str, list[float]]:
        """
        Load name embeddings for community nodes.
        """
        community_uuids = [c.uuid for c in communities]
        
        query = """
        MATCH (c:Community)
        WHERE c.uuid IN $community_uuids
        RETURN c.uuid AS uuid, c.name_embedding AS embedding
        """
        
        result, _, _ = await driver.execute_query(query, community_uuids=community_uuids)
        
        embeddings = {}
        for record in result:
            if record['embedding']:
                embeddings[record['uuid']] = [float(x) for x in record['embedding'].split(',')]
        
        return embeddings

    async def node_distance_reranker(
        self,
        driver: Any,
        node_uuids: list[str],
        center_node_uuid: str,
        min_score: float = 0,
    ) -> tuple[list[str], list[float]]:
        """
        Rerank nodes by their graph distance using LadybugDB's native shortest path algorithm.
        """
        if LadybugGraphAlgorithms is None:
            # Fallback to basic implementation
            return [], []
        
        # Compute shortest paths from center to all target nodes
        distance_scores = {}
        for node_uuid in node_uuids:
            path = await LadybugGraphAlgorithms.shortest_path(
                driver, center_node_uuid, node_uuid
            )
            if path:
                distance = len(path) - 1  # Number of edges
                score = 1.0 / distance if distance > 0 else 1.0  # Direct connection gets 1.0
                distance_scores[node_uuid] = score
            else:
                distance_scores[node_uuid] = 0.0  # No path
        
        # Filter by min_score and sort
        filtered_results = [
            (uuid, score) 
            for uuid, score in distance_scores.items() 
            if score >= min_score
        ]
        
        sorted_results = sorted(filtered_results, key=lambda x: x[1], reverse=True)
        
        if sorted_results:
            uuids, scores = zip(*sorted_results)
            return list(uuids), list(scores)
        else:
            return [], []

    async def episode_mentions_reranker(
        self,
        driver: Any,
        node_uuids: list[list[str]],
        min_score: float = 0,
    ) -> tuple[list[str], list[float]]:
        """
        Rerank nodes by their episode mention count using LadybugDB's aggregation.
        """
        all_uuids = [uuid for sublist in node_uuids for uuid in sublist]
        
        query = """
        UNWIND $all_uuids AS node_uuid
        MATCH (n:Entity {uuid: node_uuid})<-[:MENTIONS]-(e:Episodic)
        RETURN n.uuid AS uuid, count(e) AS mention_count
        ORDER BY mention_count DESC
        """
        
        result, _, _ = await driver.execute_query(query, all_uuids=all_uuids)
        
        # Filter by min_score and return results
        filtered_results = [
            (r['uuid'], float(r['mention_count'])) 
            for r in result 
            if r['mention_count'] >= min_score
        ]
        
        if filtered_results:
            uuids, scores = zip(*filtered_results)
            return list(uuids), list(scores)
        else:
            return [], []

    def build_node_search_filters(self, search_filters: Any) -> Any:
        """
        Build LadybugDB-specific node search filters.
        """
        # For now, return the filters as-is since LadybugDB uses standard Cypher
        return search_filters

    def build_edge_search_filters(self, search_filters: Any) -> Any:
        """
        Build LadybugDB-specific edge search filters.
        """
        # For now, return the filters as-is since LadybugDB uses standard Cypher
        return search_filters

    # Helper methods for parsing results
    def _parse_entity_edges(self, result: list, search_filter: Any) -> list[Any]:
        """Parse LadybugDB query results into EntityEdge objects."""
        from graphiti_core.edges import get_entity_edge_from_record
        
        edges = []
        for record in result:
            try:
                edge = get_entity_edge_from_record(record)
                if edge:
                    edges.append(edge)
            except Exception as e:
                logger.warning(f"Failed to parse edge from record: {e}")
        
        return edges

    def _parse_entity_nodes(self, result: list, search_filter: Any) -> list[Any]:
        """Parse LadybugDB query results into EntityNode objects."""
        from graphiti_core.nodes import get_entity_node_from_record
        
        nodes = []
        for record in result:
            try:
                node = get_entity_node_from_record(record)
                if node:
                    nodes.append(node)
            except Exception as e:
                logger.warning(f"Failed to parse node from record: {e}")
        
        return nodes

    def _parse_episodic_nodes(self, result: list, search_filter: Any) -> list[Any]:
        """Parse LadybugDB query results into EpisodicNode objects."""
        from graphiti_core.nodes import get_episodic_node_from_record
        
        nodes = []
        for record in result:
            try:
                node = get_episodic_node_from_record(record)
                if node:
                    nodes.append(node)
            except Exception as e:
                logger.warning(f"Failed to parse episodic node from record: {e}")
        
        return nodes

    def _parse_community_nodes(self, result: list) -> list[Any]:
        """Parse LadybugDB query results into CommunityNode objects."""
        from graphiti_core.nodes import get_community_node_from_record
        
        nodes = []
        for record in result:
            try:
                node = get_community_node_from_record(record)
                if node:
                    nodes.append(node)
            except Exception as e:
                logger.warning(f"Failed to parse community node from record: {e}")
        
        return nodes
