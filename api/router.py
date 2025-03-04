from typing import Literal

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection
from pydantic import BaseModel

import security
from db import get_db_connection

router = APIRouter()


@router.get("/")
def hello_world() -> Literal["Hello, world!"]:
    return "Hello, world!"

class City(BaseModel):
    city_name: str
    player_login: str
    population: int

class WorldTile(BaseModel):
    x: int
    y: int
    tile: Literal["dead", "plain", "forest", "mountain"]
    city: City | None

@router.get("/world_map")
async def world_map(db: AsyncConnection = Depends(get_db_connection)) -> list[WorldTile]:
    async with db.cursor() as cursor:
        await cursor.execute("""
            SELECT x, y, tile, name, login, population
            FROM world_map
            LEFT JOIN cities ON world_map.city_id = cities.city_id
            LEFT JOIN players ON cities.player_id = players.player_id
        """)

        return [
            WorldTile(
                x=x, y=y, tile=tile,
                city=city_name and City(city_name=city_name, player_login=login, population=population)
            )
            for x, y, tile, city_name, login, population in await cursor.fetchall()
        ]

class LoginPair(BaseModel):
    login: str
    password: str

@router.post("/login")
async def login(login_pair: LoginPair, db: AsyncConnection = Depends(get_db_connection)) -> bool:
    async with db.cursor() as cursor:
        await cursor.execute("""
            SELECT password FROM players
            WHERE login = %s
        """, (login_pair.login, ))

        password_hash, = await cursor.fetchone()
        return security.verify_password(login_pair.password, password_hash)
