import logging
import pathlib
import random
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

    connection.execute(pathlib.Path("sql/create.sql").read_text())

    TILE_TYPES = {
        ".": "dead",
        "-": "plain",
        "f": "forest",
        "^": "mountain",
    }

    for y, line in enumerate(pathlib.Path("map.txt").read_text().splitlines()):
        for x, character in enumerate(line):
            connection.execute(
                "INSERT INTO world_map (x, y, tile, configuration) VALUES (%s, %s, %s, %s)",
                (x, y, TILE_TYPES[character], random.randint(0, 4))
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


update_code = pathlib.Path("sql/update.sql").read_text()

def update(connection: psycopg.Connection):
    # TODO! remove subquery from the first query
    connection.execute(update_code)
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
