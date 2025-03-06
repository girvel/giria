from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Response
from psycopg import AsyncCursor
from pydantic import BaseModel

from . import security
from .dependencies.db import cursor
from .dependencies.auth import login, LoginData

router = APIRouter()


@router.get("/")
def hello_world() -> Literal["Hello, world!"]:
    return "Hello, world!"

class City(BaseModel):
    city_name: str
    player_login: str
    player_color: str
    population: int

class WorldTile(BaseModel):
    x: int
    y: int
    tile: Literal["dead", "plain", "forest", "mountain"]
    city: City | None

@router.get("/world_map")
async def world_map(db: AsyncCursor = Depends(cursor)) -> list[WorldTile]:
    await db.execute("""
        SELECT x, y, tile, name, login, color, population
        FROM world_map
        LEFT JOIN cities ON world_map.city_id = cities.city_id
        LEFT JOIN players ON cities.player_id = players.player_id
    """)

    return [
        WorldTile(
            x=x, y=y, tile=tile,
            city=city_name and City(city_name=city_name, player_login=login, player_color=color, population=population)
        )
        for x, y, tile, city_name, login, color, population in await db.fetchall()
    ]

class LoginPair(BaseModel):
    login: str
    password: str

@router.post("/login")
async def login_(response: Response, login_pair: LoginPair, db: AsyncCursor = Depends(cursor)):
    await db.execute("""
        SELECT password, player_id FROM players
        WHERE login = %s
    """, (login_pair.login, ))

    entry = await db.fetchone()
    if not entry or not security.verify_password(login_pair.password, entry[0]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials",
        )

    response.set_cookie(
        key="jwt",
        value=security.create_access_token({"login": login_pair.login, "id": entry[1]}),
        httponly=True,
        # secure=True,  # TODO https
        samesite="lax",
        max_age=security.TOKEN_LIFETIME_SEC
    )

class PlayerInfo(BaseModel):
    login: str
    settled: bool

@router.get("/player_info")
async def player_info(db: AsyncCursor = Depends(cursor), user: LoginData = Depends(login)) -> PlayerInfo:
    await db.execute("""
        SELECT EXISTS(
            SELECT city_id FROM cities
            WHERE player_id = %s
        );
    """, (user.id, ))

    settled, = await db.fetchone()

    return PlayerInfo(login=user.login, settled=settled)


class SettleBody(BaseModel):
    x: int
    y: int
    city_name: str

@router.post("/settle")
async def settle(body: SettleBody, db: AsyncCursor = Depends(cursor), user: LoginData = Depends(login)):
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
            WHERE player_id = %s
        );
    """, (user.id, ))

    if (await db.fetchone())[0]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player already settled",
        )

    await db.execute("""
        INSERT INTO cities (name, population, player_id)
        VALUES (%s, 100, %s)
        RETURNING city_id;
    """, (body.city_name, user.id))

    city_id, = await db.fetchone()  # TODO! try joining queries

    await db.execute("""
        UPDATE world_map
        SET city_id = %s
        WHERE x = %s AND y = %s
    """, (city_id, body.x, body.y))
