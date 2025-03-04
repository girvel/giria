import pathlib

import psycopg


if __name__ == '__main__':
    with psycopg.connect(
        dbname="giria",
        user="postgres",
        password="postgres",
        host="db",
        port=5432,
    ) as conn:
        print("Connected")

        db_version, = conn.execute("SELECT version();").fetchone()
        print(f"{db_version = }")

        already_exists = conn.execute("""
            SELECT EXISTS(
                SELECT *
                FROM information_schema.tables
                WHERE table_name='world_map'
            )
        """).fetchone()[0]

        if not already_exists:
            conn.execute("""
                CREATE TABLE players (
                    player_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    login VARCHAR(20) NOT NULL,
                    password BYTEA NOT NULL,
                    color CHAR(6) NOT NULL
                );
                
                INSERT INTO players (login, color, password)
                VALUES ('remnants', 'dddddd', '$2b$12$VCMoArsi18YhtdDoJIfE5.J4PeUpJfLOxvJSnw5vB.0MLCDfSXQyi');
                
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
                    conn.execute(
                        "INSERT INTO world_map (x, y, tile) VALUES (%s, %s, %s)",
                        (x, y, TILE_TYPES[character])
                    )

            conn.execute("""
                UPDATE world_map
                SET city_id = 1
                WHERE x = 1 AND y = 1;
            """)


            print("Initialized DB")

        print(conn.execute("SELECT tile FROM world_map WHERE x = 2 AND y = 1").fetchone())
