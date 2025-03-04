from typing import Literal

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection
from pydantic import BaseModel

from db import get_db_connection

router = APIRouter()


@router.get("/")
def hello_world() -> Literal["Hello, world!"]:
    return "Hello, world!"

class City(BaseModel):
    city_id: int
    player_login: str
    population: int

class WorldTile(BaseModel):
    x: int
    y: int
    tile: Literal["dead", "plain", "forest", "mountain"]
    city: City | None

@router.get("/global_map")
async def global_map(db: AsyncConnection = Depends(get_db_connection)) -> list[WorldTile]:
    async with db.cursor() as cursor:
        await cursor.execute("""
            SELECT x, y, tile, global_map.city_id, login, population
            FROM global_map
            LEFT JOIN cities ON global_map.city_id = cities.city_id
            LEFT JOIN players ON cities.player_id = players.player_id
        """)

        return [
            WorldTile(
                x=x, y=y, tile=tile,
                city=city_id and City(city_id=city_id, player_login=login, population=population)
            )
            for x, y, tile, city_id, login, population in await cursor.fetchall()
        ]
