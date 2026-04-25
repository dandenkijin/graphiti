"""
LadybugDB Graph Algorithms Integration.

This module provides wrapper functions for LadybugDB's built-in graph algorithms
including PageRank, Louvain community detection, and connected components.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LadybugGraphAlgorithms:
    """
    Wrapper class for LadybugDB's native graph algorithms.
    
    This class provides methods to call LadybugDB's built-in algorithms:
    - PageRank: Node importance scoring
    - Louvain: Community detection
    - Connected Components: Graph connectivity analysis
    """
    
    @staticmethod
    async def pagerank(
        driver: Any,
        node_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
        max_iterations: int = 20,
        damping_factor: float = 0.85,
    ) -> dict[str, float]:
        """
        Compute PageRank scores for nodes using LadybugDB's native algorithm.
        
        Args:
            driver: GraphDriver instance
            node_types: Optional list of node types to include
            relationship_types: Optional list of relationship types to traverse
            max_iterations: Maximum number of iterations
            damping_factor: PageRank damping factor
            
        Returns:
            Dict mapping node UUIDs to PageRank scores
        """
        # Build node filter
        node_filter = ""
        if node_types:
            node_patterns = [f":{ntype}" for ntype in node_types]
            node_filter = f"WHERE {' OR '.join([f'n{pattern}' for pattern in node_patterns])}"
        
        # Build relationship filter
        rel_filter = ""
        if relationship_types:
            rel_patterns = "|".join(relationship_types)
            rel_filter = f"[{rel_patterns}]"
        else:
            rel_filter = "[RELATES_TO|MENTIONS]"
        
        query = f"""
        CALL pagerank(
            max_iterations: $max_iterations,
            damping_factor: $damping_factor
        ) YIELD node, score
        MATCH (n {{uuid: node.uuid}}) {node_filter}
        RETURN n.uuid AS uuid, score
        ORDER BY score DESC
        """
        
        result, _, _ = await driver.execute_query(
            query,
            max_iterations=max_iterations,
            damping_factor=damping_factor
        )
        
        return {record['uuid']: float(record['score']) for record in result}
    
    @staticmethod
    async def louvain_communities(
        driver: Any,
        node_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
        max_iterations: int = 10,
        resolution: float = 1.0,
    ) -> dict[str, int]:
        """
        Detect communities using Louvain algorithm via LadybugDB's native implementation.
        
        Args:
            driver: GraphDriver instance
            node_types: Optional list of node types to include
            relationship_types: Optional list of relationship types to traverse
            max_iterations: Maximum number of iterations
            resolution: Community resolution parameter
            
        Returns:
            Dict mapping node UUIDs to community IDs
        """
        # Build node filter
        node_filter = ""
        if node_types:
            node_patterns = [f":{ntype}" for ntype in node_types]
            node_filter = f"WHERE {' OR '.join([f'n{pattern}' for pattern in node_patterns])}"
        
        # Build relationship filter
        rel_filter = ""
        if relationship_types:
            rel_patterns = "|".join(relationship_types)
            rel_filter = f"[{rel_patterns}]"
        else:
            rel_filter = "[RELATES_TO|MENTIONS]"
        
        query = f"""
        CALL louvain(
            max_iterations: $max_iterations,
            resolution: $resolution
        ) YIELD node, community_id
        MATCH (n {{uuid: node.uuid}}) {node_filter}
        RETURN n.uuid AS uuid, community_id
        ORDER BY community_id, n.uuid
        """
        
        result, _, _ = await driver.execute_query(
            query,
            max_iterations=max_iterations,
            resolution=resolution
        )
        
        return {record['uuid']: int(record['community_id']) for record in result}
    
    @staticmethod
    async def connected_components(
        driver: Any,
        node_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
        direction: str = "undirected",
    ) -> dict[str, int]:
        """
        Find connected components using LadybugDB's native algorithm.
        
        Args:
            driver: GraphDriver instance
            node_types: Optional list of node types to include
            relationship_types: Optional list of relationship types to traverse
            direction: "directed" or "undirected"
            
        Returns:
            Dict mapping node UUIDs to component IDs
        """
        # Build node filter
        node_filter = ""
        if node_types:
            node_patterns = [f":{ntype}" for ntype in node_types]
            node_filter = f"WHERE {' OR '.join([f'n{pattern}' for pattern in node_patterns])}"
        
        # Build relationship filter
        rel_filter = ""
        if relationship_types:
            rel_patterns = "|".join(relationship_types)
            rel_filter = f"[{rel_patterns}]"
        else:
            rel_filter = "[RELATES_TO|MENTIONS]"
        
        query = f"""
        CALL connected_components(
            direction: $direction
        ) YIELD node, component_id
        MATCH (n {{uuid: node.uuid}}) {node_filter}
        RETURN n.uuid AS uuid, component_id
        ORDER BY component_id, n.uuid
        """
        
        result, _, _ = await driver.execute_query(query, direction=direction)
        
        return {record['uuid']: int(record['component_id']) for record in result}
    
    @staticmethod
    async def shortest_path(
        driver: Any,
        source_uuid: str,
        target_uuid: str,
        relationship_types: list[str] | None = None,
        max_depth: int = 10,
    ) -> list[str] | None:
        """
        Find shortest path between two nodes using LadybugDB's native algorithm.
        
        Args:
            driver: GraphDriver instance
            source_uuid: UUID of source node
            target_uuid: UUID of target node
            relationship_types: Optional list of relationship types to traverse
            max_depth: Maximum path depth
            
        Returns:
            List of node UUIDs in the path, or None if no path exists
        """
        # Build relationship filter
        rel_filter = ""
        if relationship_types:
            rel_patterns = "|".join(relationship_types)
            rel_filter = f"[{rel_patterns}]"
        else:
            rel_filter = "[RELATES_TO|MENTIONS]"
        
        query = f"""
        MATCH (source {{uuid: $source_uuid}}), (target {{uuid: $target_uuid}})
        CALL algo.shortestPath(source, target, '{rel_filter}', $max_depth) 
        YIELD path, distance
        RETURN path, distance
        """
        
        result, _, _ = await driver.execute_query(
            query,
            source_uuid=source_uuid,
            target_uuid=target_uuid,
            max_depth=max_depth
        )
        
        if not result:
            return None
        
        # Extract node UUIDs from the path
        path_record = result[0]
        if 'path' in path_record:
            # Assuming path is returned as a list of nodes or node IDs
            path = path_record['path']
            if isinstance(path, list):
                return [str(node) for node in path]
        
        return None
    
    @staticmethod
    async def node_centrality(
        driver: Any,
        centrality_type: str = "betweenness",
        node_types: list[str] | None = None,
        relationship_types: list[str] | None = None,
    ) -> dict[str, float]:
        """
        Compute various centrality measures using LadybugDB's native algorithms.
        
        Args:
            driver: GraphDriver instance
            centrality_type: Type of centrality ("betweenness", "closeness", "degree")
            node_types: Optional list of node types to include
            relationship_types: Optional list of relationship types to traverse
            
        Returns:
            Dict mapping node UUIDs to centrality scores
        """
        # Build node filter
        node_filter = ""
        if node_types:
            node_patterns = [f":{ntype}" for ntype in node_types]
            node_filter = f"WHERE {' OR '.join([f'n{pattern}' for pattern in node_patterns])}"
        
        # Build relationship filter
        rel_filter = ""
        if relationship_types:
            rel_patterns = "|".join(relationship_types)
            rel_filter = f"[{rel_patterns}]"
        else:
            rel_filter = "[RELATES_TO|MENTIONS]"
        
        query = f"""
        CALL {centrality_type}_centrality() YIELD node, score
        MATCH (n {{uuid: node.uuid}}) {node_filter}
        RETURN n.uuid AS uuid, score
        ORDER BY score DESC
        """
        
        result, _, _ = await driver.execute_query(query)
        
        return {record['uuid']: float(record['score']) for record in result}


# Algorithm-based rerankers for search results
class LadybugAlgorithmRerankers:
    """
    Reranker implementations that use LadybugDB's native graph algorithms.
    """
    
    @staticmethod
    async def pagerank_reranker(
        driver: Any,
        node_uuids: list[str],
        min_score: float = 0.0,
    ) -> tuple[list[str], list[float]]:
        """
        Rerank nodes by their PageRank scores.
        """
        scores = await LadybugGraphAlgorithms.pagerank(driver)
        
        # Filter and sort by PageRank score
        filtered_results = [
            (uuid, scores.get(uuid, 0.0)) 
            for uuid in node_uuids 
            if scores.get(uuid, 0.0) >= min_score
        ]
        
        sorted_results = sorted(filtered_results, key=lambda x: x[1], reverse=True)
        
        if sorted_results:
            uuids, pagerank_scores = zip(*sorted_results)
            return list(uuids), list(pagerank_scores)
        else:
            return [], []
    
    @staticmethod
    async def community_reranker(
        driver: Any,
        node_uuids: list[str],
        center_node_uuid: str,
        min_score: float = 0.0,
    ) -> tuple[list[str], list[float]]:
        """
        Rerank nodes by community membership - prioritize nodes in the same community as center.
        """
        communities = await LadybugGraphAlgorithms.louvain_communities(driver)
        
        # Get community of center node
        center_community = communities.get(center_node_uuid)
        
        if center_community is None:
            return [], []
        
        # Score nodes: 1.0 if same community, 0.0 otherwise
        filtered_results = []
        for uuid in node_uuids:
            node_community = communities.get(uuid)
            if node_community == center_community:
                filtered_results.append((uuid, 1.0))
        
        # Sort by UUID for consistent ordering within same community
        sorted_results = sorted(filtered_results, key=lambda x: x[0])
        
        if sorted_results:
            uuids, community_scores = zip(*sorted_results)
            return list(uuids), list(community_scores)
        else:
            return [], []
    
    @staticmethod
    async def centrality_reranker(
        driver: Any,
        node_uuids: list[str],
        centrality_type: str = "betweenness",
        min_score: float = 0.0,
    ) -> tuple[list[str], list[float]]:
        """
        Rerank nodes by centrality measures.
        """
        scores = await LadybugGraphAlgorithms.node_centrality(driver, centrality_type)
        
        # Filter and sort by centrality score
        filtered_results = [
            (uuid, scores.get(uuid, 0.0)) 
            for uuid in node_uuids 
            if scores.get(uuid, 0.0) >= min_score
        ]
        
        sorted_results = sorted(filtered_results, key=lambda x: x[1], reverse=True)
        
        if sorted_results:
            uuids, centrality_scores = zip(*sorted_results)
            return list(uuids), list(centrality_scores)
        else:
            return [], []
