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
from graphiti_core.driver.operations.community_edge_ops import CommunityEdgeOperations
from graphiti_core.driver.query_executor import QueryExecutor, Transaction
from graphiti_core.edges import CommunityEdge
from graphiti_core.errors import EdgeNotFoundError
from graphiti_core.helpers import parse_db_date
from graphiti_core.models.edges.edge_db_queries import (
    COMMUNITY_EDGE_RETURN,
    get_community_edge_save_query,
)

logger = logging.getLogger(__name__)


def _community_edge_from_record(record: Any) -> CommunityEdge:
    return CommunityEdge(
        uuid=record['uuid'],
        group_id=record['group_id'],
        source_node_uuid=record['source_node_uuid'],
        target_node_uuid=record['target_node_uuid'],
        created_at=parse_db_date(record['created_at']),  # type: ignore[arg-type]
    )


class LadybugCommunityEdgeOperations(CommunityEdgeOperations):
    async def save(
        self,
        executor: QueryExecutor,
        edge: CommunityEdge,
        tx: Transaction | None = None,
    ) -> None:
        """Save a community edge to LadybugDB."""
        query = get_community_edge_save_query(GraphProvider.LADYBUG)
        params = {
            'uuid': str(edge.uuid),
            'group_id': str(edge.group_id),
            'source_node_uuid': str(edge.source_node_uuid),
            'target_node_uuid': str(edge.target_node_uuid),
            'created_at': edge.created_at,
        }
        await executor.execute_query(query, params, tx)

    async def get_by_uuid(
        self,
        executor: QueryExecutor,
        uuid: str,
        tx: Transaction | None = None,
    ) -> CommunityEdge:
        """Get a community edge by UUID from LadybugDB."""
        query = f"""
        MATCH (source:Entity)-[r:COMMUNITY_RELATES_TO]->(target:Entity)
        WHERE r.uuid = $uuid
        RETURN {COMMUNITY_EDGE_RETURN}
        """
        params = {'uuid': uuid}
        result = await executor.execute_query(query, params, tx)
        
        if not result:
            raise EdgeNotFoundError(f'Community edge with uuid {uuid} not found')
        
        return _community_edge_from_record(result[0])

    async def get_by_source_target(
        self,
        executor: QueryExecutor,
        source_node_uuid: str,
        target_node_uuid: str,
        tx: Transaction | None = None,
    ) -> list[CommunityEdge]:
        """Get community edges by source and target UUIDs from LadybugDB."""
        query = f"""
        MATCH (source:Entity)-[r:COMMUNITY_RELATES_TO]->(target:Entity)
        WHERE source.uuid = $source_node_uuid AND target.uuid = $target_node_uuid
        RETURN {COMMUNITY_EDGE_RETURN}
        ORDER BY r.created_at DESC
        """
        params = {
            'source_node_uuid': source_node_uuid,
            'target_node_uuid': target_node_uuid,
        }
        result = await executor.execute_query(query, params, tx)
        
        return [_community_edge_from_record(record) for record in result]

    async def get_by_group_id(
        self,
        executor: QueryExecutor,
        group_id: str,
        tx: Transaction | None = None,
    ) -> list[CommunityEdge]:
        """Get community edges by group ID from LadybugDB."""
        query = f"""
        MATCH (source:Entity)-[r:COMMUNITY_RELATES_TO]->(target:Entity)
        WHERE r.group_id = $group_id
        RETURN {COMMUNITY_EDGE_RETURN}
        ORDER BY r.created_at DESC
        """
        params = {'group_id': group_id}
        result = await executor.execute_query(query, params, tx)
        
        return [_community_edge_from_record(record) for record in result]

    async def delete_by_uuid(
        self,
        executor: QueryExecutor,
        uuid: str,
        tx: Transaction | None = None,
    ) -> None:
        """Delete a community edge by UUID from LadybugDB."""
        query = """
        MATCH (source:Entity)-[r:COMMUNITY_RELATES_TO]->(target:Entity)
        WHERE r.uuid = $uuid
        DELETE r
        """
        params = {'uuid': uuid}
        await executor.execute_query(query, params, tx)
