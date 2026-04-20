from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from graph_service.config import get_settings
from graph_service.routers import ingest, retrieve
from graph_service.zep_graphiti import initialize_graphiti


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    await initialize_graphiti(settings)
    yield
    # Shutdown
    # No need to close Graphiti here, as it's handled per-request


app = FastAPI(lifespan=lifespan)


app.include_router(retrieve.router)
app.include_router(ingest.router)


@app.get('/healthcheck')
async def healthcheck():
    return JSONResponse(content={'status': 'healthy'}, status_code=200)


@app.get('/threads')
async def thread_monitor():
    """Monitor thread usage for debugging thread leaks"""
    import threading
    import os
    try:
        # Get current thread count
        thread_count = threading.active_count()
        
        # Get process ID and thread list
        pid = os.getpid()
        threads = threading.enumerate()
        
        # Count threads by name pattern
        uvicorn_threads = sum(1 for t in threads if 'uvicorn' in t.name.lower())
        worker_threads = sum(1 for t in threads if 'worker' in t.name.lower())
        async_threads = sum(1 for t in threads if 'asyncio' in t.name.lower() or 'threadpool' in t.name.lower())
        
        return JSONResponse(content={
            'pid': pid,
            'total_threads': thread_count,
            'uvicorn_threads': uvicorn_threads,
            'worker_threads': worker_threads,
            'async_threads': async_threads,
            'thread_names': [t.name for t in threads[:10]]  # First 10 thread names
        }, status_code=200)
    except Exception as e:
        return JSONResponse(content={'error': str(e)}, status_code=500)
