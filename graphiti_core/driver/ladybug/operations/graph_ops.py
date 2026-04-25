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
from graphiti_core.driver.operations.graph_ops import GraphMaintenanceOperations
from graphiti_core.driver.query_executor import QueryExecutor, Transaction
from graphiti_core.models.nodes.node_db_queries import (
    get_node_cleanup_query,
    get_edge_cleanup_query,
)

logger = logging.getLogger(__name__)


class LadybugGraphMaintenanceOperations(GraphMaintenanceOperations):
    async def cleanup_expired_nodes(
        self,
        executor: QueryExecutor,
        tx: Transaction | None = None,
    ) -> None:
        """Clean up expired nodes in LadybugDB."""
        query = get_node_cleanup_query(GraphProvider.LADYBUG)
        if tx is not None:
            await executor.execute_query(query, {}, tx)
        else:
            await executor.execute_query(query, {})

    async def cleanup_expired_edges(
        self,
        executor: QueryExecutor,
        tx: Transaction | None = None,
    ) -> None:
        """Clean up expired edges in LadybugDB."""
        query = get_edge_cleanup_query(GraphProvider.LADYBUG)
        if tx is not None:
            await executor.execute_query(query, {}, tx)
        else:
            await executor.execute_query(query, {})

    async def get_node_count(
        self,
        executor: QueryExecutor,
        tx: Transaction | None = None,
    ) -> dict[str, int]:
        """Get count of nodes by type in LadybugDB."""
        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(*) as count
        """
        result = await executor.execute_query(query, {}, tx)
        
        node_counts = {}
        for record in result:
            label = record.get('label', 'Unknown')
            node_counts[label] = record.get('count', 0)
        
        return node_counts

    async def get_edge_count(
        self,
        executor: QueryExecutor,
        tx: Transaction | None = None,
    ) -> dict[str, int]:
        """Get count of edges by type in LadybugDB."""
        query = """
        MATCH ()-[r]-()
        RETURN type(r) as edge_type, count(*) as count
        """
        result = await executor.execute_query(query, {}, tx)
        
        edge_counts = {}
        for record in result:
            edge_type = record.get('edge_type', 'Unknown')
            edge_counts[edge_type] = record.get('count', 0)
        
        return edge_counts

    async def create_constraints(
        self,
        executor: QueryExecutor,
        tx: Transaction | None = None,
    ) -> None:
        """Create constraints for LadybugDB."""
        # LadybugDB uses indexes rather than constraints
        constraints = [
            "CREATE INDEX IF NOT EXISTS idx_entity_uuid ON Entity (uuid)",
            "CREATE INDEX IF NOT EXISTS idx_episodic_uuid ON Episodic (uuid)",
            "CREATE INDEX IF NOT EXISTS idx_community_uuid ON Community (uuid)",
            "CREATE INDEX IF NOT EXISTS idx_entity_group_id ON Entity (group_id)",
            "CREATE INDEX IF NOT EXISTS idx_episodic_group_id ON Episodic (group_id)",
            "CREATE INDEX IF NOT EXISTS idx_community_group_id ON Community (group_id)",
        ]
        
        for constraint in constraints:
            if tx is not None:
                await executor.execute_query(constraint, {}, tx)
            else:
                await executor.execute_query(constraint, {})

    async def validate_schema(
        self,
        executor: QueryExecutor,
        tx: Transaction | None = None,
    ) -> bool:
        """Validate that the LadybugDB schema is correct."""
        try:
            # Check that required node types exist
            node_types_query = """
            MATCH (n) 
            RETURN DISTINCT labels(n) as node_types
            """
            result = await executor.execute_query(node_types_query, {}, tx)
            
            node_types = set()
            for record in result:
                node_types.update(record.get('node_types', []))
            
            required_nodes = {'Entity', 'Episodic', 'Community'}
            if not required_nodes.issubset(node_types):
                return False
            
            return True
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False
