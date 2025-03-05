from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncCursor
from pydantic import BaseModel

from . import security
from .dependencies.db import cursor
from .dependencies.auth import login

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
async def world_map(db: AsyncCursor = Depends(cursor)) -> list[WorldTile]:
    await db.execute("""
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
        for x, y, tile, city_name, login, population in await db.fetchall()
    ]

class LoginPair(BaseModel):
    login: str
    password: str

class LoginResponse(BaseModel):
    token: str
    token_type: Literal["bearer"]

@router.post("/login")
async def login_(login_pair: LoginPair, db: AsyncCursor = Depends(cursor)) -> LoginResponse:
    await db.execute("""
        SELECT password FROM players
        WHERE login = %s
    """, (login_pair.login, ))

    password_hash, = await db.fetchone()
    if not security.verify_password(login_pair.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )

    return LoginResponse(
        token=security.create_access_token(login_pair.model_dump()),
        token_type="bearer",
    )

class SettleBody(BaseModel):
    x: int
    y: int
    city_name: str

@router.post("/settle")
async def settle(body: SettleBody, db: AsyncCursor = Depends(cursor), user: str = Depends(login)):
    await db.execute("""
        SELECT city_id FROM world_map
        WHERE x = %s AND y = %s;
    """, (body.x, body.y))

    if (await db.fetchone())[0] is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Position occupied",
        )

    await db.execute("""
        SELECT EXISTS(
            SELECT * FROM cities
            LEFT JOIN players ON cities.player_id = players.player_id
            WHERE login = %s
        );
    """, (user, ))

    if (await db.fetchone())[0]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player already settled",
        )

    await db.execute("""
        INSERT INTO cities (name, population, player_id)
        SELECT %s AS name, 100 AS population, player_id
        FROM players
        WHERE login = %s
        RETURNING city_id
    """, (body.city_name, user, ))

    city_id, = await db.fetchone()  # TODO! try joining queries

    await db.execute("""
        UPDATE world_map
        SET city_id = %s
        WHERE x = %s AND y = %s
    """, (city_id, body.x, body.y))
