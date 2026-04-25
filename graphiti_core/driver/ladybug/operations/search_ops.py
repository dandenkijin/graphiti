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

import logging
from typing import Any

from graphiti_core.driver.driver import GraphProvider
from graphiti_core.driver.operations.search_ops import SearchOperations
from graphiti_core.driver.query_executor import QueryExecutor, Transaction
from graphiti_core.search.search_filter import SearchFilter
from graphiti_core.search.search_types import (
    SearchResponse,
    SearchResult,
    SearchType,
)

logger = logging.getLogger(__name__)


class LadybugSearchOperations(SearchOperations):
    async def edge_fulltext_search(
        self,
        executor: QueryExecutor,
        query: str,
        search_filter: SearchFilter,
        group_ids: list[str] | None = None,
        limit: int = 100,
        tx: Transaction | None = None,
    ) -> SearchResponse:
        """Perform BM25 full-text search over edge facts and names using LadybugDB's native FTS."""
        fts_query = f"""
        CALL QUERY_FTS_INDEX('RelatesToNode_', 'edge_name_and_fact_bm25', $query, TOP := $limit) 
        YIELD node, distance
        MATCH (n:Entity)-[:RELATES_TO]->(e:RelatesToNode_ {{uuid: node.uuid}})-[:RELATES_TO]->(m:Entity)
        WHERE distance <= $max_distance
        """
        
        if group_ids:
            fts_query += " WHERE e.group_id IN $group_ids"
        
        fts_query += " RETURN e, n, m, distance as score"
        
        # Convert search filter score to max_distance (inverse relationship)
        max_distance = 1.0 - search_filter.min_score  # Higher score = lower distance
        
        params = {
            'query': query,
            'limit': limit,
            'max_distance': max_distance,
            'group_ids': group_ids
        }
        
        result = await executor.execute_query(fts_query, params, tx)
        
        search_results = []
        for record in result:
            search_result = SearchResult(
                uuid=record['e']['uuid'],
                name=record['e']['name'],
                description=record['e']['fact'],
                score=record['score'],
                metadata={
                    'source_node': record['n'],
                    'target_node': record['m'],
                    'edge_data': record['e']
                }
            )
            search_results.append(search_result)
        
        return SearchResponse(
            results=search_results,
            search_type=SearchType.FULLTEXT,
            query=query,
            total=len(search_results)
        )

    async def edge_similarity_search(
        self,
        executor: QueryExecutor,
        search_vector: list[float],
        search_filter: SearchFilter,
        group_ids: list[str] | None = None,
        limit: int = 100,
        tx: Transaction | None = None,
    ) -> SearchResponse:
        """Perform HNSW vector similarity search over edge fact embeddings."""
        vector_query = f"""
        CALL QUERY_VECTOR_INDEX('RelatesToNode_', 'fact_embedding_hnsw', $search_vector, $limit) 
        WITH node AS result_node, distance
        MATCH (n:Entity)-[:RELATES_TO]->(e:RelatesToNode_ {{uuid: result_node.uuid}})-[:RELATES_TO]->(m:Entity)
        WHERE distance <= $max_distance
        """
        
        filter_conditions = []
        if search_filter.source_node_uuid:
            filter_conditions.append("n.uuid = $source_uuid")
        if search_filter.target_node_uuid:
            filter_conditions.append("m.uuid = $target_uuid")
        if group_ids:
            filter_conditions.append("e.group_id IN $group_ids")
        
        if filter_conditions:
            vector_query += " AND " + " AND ".join(filter_conditions)
        
        vector_query += " RETURN e, n, m, distance as score"
        
        # Convert min_score to max_distance (inverse relationship)
        max_distance = 1.0 - search_filter.min_score
        
        params = {
            'search_vector': search_vector,
            'limit': limit,
            'max_distance': max_distance,
            'source_uuid': search_filter.source_node_uuid,
            'target_uuid': search_filter.target_node_uuid,
            'group_ids': group_ids
        }
        
        result = await executor.execute_query(vector_query, params, tx)
        
        search_results = []
        for record in result:
            search_result = SearchResult(
                uuid=record['e']['uuid'],
                name=record['e']['name'],
                description=record['e']['fact'],
                score=record['score'],
                metadata={
                    'source_node': record['n'],
                    'target_node': record['m'],
                    'edge_data': record['e']
                }
            )
            search_results.append(search_result)
        
        return SearchResponse(
            results=search_results,
            search_type=SearchType.SIMILARITY,
            query="vector_search",
            total=len(search_results)
        )

    async def node_fulltext_search(
        self,
        executor: QueryExecutor,
        query: str,
        search_filter: SearchFilter,
        group_ids: list[str] | None = None,
        limit: int = 100,
        tx: Transaction | None = None,
    ) -> SearchResponse:
        """Perform BM25 full-text search over node names and summaries."""
        fts_query = """
        CALL QUERY_FTS_INDEX('Entity', 'entity_name_bm25', $query, TOP := $limit) 
        YIELD node, distance
        MATCH (n:Entity {uuid: node.uuid})
        WHERE distance <= $max_distance
        """
        
        if group_ids:
            fts_query += " WHERE n.group_id IN $group_ids"
        
        fts_query += " RETURN n, distance as score"
        
        # Convert min_score to max_distance (inverse relationship)
        max_distance = 1.0 - search_filter.min_score
        
        params = {
            'query': query,
            'limit': limit,
            'max_distance': max_distance,
            'group_ids': group_ids
        }
        
        result = await executor.execute_query(fts_query, params, tx)
        
        search_results = []
        for record in result:
            search_result = SearchResult(
                uuid=record['n']['uuid'],
                name=record['n']['name'],
                description=record['n']['summary'],
                score=record['score'],
                metadata={'node_data': record['n']}
            )
            search_results.append(search_result)
        
        return SearchResponse(
            results=search_results,
            search_type=SearchType.FULLTEXT,
            query=query,
            total=len(search_results)
        )

    async def node_similarity_search(
        self,
        executor: QueryExecutor,
        search_vector: list[float],
        search_filter: SearchFilter,
        group_ids: list[str] | None = None,
        limit: int = 100,
        tx: Transaction | None = None,
    ) -> SearchResponse:
        """Perform HNSW vector similarity search over node name embeddings."""
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
        max_distance = 1.0 - search_filter.min_score
        
        params = {
            'search_vector': search_vector,
            'limit': limit,
            'max_distance': max_distance,
            'group_ids': group_ids
        }
        
        result = await executor.execute_query(vector_query, params, tx)
        
        search_results = []
        for record in result:
            search_result = SearchResult(
                uuid=record['n']['uuid'],
                name=record['n']['name'],
                description=record['n']['summary'],
                score=record['score'],
                metadata={'node_data': record['n']}
            )
            search_results.append(search_result)
        
        return SearchResponse(
            results=search_results,
            search_type=SearchType.SIMILARITY,
            query="vector_search",
            total=len(search_results)
        )

    async def episode_fulltext_search(
        self,
        executor: QueryExecutor,
        query: str,
        search_filter: SearchFilter,
        group_ids: list[str] | None = None,
        limit: int = 100,
        tx: Transaction | None = None,
    ) -> SearchResponse:
        """Perform BM25 full-text search over episode content."""
        fts_query = """
        CALL QUERY_FTS_INDEX('Episodic', 'episodic_content_bm25', $query, TOP := $limit) 
        YIELD node, distance
        MATCH (e:Episodic {uuid: node.uuid})
        WHERE distance <= $max_distance
        """
        
        if group_ids:
            fts_query += " WHERE e.group_id IN $group_ids"
        
        fts_query += " RETURN e, distance as score"
        
        # Convert min_score to max_distance (inverse relationship)
        max_distance = 1.0 - search_filter.min_score
        
        params = {
            'query': query,
            'limit': limit,
            'max_distance': max_distance,
            'group_ids': group_ids
        }
        
        result = await executor.execute_query(fts_query, params, tx)
        
        search_results = []
        for record in result:
            search_result = SearchResult(
                uuid=record['e']['uuid'],
                name=record['e']['name'],
                description=record['e']['content'],
                score=record['score'],
                metadata={'episode_data': record['e']}
            )
            search_results.append(search_result)
        
        return SearchResponse(
            results=search_results,
            search_type=SearchType.FULLTEXT,
            query=query,
            total=len(search_results)
        )

    async def community_similarity_search(
        self,
        executor: QueryExecutor,
        search_vector: list[float],
        group_ids: list[str] | None = None,
        limit: int = 100,
        min_score: float = 0.6,
        tx: Transaction | None = None,
    ) -> SearchResponse:
        """Perform HNSW vector similarity search over community name embeddings."""
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
        max_distance = 1.0 - min_score
        
        params = {
            'search_vector': search_vector,
            'limit': limit,
            'max_distance': max_distance,
            'group_ids': group_ids
        }
        
        result = await executor.execute_query(vector_query, params, tx)
        
        search_results = []
        for record in result:
            search_result = SearchResult(
                uuid=record['c']['uuid'],
                name=record['c']['name'],
                description=record['c']['summary'],
                score=record['score'],
                metadata={'community_data': record['c']}
            )
            search_results.append(search_result)
        
        return SearchResponse(
            results=search_results,
            search_type=SearchType.SIMILARITY,
            query="vector_search",
            total=len(search_results)
        )
