from contextlib import asynccontextmanager
from typing import TypeAlias, Annotated

import asyncpg
from fastapi import Request, FastAPI, Depends


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with asyncpg.create_pool(
        host="db",
        database="giria",
        user="postgres",
        password="postgres",
        min_size=1,
        max_size=10,
    ) as pool:
        yield {"db_pool": pool}


async def get_pg_transaction(request: Request) -> asyncpg.Connection:
    async with request.state.db_pool.acquire() as conn:
        async with conn.transaction():
            yield conn

PgConnection: TypeAlias = Annotated[asyncpg.Connection, Depends(get_pg_transaction)]
