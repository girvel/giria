import logging
import pathlib
import sys
import time
import signal

import psycopg

logging.basicConfig(level=logging.DEBUG)


def initialize(connection: psycopg.Connection):
    already_exists, = connection.execute("""
        SELECT EXISTS(
            SELECT *
            FROM information_schema.tables
            WHERE table_name='world_map'
        );
    """).fetchone()

    if already_exists:
        logging.info("DB already initialized")
        return

    logging.info("Initializing DB")

    # TODO! separate SQL file
    connection.execute("""
        CREATE TABLE tiles (
            tile VARCHAR(8) PRIMARY KEY,
            growth_rate DOUBLE PRECISION NOT NULL,
            gold_rate DOUBLE PRECISION NOT NULL,
            wood_rate DOUBLE PRECISION NOT NULL
        );
        
        INSERT INTO tiles (tile, growth_rate, gold_rate, wood_rate) VALUES
        ('dead', 0.5, 0.5, 0.5),
        ('plain', 2, 1, 1),
        ('forest', 0.8, 0.8, 2),
        ('mountain', 0.8, 2, 0.5);
    
        CREATE TABLE players (
            player_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            login VARCHAR(20) NOT NULL,
            password BYTEA NOT NULL,
            color CHAR(6) NOT NULL,
            gold INTEGER NOT NULL,
            wood INTEGER NOT NULL
        );
        
        INSERT INTO players (login, color, password, gold, wood)
        VALUES
        ('remnants', 'dddddd', '$2b$12$VCMoArsi18YhtdDoJIfE5.J4PeUpJfLOxvJSnw5vB.0MLCDfSXQyi', 0, 0),
        ('girvel', 'dd134b', '$2b$12$D38R.HynTNpRGcsq1lhae.MyOSgVM7tUyfhfLBzbgXrWUQ5k.iRxi', 10, 10);
        
        CREATE TABLE cities (
            city_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            name VARCHAR(20) NOT NULL,
            population INTEGER NOT NULL,
            player_id INTEGER NOT NULL REFERENCES players
        );
        
        INSERT INTO cities (name, population, player_id) VALUES
        ('Aldberg', 100, 1),
        ('Westhall', 150, 1),
        ('Eastwatch', 50, 1),
        ('Ledfolk', 100, 1);
        
        CREATE TABLE world_map (
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            tile VARCHAR(8) NOT NULL REFERENCES tiles,
            city_id INTEGER REFERENCES cities,
            PRIMARY KEY(x, y)
        );
        
        CREATE FUNCTION fmod (
           dividend double precision,
           divisor double precision
        ) RETURNS double precision
            LANGUAGE sql IMMUTABLE AS
        'SELECT dividend - floor(dividend / divisor) * divisor';
        
        CREATE FUNCTION random_round (
            value double precision
        ) RETURNS INTEGER
            LANGUAGE sql IMMUTABLE AS
        'SELECT FLOOR(value) + CASE WHEN RANDOM() < fmod(value, 1) THEN 1 ELSE 0 END';
    """)

    TILE_TYPES = {
        ".": "dead",
        "-": "plain",
        "f": "forest",
        "^": "mountain",
    }

    for y, line in enumerate(pathlib.Path("map.txt").read_text().splitlines()):
        for x, character in enumerate(line):
            connection.execute(
                "INSERT INTO world_map (x, y, tile) VALUES (%s, %s, %s)",
                (x, y, TILE_TYPES[character])
            )

    connection.execute("""
        UPDATE world_map
        SET city_id = 1
        WHERE x = 1 AND y = 1;
        
        UPDATE world_map
        SET city_id = 2
        WHERE x = 18 AND y = 2;
        
        UPDATE world_map
        SET city_id = 3
        WHERE x = 2 AND y = 7;
        
        UPDATE world_map
        SET city_id = 4
        WHERE x = 11 AND y = 5;
    """)

    connection.commit()

    logging.info("Initialized DB")


def update(connection: psycopg.Connection):
    # TODO! remove subquery from the first query
    connection.execute("""
        UPDATE cities
        SET population = random_round(float_value)
        FROM (
            SELECT
                LEAST(1000, population * (1 + 0.00064 * growth_rate)) AS float_value,
                cities.city_id AS city_id
            FROM cities
            LEFT JOIN world_map ON world_map.city_id = cities.city_id
            LEFT JOIN tiles ON world_map.tile = tiles.tile
        ) AS new_population
        WHERE new_population.city_id = cities.city_id;
        
        UPDATE players
        SET
            gold = random_round(gold + gold_rate_total),
            wood = random_round(wood + wood_rate_total)
        FROM (
            SELECT SUM(gold_rate) AS gold_rate_total,
                   SUM(wood_rate) AS wood_rate_total,
                   player_id
            FROM cities
            JOIN world_map ON cities.city_id = world_map.city_id
            JOIN tiles ON world_map.tile = tiles.tile
            GROUP BY player_id
        ) AS subquery
        WHERE players.player_id = subquery.player_id;
    """)

    connection.commit()


if __name__ == '__main__':
    with psycopg.connect(
        dbname="giria",
        user="postgres",
        password="postgres",
        host="db",
        port=5432,
    ) as conn:
        logging.info("Connected to DB")
        db_version, = conn.execute("SELECT version();").fetchone()
        logging.info(f"{db_version = }")

        initialize(conn)

        logging.info("Starting game loop")

        def terminate(signum, frame):
            logging.info(f"Received signal {signum}, shutting down gracefully...")
            sys.exit(0)

        signal.signal(signal.SIGTERM, terminate)
        signal.signal(signal.SIGINT, terminate)

        while True:
            t = time.time()
            update(conn)
            t = time.time() - t

            time.sleep(max(0, 1 - t))
