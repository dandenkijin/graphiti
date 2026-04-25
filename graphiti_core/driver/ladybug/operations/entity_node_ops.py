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
from graphiti_core.driver.operations.entity_node_ops import EntityNodeOperations
from graphiti_core.driver.query_executor import QueryExecutor, Transaction
from graphiti_core.driver.record_parsers import entity_node_from_record
from graphiti_core.errors import NodeNotFoundError
from graphiti_core.models.nodes.node_db_queries import (
    get_entity_node_save_query,
    get_entity_node_return_query,
)
from graphiti_core.nodes import EntityNode

logger = logging.getLogger(__name__)


class LadybugEntityNodeOperations(EntityNodeOperations):
    async def save(
        self,
        executor: QueryExecutor,
        node: EntityNode,
        tx: Transaction | None = None,
    ) -> None:
        query = get_entity_node_save_query(GraphProvider.LADYBUG)
        params: dict[str, Any] = {
            'uuid': node.uuid,
            'name': node.name,
            'group_id': node.group_id,
            'summary': node.summary,
            'name_embedding': node.name_embedding,
            'created_at': node.created_at,
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
    ) -> EntityNode:
        entity_node_return = get_entity_node_return_query(GraphProvider.LADYBUG)
        query = f"""
        MATCH (n:Entity {{uuid: $uuid}})
        RETURN {entity_node_return}
        """
        params = {'uuid': uuid}
        result = await executor.execute_query(query, params, tx)
        
        if not result:
            raise NodeNotFoundError(f'Entity node with uuid {uuid} not found')
        
        return entity_node_from_record(result[0])

    async def get_by_group_id(
        self,
        executor: QueryExecutor,
        group_id: str,
        tx: Transaction | None = None,
    ) -> list[EntityNode]:
        entity_node_return = get_entity_node_return_query(GraphProvider.LADYBUG)
        query = f"""
        MATCH (n:Entity {{group_id: $group_id}})
        RETURN {entity_node_return}
        ORDER BY n.created_at DESC
        """
        params = {'group_id': group_id}
        result = await executor.execute_query(query, params, tx)
        
        return [entity_node_from_record(record) for record in result]

    async def get_by_name(
        self,
        executor: QueryExecutor,
        name: str,
        tx: Transaction | None = None,
    ) -> list[EntityNode]:
        entity_node_return = get_entity_node_return_query(GraphProvider.LADYBUG)
        query = f"""
        MATCH (n:Entity {{name: $name}})
        RETURN {entity_node_return}
        ORDER BY n.created_at DESC
        """
        params = {'name': name}
        result = await executor.execute_query(query, params, tx)
        
        return [entity_node_from_record(record) for record in result]

    async def delete_by_uuid(
        self,
        executor: QueryExecutor,
        uuid: str,
        tx: Transaction | None = None,
    ) -> None:
        query = """
        MATCH (n:Entity {uuid: $uuid})
        DETACH DELETE n
        """
        params = {'uuid': uuid}
        await executor.execute_query(query, params, tx)

    async def update_summary(
        self,
        executor: QueryExecutor,
        uuid: str,
        summary: str,
        tx: Transaction | None = None,
    ) -> None:
        query = """
        MATCH (n:Entity {uuid: $uuid})
        SET n.summary = $summary
        """
        params = {'uuid': uuid, 'summary': summary}
        await executor.execute_query(query, params, tx)

    async def update_name_embedding(
        self,
        executor: QueryExecutor,
        uuid: str,
        name_embedding: list[float],
        tx: Transaction | None = None,
    ) -> None:
        query = """
        MATCH (n:Entity {uuid: $uuid})
        SET n.name_embedding = $name_embedding
        """
        params = {'uuid': uuid, 'name_embedding': name_embedding}
        await executor.execute_query(query, params, tx)
