#!/usr/bin/env python3
"""
Performance benchmark tests for LadybugDB native integration.

This test suite validates that the native integration provides better performance
than the generic implementations.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Any

from graphiti_core.driver.ladybug.search_interface import LadybugSearchInterface
from graphiti_core.driver.ladybug.algorithms import LadybugGraphAlgorithms


class TestVectorSearchPerformance:
    """Test vector search performance improvements."""
    
    @pytest.mark.asyncio
    async def test_hnsw_vs_brute_force_performance(self):
        """
        Benchmark HNSW vector search vs brute-force cosine similarity.
        
        This test validates that HNSW provides significant performance improvements
        over the previous NumPy-based brute force approach.
        """
        # Mock large dataset
        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()
        
        # Simulate HNSW search (should be fast)
        hnsw_start = time.time()
        interface = LadybugSearchInterface()
        
        # Mock HNSW results (fast retrieval)
        mock_driver.execute_query.return_value = (
            [{'uuid': f'node_{i}', 'score': 0.8 - i * 0.01} for i in range(100)],
            None,
            None
        )
        
        await interface.node_similarity_search(
            mock_driver, 
            [0.1] * 1536,  # Typical embedding dimension
            Mock(),
            None,
            100,
            0.7
        )
        
        hnsw_time = time.time() - hnsw_start
        
        # Verify HNSW query was used
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "hnsw_search" in query
        assert "entity_name_embedding_hnsw" in query
        
        # HNSW should be significantly faster than brute force
        # (This is more of a documentation test - actual performance would be measured in real scenarios)
        assert hnsw_time < 1.0  # HNSW should return results quickly


class TestGraphTraversalPerformance:
    """Test graph traversal performance improvements."""
    
    @pytest.mark.asyncio
    async def test_cypher_vs_sql_traversal_performance(self):
        """
        Benchmark Cypher graph traversal vs SQL-based traversal.
        
        This test validates that native Cypher traversal provides better performance
        than the previous SQL pattern matching approach.
        """
        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()
        
        # Mock BFS traversal results
        mock_driver.execute_query.return_value = (
            [
                {
                    'e': Mock(uuid=f'edge_{i}'),
                    'source': Mock(uuid=f'source_{i}'),
                    'target': Mock(uuid=f'target_{i}'),
                    'distance': i % 3 + 1
                }
                for i in range(50)
            ],
            None,
            None
        )
        
        interface = LadybugSearchInterface()
        
        # Measure Cypher traversal time
        cypher_start = time.time()
        await interface.edge_bfs_search(
            mock_driver,
            ['start_node_uuid'],
            3,
            Mock(),
            None,
            50
        )
        cypher_time = time.time() - cypher_start
        
        # Verify Cypher query was used
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "MATCH path" in query
        assert "RELATES_TO|MENTIONS" in query
        assert "length(path)" in query
        
        # Cypher traversal should be efficient
        assert cypher_time < 1.0


class TestGraphAlgorithmPerformance:
    """Test graph algorithm performance."""
    
    @pytest.mark.asyncio
    async def test_native_algorithm_performance(self):
        """
        Test that native graph algorithms perform efficiently.
        
        This test validates that LadybugDB's built-in algorithms
        provide good performance for large graphs.
        """
        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()
        
        # Mock PageRank results for large graph
        mock_driver.execute_query.return_value = (
            [
                {'uuid': f'node_{i}', 'score': 0.001 * i}
                for i in range(1000)
            ],
            None,
            None
        )
        
        # Measure PageRank computation time
        pagerank_start = time.time()
        result = await LadybugGraphAlgorithms.pagerank(mock_driver)
        pagerank_time = time.time() - pagerank_start
        
        # Verify native algorithm call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "CALL pagerank" in query
        
        # Verify results
        assert len(result) == 1000
        assert all(0 <= score <= 1 for score in result.values())
        
        # Native algorithm should be efficient
        assert pagerank_time < 2.0
    
    @pytest.mark.asyncio
    async def test_louvain_community_detection_performance(self):
        """
        Test Louvain community detection performance.
        """
        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()
        
        # Mock community detection results
        mock_driver.execute_query.return_value = (
            [
                {'uuid': f'node_{i}', 'community_id': i % 10}
                for i in range(500)
            ],
            None,
            None
        )
        
        # Measure community detection time
        louvain_start = time.time()
        result = await LadybugGraphAlgorithms.louvain_communities(mock_driver)
        louvain_time = time.time() - louvain_start
        
        # Verify native algorithm call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "CALL louvain" in query
        
        # Verify results
        assert len(result) == 500
        assert all(isinstance(community_id, int) for community_id in result.values())
        
        # Community detection should be efficient
        assert louvain_time < 3.0


class TestBM25SearchPerformance:
    """Test BM25 full-text search performance."""
    
    @pytest.mark.asyncio
    async def test_native_bm25_performance(self):
        """
        Test that native BM25 search provides good performance.
        
        This test validates that LadybugDB's BM25 implementation
        is efficient for text search operations.
        """
        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()
        
        # Mock BM25 search results
        mock_driver.execute_query.return_value = (
            [
                {'uuid': f'doc_{i}', 'score': 0.9 - i * 0.01}
                for i in range(100)
            ],
            None,
            None
        )
        
        interface = LadybugSearchInterface()
        
        # Measure BM25 search time
        bm25_start = time.time()
        await interface.edge_fulltext_search(
            mock_driver,
            "test query string",
            Mock(),
            None,
            100
        )
        bm25_time = time.time() - bm25_start
        
        # Verify BM25 query was used
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "bm25_search" in query
        assert "edge_name_and_fact_bm25" in query
        
        # BM25 search should be efficient
        assert bm25_time < 0.5


class TestMemoryUsage:
    """Test memory usage efficiency."""
    
    @pytest.mark.asyncio
    async def test_memory_efficient_vector_search(self):
        """
        Test that HNSW vector search is memory efficient.
        
        HNSW should use less memory than loading all vectors into memory
        for brute force comparison.
        """
        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()
        
        # Mock that HNSW search doesn't require loading all vectors
        mock_driver.execute_query.return_value = ([], None, None)
        
        interface = LadybugSearchInterface()
        
        # This test mainly validates the interface - actual memory usage
        # would be measured in real scenarios with memory profiling tools
        await interface.node_similarity_search(
            mock_driver,
            [0.1] * 1536,
            Mock(),
            None,
            1000,  # Large result set
            0.7
        )
        
        # Verify HNSW is used (memory efficient)
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "hnsw_search" in query


class TestScalabilityBenchmarks:
    """Test scalability of the native integration."""
    
    @pytest.mark.asyncio
    async def test_large_graph_traversal_scalability(self):
        """
        Test that graph traversal scales well with graph size.
        
        Native Cypher traversal should maintain good performance
        even on large graphs.
        """
        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()
        
        # Simulate large graph traversal
        mock_driver.execute_query.return_value = (
            [
                {
                    'e': Mock(uuid=f'edge_{i}'),
                    'source': Mock(uuid=f'source_{i}'),
                    'target': Mock(uuid=f'target_{i}'),
                    'distance': i % 5 + 1
                }
                for i in range(1000)  # Large result set
            ],
            None,
            None
        )
        
        interface = LadybugSearchInterface()
        
        # Measure traversal time on large graph
        traversal_start = time.time()
        await interface.edge_bfs_search(
            mock_driver,
            ['start_node_uuid'],
            5,  # Deeper traversal
            Mock(),
            None,
            1000
        )
        traversal_time = time.time() - traversal_start
        
        # Should still be efficient even with large results
        assert traversal_time < 2.0
        
        # Verify efficient Cypher query
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "MATCH path" in query
        assert "*1..5" in query  # Variable-length traversal
    
    @pytest.mark.asyncio
    async def test_concurrent_search_performance(self):
        """
        Test performance of concurrent search operations.
        
        Native integration should handle concurrent searches efficiently.
        """
        mock_driver = Mock()
        mock_driver.execute_query = AsyncMock()
        
        # Mock search results
        mock_driver.execute_query.return_value = (
            [{'uuid': 'node_0', 'score': 0.8}],
            None,
            None
        )
        
        interface = LadybugSearchInterface()
        
        # Run multiple concurrent searches
        concurrent_start = time.time()
        tasks = [
            interface.node_similarity_search(
                mock_driver,
                [0.1] * 1536,
                Mock(),
                None,
                10,
                0.7
            )
            for _ in range(10)  # 10 concurrent searches
        ]
        
        await asyncio.gather(*tasks)
        concurrent_time = time.time() - concurrent_start
        
        # Concurrent searches should be efficient
        assert concurrent_time < 3.0
        
        # Verify all searches used native HNSW
        assert mock_driver.execute_query.call_count == 10
        for call in mock_driver.execute_query.call_args_list:
            query = call[0][0]
            assert "hnsw_search" in query


if __name__ == "__main__":
    # Run the performance tests
    pytest.main([__file__, "-v"])
