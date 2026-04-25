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
from graphiti_core.driver.operations.saga_node_ops import SagaNodeOperations
from graphiti_core.driver.query_executor import QueryExecutor, Transaction
from graphiti_core.driver.record_parsers import saga_node_from_record
from graphiti_core.errors import NodeNotFoundError
from graphiti_core.models.nodes.node_db_queries import (
    SAGA_NODE_RETURN,
)
from graphiti_core.nodes import SagaNode

logger = logging.getLogger(__name__)


class LadybugSagaNodeOperations(SagaNodeOperations):
    async def save(
        self,
        executor: QueryExecutor,
        node: SagaNode,
        tx: Transaction | None = None,
    ) -> None:
        # Use a basic save query for LadybugDB saga nodes
        query = """
        MERGE (n:Saga {uuid: $uuid})
        SET
            n.name = $name,
            n.group_id = $group_id,
            n.summary = $summary,
            n.name_embedding = $name_embedding,
            n.created_at = $created_at
        """
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
    ) -> SagaNode:
        query = f"""
        MATCH (n:Saga {{uuid: $uuid}})
        RETURN {SAGA_NODE_RETURN}
        """
        params = {'uuid': uuid}
        result = await executor.execute_query(query, params, tx)
        
        if not result:
            raise NodeNotFoundError(f'Saga node with uuid {uuid} not found')
        
        return saga_node_from_record(result[0])

    async def get_by_group_id(
        self,
        executor: QueryExecutor,
        group_id: str,
        tx: Transaction | None = None,
    ) -> list[SagaNode]:
        query = f"""
        MATCH (n:Saga {{group_id: $group_id}})
        RETURN {SAGA_NODE_RETURN}
        ORDER BY n.created_at DESC
        """
        params = {'group_id': group_id}
        result = await executor.execute_query(query, params, tx)
        
        return [saga_node_from_record(record) for record in result]

    async def get_by_name(
        self,
        executor: QueryExecutor,
        name: str,
        tx: Transaction | None = None,
    ) -> list[SagaNode]:
        query = f"""
        MATCH (n:Saga {{name: $name}})
        RETURN {SAGA_NODE_RETURN}
        ORDER BY n.created_at DESC
        """
        params = {'name': name}
        result = await executor.execute_query(query, params, tx)
        
        return [saga_node_from_record(record) for record in result]

    async def delete_by_uuid(
        self,
        executor: QueryExecutor,
        uuid: str,
        tx: Transaction | None = None,
    ) -> None:
        query = """
        MATCH (n:Saga {uuid: $uuid})
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
        MATCH (n:Saga {uuid: $uuid})
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
        MATCH (n:Saga {uuid: $uuid})
        SET n.name_embedding = $name_embedding
        """
        params = {'uuid': uuid, 'name_embedding': name_embedding}
        await executor.execute_query(query, params, tx)
