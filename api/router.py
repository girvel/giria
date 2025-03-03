from typing import Literal

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection
from pydantic import BaseModel

from db import get_db_connection

router = APIRouter()


@router.get("/")
def hello_world() -> Literal["Hello, world!"]:
    return "Hello, world!"

class WorldTile(BaseModel):
    x: int
    y: int
    tile: Literal["dead", "plain", "forest", "mountain"]

@router.get("/global_map")
async def global_map(db: AsyncConnection = Depends(get_db_connection)) -> list[WorldTile]:
    async with db.cursor() as cursor:
        await cursor.execute("""SELECT * FROM global_map""")
        return [
            WorldTile(x=x, y=y, tile=tile)
            for x, y, tile in await cursor.fetchall()
        ]
