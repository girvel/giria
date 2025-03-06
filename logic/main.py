import logging
import pathlib
import sys
import time
import signal

import psycopg

logging.basicConfig(level=logging.INFO)


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

    connection.execute("""
        CREATE TABLE players (
            player_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            login VARCHAR(20) NOT NULL,
            password BYTEA NOT NULL,
            color CHAR(6) NOT NULL
        );
        
        INSERT INTO players (login, color, password)
        VALUES
        ('remnants', 'dddddd', '$2b$12$VCMoArsi18YhtdDoJIfE5.J4PeUpJfLOxvJSnw5vB.0MLCDfSXQyi'),
        ('girvel', 'dd134b', '$2b$12$D38R.HynTNpRGcsq1lhae.MyOSgVM7tUyfhfLBzbgXrWUQ5k.iRxi');
        
        CREATE TABLE cities (
            city_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
            name VARCHAR(20),
            population INTEGER NOT NULL,
            player_id INTEGER REFERENCES players
        );
        
        INSERT INTO cities (name, population, player_id)
        VALUES ('Aldberg', 500, 1);
        
        CREATE TABLE world_map (
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            tile VARCHAR(8),
            city_id INTEGER REFERENCES cities,
            PRIMARY KEY(x, y)
        );
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
    """)

    connection.commit()

    logging.info("Initialized DB")


def update(connection: psycopg.Connection):
    connection.execute("""
        UPDATE cities
        SET population = CEIL(float_value) + CASE
            WHEN random() < MOD(float_value, 1) THEN 1
            ELSE 0
        END
        FROM (
            SELECT LEAST(1000, population * 1.00064) AS float_value, city_id
            FROM cities
        ) AS new_population
        WHERE new_population.city_id = cities.city_id;
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
