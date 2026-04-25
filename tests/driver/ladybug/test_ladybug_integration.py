#!/usr/bin/env python3
"""
Comprehensive tests for LadybugDB native integration.

This test suite validates that all 4 retrieval methods are properly integrated
with LadybugDB's native capabilities.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Any

# Import the components we're testing
from graphiti_core.driver.ladybug_driver import LadybugDriver
from graphiti_core.driver.ladybug.search_interface import LadybugSearchInterface
from graphiti_core.driver.ladybug.algorithms import LadybugGraphAlgorithms, LadybugAlgorithmRerankers
from graphiti_core.driver.driver import GraphProvider


class TestLadybugDBIntegration:
    """Test suite for LadybugDB native integration."""
    
    @pytest.fixture
    def mock_real_ladybug(self):
        """Mock real_ladybug package for testing."""
        with patch('graphiti_core.driver.ladybug_driver.real_ladybug') as mock:
            # Mock Database and Connection classes
            mock.Database = Mock()
            mock.Connection = Mock()
            yield mock
    
    @pytest.fixture
    def ladybug_driver(self, mock_real_ladybug):
        """Create a LadybugDriver instance for testing."""
        # Don't mock LadybugSearchInterface so we can test the real implementation
        driver = LadybugDriver(db=":memory:")
        return driver
    
    def test_ladybug_provider_enum(self):
        """Test that LADYBUG provider is properly added to enum."""
        assert GraphProvider.LADYBUG.value == 'ladybug'
        assert hasattr(GraphProvider, 'LADYBUG')
    
    def test_driver_uses_ladybug_provider(self, ladybug_driver):
        """Test that driver uses LADYBUG provider instead of KUZU."""
        assert ladybug_driver.provider == GraphProvider.LADYBUG
        assert ladybug_driver.provider != GraphProvider.KUZU
    
    def test_driver_has_search_interface(self, ladybug_driver):
        """Test that driver initializes with LadybugSearchInterface."""
        assert ladybug_driver.search_interface is not None
        assert isinstance(ladybug_driver.search_interface, LadybugSearchInterface)
    
    @pytest.mark.asyncio
    async def test_hnsw_vector_indexes_created(self, ladybug_driver, mock_real_ladybug):
        """Test that HNSW vector indexes are created during schema setup."""
        # Mock connection
        mock_conn = Mock()
        mock_conn.execute = Mock()
        
        # Mock the get_connection context manager
        ladybug_driver.get_connection = Mock()
        ladybug_driver.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        ladybug_driver.get_connection.return_value.__exit__ = Mock(return_value=None)
        
        # Run schema setup
        ladybug_driver.setup_schema()
        
        # Verify HNSW vector index creation calls
        vector_index_queries = [
            call[0][0] for call in mock_conn.execute.call_args_list
            if "CREATE_VECTOR_INDEX" in call[0][0] and "HNSW" in call[0][0]
        ]
        
        assert len(vector_index_queries) >= 3  # Entity, RelatesToNode_, Community
        assert "entity_name_embedding_hnsw" in vector_index_queries[0]
        assert "fact_embedding_hnsw" in vector_index_queries[1]
        assert "community_name_embedding_hnsw" in vector_index_queries[2]
    
    @pytest.mark.asyncio
    async def test_bm25_indexes_created(self, ladybug_driver, mock_real_ladybug):
        """Test that BM25 indexes are created during schema setup."""
        # Mock connection
        mock_conn = Mock()
        mock_conn.execute = Mock()
        
        # Mock the get_connection context manager
        ladybug_driver.get_connection = Mock()
        ladybug_driver.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        ladybug_driver.get_connection.return_value.__exit__ = Mock(return_value=None)
        
        # Run schema setup
        ladybug_driver.setup_schema()
        
        # Verify BM25 index creation calls
        bm25_index_queries = [
            call[0][0] for call in mock_conn.execute.call_args_list
            if "CREATE_BM25_INDEX" in call[0][0]
        ]
        
        assert len(bm25_index_queries) >= 3  # Entity, RelatesToNode_, Episodic
        assert "edge_name_and_fact_bm25" in bm25_index_queries[0]
        assert "entity_name_bm25" in bm25_index_queries[1]
        assert "episodic_content_bm25" in bm25_index_queries[2]


class TestLadybugSearchInterface:
    """Test suite for LadybugSearchInterface."""
    
    @pytest.fixture
    def search_interface(self):
        """Create LadybugSearchInterface instance."""
        return LadybugSearchInterface()
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock driver for testing."""
        driver = Mock()
        driver.execute_query = AsyncMock(return_value=([], None, None))
        return driver
    
    @pytest.mark.asyncio
    async def test_edge_fulltext_search_uses_bm25(self, search_interface, mock_driver):
        """Test that edge fulltext search uses native BM25."""
        mock_driver.execute_query.return_value = ([], None, None)
        
        await search_interface.edge_fulltext_search(
            mock_driver, "test query", Mock(), ["group1"], 10
        )
        
        # Verify BM25 search call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "bm25_search" in query
        assert "edge_name_and_fact_bm25" in query
    
    @pytest.mark.asyncio
    async def test_edge_similarity_search_uses_hnsw(self, search_interface, mock_driver):
        """Test that edge similarity search uses native HNSW."""
        mock_driver.execute_query.return_value = ([], None, None)
        
        await search_interface.edge_similarity_search(
            mock_driver, [0.1, 0.2, 0.3], None, None, Mock(), ["group1"], 10, 0.7
        )
        
        # Verify HNSW search call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "hnsw_search" in query
        assert "fact_embedding_hnsw" in query
    
    @pytest.mark.asyncio
    async def test_node_fulltext_search_uses_bm25(self, search_interface, mock_driver):
        """Test that node fulltext search uses native BM25."""
        mock_driver.execute_query.return_value = ([], None, None)
        
        await search_interface.node_fulltext_search(
            mock_driver, "test query", Mock(), ["group1"], 10
        )
        
        # Verify BM25 search call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "bm25_search" in query
        assert "entity_name_bm25" in query
    
    @pytest.mark.asyncio
    async def test_node_similarity_search_uses_hnsw(self, search_interface, mock_driver):
        """Test that node similarity search uses native HNSW."""
        mock_driver.execute_query.return_value = ([], None, None)
        
        await search_interface.node_similarity_search(
            mock_driver, [0.1, 0.2, 0.3], Mock(), ["group1"], 10, 0.7
        )
        
        # Verify HNSW search call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "hnsw_search" in query
        assert "entity_name_embedding_hnsw" in query
    
    @pytest.mark.asyncio
    async def test_episode_fulltext_search_uses_bm25(self, search_interface, mock_driver):
        """Test that episode fulltext search uses native BM25."""
        mock_driver.execute_query.return_value = ([], None, None)
        
        await search_interface.episode_fulltext_search(
            mock_driver, "test query", Mock(), ["group1"], 10
        )
        
        # Verify BM25 search call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "bm25_search" in query
        assert "episodic_content_bm25" in query
    
    @pytest.mark.asyncio
    async def test_community_similarity_search_uses_hnsw(self, search_interface, mock_driver):
        """Test that community similarity search uses native HNSW."""
        mock_driver.execute_query.return_value = ([], None, None)
        
        await search_interface.community_similarity_search(
            mock_driver, [0.1, 0.2, 0.3], ["group1"], 10, 0.6
        )
        
        # Verify HNSW search call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "hnsw_search" in query
        assert "community_name_embedding_hnsw" in query
    
    @pytest.mark.asyncio
    async def test_edge_bfs_search_uses_cypher(self, search_interface, mock_driver):
        """Test that edge BFS search uses native Cypher traversal."""
        mock_driver.execute_query.return_value = ([], None, None)
        
        await search_interface.edge_bfs_search(
            mock_driver, ["uuid1", "uuid2"], 3, Mock(), ["group1"], 10
        )
        
        # Verify Cypher traversal call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "MATCH path" in query
        assert "RELATES_TO|MENTIONS" in query
        assert "length(path)" in query
    
    @pytest.mark.asyncio
    async def test_node_bfs_search_uses_cypher(self, search_interface, mock_driver):
        """Test that node BFS search uses native Cypher traversal."""
        mock_driver.execute_query.return_value = ([], None, None)
        
        await search_interface.node_bfs_search(
            mock_driver, ["uuid1", "uuid2"], Mock(), 3, ["group1"], 10
        )
        
        # Verify Cypher traversal call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "MATCH path" in query
        assert "RELATES_TO|MENTIONS" in query
        assert "length(path)" in query


class TestLadybugGraphAlgorithms:
    """Test suite for LadybugGraphAlgorithms."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock driver for testing."""
        driver = Mock()
        driver.execute_query = AsyncMock()
        return driver
    
    @pytest.mark.asyncio
    async def test_pagerank_algorithm(self, mock_driver):
        """Test PageRank algorithm integration."""
        # Mock algorithm results
        mock_driver.execute_query.return_value = (
            [
                {'uuid': 'node1', 'score': 0.5},
                {'uuid': 'node2', 'score': 0.3},
                {'uuid': 'node3', 'score': 0.2}
            ],
            None,
            None
        )
        
        result = await LadybugGraphAlgorithms.pagerank(mock_driver)
        
        # Verify algorithm call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "CALL pagerank" in query
        
        # Verify results
        assert len(result) == 3
        assert result['node1'] == 0.5
        assert result['node2'] == 0.3
        assert result['node3'] == 0.2
    
    @pytest.mark.asyncio
    async def test_louvain_algorithm(self, mock_driver):
        """Test Louvain community detection algorithm."""
        # Mock algorithm results
        mock_driver.execute_query.return_value = (
            [
                {'uuid': 'node1', 'community_id': 1},
                {'uuid': 'node2', 'community_id': 1},
                {'uuid': 'node3', 'community_id': 2}
            ],
            None,
            None
        )
        
        result = await LadybugGraphAlgorithms.louvain_communities(mock_driver)
        
        # Verify algorithm call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "CALL louvain" in query
        
        # Verify results
        assert len(result) == 3
        assert result['node1'] == 1
        assert result['node2'] == 1
        assert result['node3'] == 2
    
    @pytest.mark.asyncio
    async def test_connected_components_algorithm(self, mock_driver):
        """Test connected components algorithm."""
        # Mock algorithm results
        mock_driver.execute_query.return_value = (
            [
                {'uuid': 'node1', 'component_id': 1},
                {'uuid': 'node2', 'component_id': 1},
                {'uuid': 'node3', 'component_id': 2}
            ],
            None,
            None
        )
        
        result = await LadybugGraphAlgorithms.connected_components(mock_driver)
        
        # Verify algorithm call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "CALL connected_components" in query
        
        # Verify results
        assert len(result) == 3
        assert result['node1'] == 1
        assert result['node2'] == 1
        assert result['node3'] == 2
    
    @pytest.mark.asyncio
    async def test_shortest_path_algorithm(self, mock_driver):
        """Test shortest path algorithm."""
        # Mock algorithm results
        mock_driver.execute_query.return_value = (
            [{'path': ['node1', 'node2', 'node3'], 'distance': 2}],
            None,
            None
        )
        
        result = await LadybugGraphAlgorithms.shortest_path(
            mock_driver, 'node1', 'node3'
        )
        
        # Verify algorithm call
        call_args = mock_driver.execute_query.call_args
        query = call_args[0][0]
        assert "CALL algo.shortestPath" in query
        
        # Verify results
        assert result == ['node1', 'node2', 'node3']


class TestLadybugAlgorithmRerankers:
    """Test suite for LadybugAlgorithmRerankers."""
    
    @pytest.fixture
    def mock_driver(self):
        """Create mock driver for testing."""
        driver = Mock()
        driver.execute_query = AsyncMock()
        return driver
    
    @pytest.mark.asyncio
    async def test_pagerank_reranker(self, mock_driver):
        """Test PageRank-based reranking."""
        # Mock PageRank results
        with patch.object(LadybugGraphAlgorithms, 'pagerank') as mock_pagerank:
            mock_pagerank.return_value = {
                'node1': 0.8,
                'node2': 0.6,
                'node3': 0.4,
                'node4': 0.2
            }
            
            uuids, scores = await LadybugAlgorithmRerankers.pagerank_reranker(
                mock_driver, ['node3', 'node1', 'node4'], 0.3
            )
            
            # Verify results are sorted by PageRank score
            assert uuids == ['node1', 'node3']
            assert scores == [0.8, 0.4]
    
    @pytest.mark.asyncio
    async def test_community_reranker(self, mock_driver):
        """Test community-based reranking."""
        # Mock Louvain results
        with patch.object(LadybugGraphAlgorithms, 'louvain_communities') as mock_louvain:
            mock_louvain.return_value = {
                'center': 1,
                'node1': 1,
                'node2': 1,
                'node3': 2,
                'node4': 2
            }
            
            uuids, scores = await LadybugAlgorithmRerankers.community_reranker(
                mock_driver, ['node1', 'node2', 'node3', 'node4'], 'center'
            )
            
            # Verify only same-community nodes are returned
            assert uuids == ['node1', 'node2']
            assert scores == [1.0, 1.0]


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_all_four_retrieval_methods_integration(self):
        """Test that all 4 retrieval methods are properly integrated."""
        # This test validates that the integration is complete
        # by checking that all components are properly connected
        
        # 1. Check that LADYBUG provider exists
        assert GraphProvider.LADYBUG.value == 'ladybug'
        
        # 2. Check that SearchInterface implements all required methods
        interface = LadybugSearchInterface()
        required_methods = [
            'edge_fulltext_search', 'edge_similarity_search', 'edge_bfs_search',
            'node_fulltext_search', 'node_similarity_search', 'node_bfs_search',
            'episode_fulltext_search', 'community_fulltext_search',
            'community_similarity_search', 'node_distance_reranker',
            'episode_mentions_reranker'
        ]
        
        for method in required_methods:
            assert hasattr(interface, method), f"Missing method: {method}"
        
        # 3. Check that algorithm classes exist
        assert LadybugGraphAlgorithms is not None
        assert LadybugAlgorithmRerankers is not None
        
        # 4. Check that algorithm classes have required methods
        algorithm_methods = ['pagerank', 'louvain_communities', 'connected_components', 'shortest_path']
        for method in algorithm_methods:
            assert hasattr(LadybugGraphAlgorithms, method), f"Missing algorithm method: {method}"
        
        reranker_methods = ['pagerank_reranker', 'community_reranker', 'centrality_reranker']
        for method in reranker_methods:
            assert hasattr(LadybugAlgorithmRerankers, method), f"Missing reranker method: {method}"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
