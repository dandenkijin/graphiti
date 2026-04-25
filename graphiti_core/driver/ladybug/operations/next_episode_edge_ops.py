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
from graphiti_core.driver.operations.next_episode_edge_ops import NextEpisodeEdgeOperations
from graphiti_core.driver.query_executor import QueryExecutor, Transaction
from graphiti_core.driver.record_parsers import next_episode_edge_from_record
from graphiti_core.errors import EdgeNotFoundError
from graphiti_core.models.edges.edge_db_queries import (
    NEXT_EPISODE_EDGE_RETURN,
)
from graphiti_core.edges import NextEpisodeEdge

logger = logging.getLogger(__name__)


class LadybugNextEpisodeEdgeOperations(NextEpisodeEdgeOperations):
    async def save(
        self,
        executor: QueryExecutor,
        edge: NextEpisodeEdge,
        tx: Transaction | None = None,
    ) -> None:
        # Use a basic save query for LadybugDB next episode edges
        query = """
        MATCH (source:Episodic {uuid: $source_node_uuid})
        MATCH (target:Episodic {uuid: $target_node_uuid})
        MERGE (source)-[r:NEXT_EPISODE {uuid: $uuid}]->(target)
        SET
            r.group_id = $group_id,
            r.weight = $weight,
            r.created_at = $created_at,
            r.expired_at = $expired_at,
            r.valid_at = $valid_at,
            r.invalid_at = $invalid_at
        """
        params: dict[str, Any] = {
            'uuid': edge.uuid,
            'group_id': edge.group_id,
            'source_node_uuid': edge.source_node_uuid,
            'target_node_uuid': edge.target_node_uuid,
            'weight': edge.weight,
            'created_at': edge.created_at,
            'expired_at': edge.expired_at,
            'valid_at': edge.valid_at,
            'invalid_at': edge.invalid_at,
        }
        if tx is not None:
            await executor.execute_query(query, params, tx)
        else:
            await executor.execute_query(query, params)

    async def get_by_uuid(
        self,
        executor: QueryExecutor,
        uuid: str,
        tx: Transaction | None = None,
    ) -> NextEpisodeEdge:
        query = f"""
        MATCH (source:Episodic)-[r:NEXT_EPISODE]->(target:Episodic)
        WHERE r.uuid = $uuid
        RETURN {NEXT_EPISODE_EDGE_RETURN}
        """
        params = {'uuid': uuid}
        result = await executor.execute_query(query, params, tx)
        
        if not result:
            raise EdgeNotFoundError(f'NextEpisode edge with uuid {uuid} not found')
        
        return next_episode_edge_from_record(result[0])

    async def get_by_source_target(
        self,
        executor: QueryExecutor,
        source_node_uuid: str,
        target_node_uuid: str,
        tx: Transaction | None = None,
    ) -> list[NextEpisodeEdge]:
        query = f"""
        MATCH (source:Episodic)-[r:NEXT_EPISODE]->(target:Episodic)
        WHERE source.uuid = $source_node_uuid AND target.uuid = $target_node_uuid
        RETURN {NEXT_EPISODE_EDGE_RETURN}
        ORDER BY r.created_at DESC
        """
        params = {
            'source_node_uuid': source_node_uuid,
            'target_node_uuid': target_node_uuid,
        }
        result = await executor.execute_query(query, params, tx)
        
        return [next_episode_edge_from_record(record) for record in result]

    async def get_by_group_id(
        self,
        executor: QueryExecutor,
        group_id: str,
        tx: Transaction | None = None,
    ) -> list[NextEpisodeEdge]:
        query = f"""
        MATCH (source:Episodic)-[r:NEXT_EPISODE]->(target:Episodic)
        WHERE r.group_id = $group_id
        RETURN {NEXT_EPISODE_EDGE_RETURN}
        ORDER BY r.created_at DESC
        """
        params = {'group_id': group_id}
        result = await executor.execute_query(query, params, tx)
        
        return [next_episode_edge_from_record(record) for record in result]

    async def delete_by_uuid(
        self,
        executor: QueryExecutor,
        uuid: str,
        tx: Transaction | None = None,
    ) -> None:
        query = """
        MATCH (source:Episodic)-[r:NEXT_EPISODE]->(target:Episodic)
        WHERE r.uuid = $uuid
        DELETE r
        """
        params = {'uuid': uuid}
        await executor.execute_query(query, params, tx)

    async def update_weight(
        self,
        executor: QueryExecutor,
        uuid: str,
        weight: float,
        tx: Transaction | None = None,
    ) -> None:
        query = """
        MATCH (source:Episodic)-[r:NEXT_EPISODE]->(target:Episodic)
        WHERE r.uuid = $uuid
        SET r.weight = $weight
        """
        params = {'uuid': uuid, 'weight': weight}
        await executor.execute_query(query, params, tx)
