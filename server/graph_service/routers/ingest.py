import asyncio
from contextlib import asynccontextmanager
from functools import partial

from fastapi import APIRouter, FastAPI, status
from graphiti_core.nodes import EpisodeType  # type: ignore
from graphiti_core.utils.maintenance.graph_data_operations import clear_data  # type: ignore

from graph_service.dto import AddEntityNodeRequest, AddMessagesRequest, Message, Result
from graph_service.zep_graphiti import ZepGraphitiDep


class AsyncWorker:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.task = None
        self._shutdown_event = asyncio.Event()

    async def worker(self):
        while not self._shutdown_event.is_set():
            try:
                # Use wait_for to prevent hanging indefinitely
                job = await asyncio.wait_for(
                    self.queue.get(), 
                    timeout=1.0  # Check shutdown event every second
                )
                try:
                    print(f'Got a job: (size of remaining queue: {self.queue.qsize()})')
                    await asyncio.wait_for(job(), timeout=30.0)  # 30 second timeout per job
                except asyncio.TimeoutError:
                    print(f'Job timed out, skipping')
                except Exception as e:
                    print(f'Job failed with error: {e}')
                finally:
                    self.queue.task_done()
            except asyncio.TimeoutError:
                # Timeout is expected for shutdown checking
                continue
            except asyncio.CancelledError:
                print('Worker task cancelled')
                break
            except Exception as e:
                print(f'Worker error: {e}')
                continue

    async def start(self):
        if self.task is None or self.task.done():
            self._shutdown_event.clear()
            self.task = asyncio.create_task(self.worker())

    async def stop(self):
        """Graceful shutdown with timeout"""
        if self.task and not self.task.done():
            print('Stopping AsyncWorker...')
            self._shutdown_event.set()
            
            # Cancel the task if it doesn't finish gracefully
            try:
                await asyncio.wait_for(self.task, timeout=5.0)
            except asyncio.TimeoutError:
                print('Worker did not shutdown gracefully, cancelling...')
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    print('Worker task cancelled successfully')
            
            # Clear remaining queue items
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            print('AsyncWorker stopped')


async_worker = AsyncWorker()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await async_worker.start()
    yield
    await async_worker.stop()


router = APIRouter(lifespan=lifespan)


@router.post('/messages', status_code=status.HTTP_202_ACCEPTED)
async def add_messages(
    request: AddMessagesRequest,
    graphiti: ZepGraphitiDep,
):
    async def add_messages_task(m: Message):
        await graphiti.add_episode(
            uuid=m.uuid,
            group_id=request.group_id,
            name=m.name,
            episode_body=f'{m.role or ""}({m.role_type}): {m.content}',
            reference_time=m.timestamp,
            source=EpisodeType.message,
            source_description=m.source_description,
        )

    for m in request.messages:
        await async_worker.queue.put(partial(add_messages_task, m))

    return Result(message='Messages added to processing queue', success=True)


@router.post('/entity-node', status_code=status.HTTP_201_CREATED)
async def add_entity_node(
    request: AddEntityNodeRequest,
    graphiti: ZepGraphitiDep,
):
    node = await graphiti.save_entity_node(
        uuid=request.uuid,
        group_id=request.group_id,
        name=request.name,
        summary=request.summary,
    )
    return node


@router.delete('/entity-edge/{uuid}', status_code=status.HTTP_200_OK)
async def delete_entity_edge(uuid: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_entity_edge(uuid)
    return Result(message='Entity Edge deleted', success=True)


@router.delete('/group/{group_id}', status_code=status.HTTP_200_OK)
async def delete_group(group_id: str, graphiti: ZepGraphitiDep):
    if group_id != graphiti.driver.db:
        await graphiti.delete_group(group_id)
        return Result(message='Group deleted', success=True)
    else:
        return Result(message='Cannot delete default database', success=False)


@router.delete('/episode/{uuid}', status_code=status.HTTP_200_OK)
async def delete_episode(uuid: str, graphiti: ZepGraphitiDep):
    await graphiti.delete_episodic_node(uuid)
    return Result(message='Episode deleted', success=True)


@router.post('/clear', status_code=status.HTTP_200_OK)
async def clear(
    graphiti: ZepGraphitiDep,
):
    await clear_data(graphiti.driver)
    await graphiti.build_indices_and_constraints()
    return Result(message='Graph cleared', success=True)
