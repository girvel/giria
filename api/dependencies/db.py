from contextlib import asynccontextmanager

from fastapi import Request, FastAPI
from psycopg_pool import AsyncConnectionPool


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_pool = AsyncConnectionPool(
        conninfo="postgresql://postgres:postgres@db:5432/giria",
        min_size=1,
        max_size=10,
        open=False,
    )

    await db_pool.open()
    app.state.db_pool = db_pool
    try:
        yield
    finally:
        await db_pool.close()

async def cursor(request: Request):
    async with request.app.state.db_pool.connection() as conn:
        async with conn.cursor() as result:
            yield result
        conn.commit()
