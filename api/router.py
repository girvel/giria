from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel

from . import security
from .dependencies.db import PgConnection
from .dependencies.auth import login, LoginData

router = APIRouter()


@router.get("/")
def hello_world() -> Literal["Hello, world!"]:
    return "Hello, world!"

class City(BaseModel):
    city_id: int
    city_name: str
    player_login: str
    player_color: str
    population: int

class Army(BaseModel):
    owner: str
    size: int
    color: str

class WorldTile(BaseModel):
    x: int
    y: int
    tile: Literal["dead", "plain", "forest", "mountain"]
    configuration: int
    city: City | None
    army: Army | None

@router.get("/world_map")
async def world_map(db: PgConnection) -> list[WorldTile]:
    return [
        WorldTile(
            x=x, y=y, tile=tile, configuration=configuration,
            city=city_name and City(
                city_id=city_id, city_name=city_name,
                player_login=player_login, player_color=color, population=population
            ),
            army=army_owner and Army(owner=army_owner, color=army_color, size=army_size)
        )
        for x, y, tile, configuration,
            city_id, city_name, player_login, color, population,
            army_owner, army_color, army_size
        in await db.fetch("""
            SELECT
                x, y, tile, configuration,
                cities.city_id, name, owner.login, owner.color, population,
                army_owner.login, army_owner.color, army_size
            FROM world_map
            LEFT JOIN cities ON world_map.city_id = cities.city_id
            LEFT JOIN players owner ON cities.player_id = owner.player_id
            LEFT JOIN armies ON world_map.army_id = armies.army_id
            LEFT JOIN players army_owner ON armies.player_id = army_owner.player_id
        """)
    ]

class LoginPair(BaseModel):
    login: str
    password: str

@router.post("/login")
async def login_(response: Response, login_pair: LoginPair, db: PgConnection):
    entry = await db.fetchrow("""
        SELECT password, player_id FROM players
        WHERE login = $1
    """, login_pair.login)

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

# TODO join with login?
@router.get("/player_info")
async def player_info(db: PgConnection, user: LoginData = Depends(login)) -> PlayerInfo:
    settled = await db.fetchval("""
        SELECT EXISTS(
            SELECT city_id FROM cities
            WHERE player_id = $1
        );
    """, user.id)

    return PlayerInfo(login=user.login, settled=settled)


class SettleBody(BaseModel):
    x: int
    y: int
    city_name: str

@router.post("/settle")
async def settle(body: SettleBody, db: PgConnection, user: LoginData = Depends(login)):
    city_id = await db.fetchval("""
        SELECT city_id FROM world_map
        WHERE x = $1 AND y = $2;
    """, body.x, body.y)

    if city_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Position occupied",
        )

    has_player_settled = await db.fetchval("""
        SELECT EXISTS(
            SELECT * FROM cities
            WHERE player_id = $1
        );
    """, user.id)

    if has_player_settled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Player already settled",
        )

    city_id = await db.fetchval("""
        INSERT INTO cities (name, population, player_id)
        VALUES ($1, 100, $2)
        RETURNING city_id;
    """, body.city_name, user.id)  # TODO! try joining queries

    await db.execute("""
        UPDATE world_map
        SET city_id = $1
        WHERE x = $2 AND y = $3
    """, city_id, body.x, body.y)


class Resources(BaseModel):
    gold: int
    wood: int

@router.get("/resources")
async def resources(db: PgConnection, user: LoginData = Depends(login)):
    gold, wood = await db.fetchrow("""
        SELECT gold, wood
        FROM players
        WHERE player_id = $1
    """, user.id)

    return Resources(gold=gold, wood=wood)


class HireSoldiersBody(BaseModel):
    city_id: int

@router.post("/hire_soldier")
async def hire_soldier(body: HireSoldiersBody, db: PgConnection, user: LoginData = Depends(login)):
    population = await db.fetchval("""
        SELECT population
        FROM cities
        WHERE city_id = $1 AND player_id = $2
    """, body.city_id, user.id)

    if not population:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"There is no city #{body.city_id} belonging to a player #{user.id}",
        )

    gold = await db.fetchval("""
        SELECT gold
        FROM players
        WHERE player_id = $1
    """, user.id)

    if gold < 10 or population < 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Not enough gold or population to hire a soldier",
        )

    await db.execute("""
        UPDATE players
        SET gold = gold - 10
        WHERE player_id = $1;
    """, user.id)

    await db.execute("""
        UPDATE cities
        SET population = population - 1
        WHERE city_id = $2;
    """, body.city_id)

    army_id = await db.fetchval("""
        SELECT army_id
        FROM world_map
        WHERE city_id = $1;
    """, body.city_id)

    if army_id is None:
        print("No army")

        army_id = await db.fetchval("""
            INSERT INTO armies (player_id, army_size) VALUES ($1, 1) RETURNING army_id;
        """, user.id)

        await db.execute("""
            UPDATE world_map
            SET army_id = $1
            WHERE city_id = $2
        """, army_id, body.city_id)
    else:
        print("Yes army")

        await db.execute("""
            UPDATE armies
            SET army_size = army_size + 1
            WHERE army_id = $1
        """, army_id)
