from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from starlette.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_pool = AsyncConnectionPool(
        conninfo="postgresql://postgres:postgres@db:5432/testdb",
        min_size=1,
        max_size=10,
    )

    await db_pool.open()
    app.state.db_pool = db_pool
    try:
        yield
    finally:
        await db_pool.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db_connection():
    async with app.state.db_pool.connection() as conn:
        yield conn


# TODO! move routes
@app.get("/")
def hello_world():
    return {"Hello": "World1"}

# TODO! return type
@app.get("/global_map")
async def global_map(db: AsyncConnection = Depends(get_db_connection)):
    async with db.cursor() as cursor:
        await cursor.execute("""SELECT * FROM global_map""")
        return await cursor.fetchall()
