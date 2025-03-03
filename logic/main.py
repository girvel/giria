import pathlib

import psycopg


if __name__ == '__main__':
    with psycopg.connect(
        dbname="testdb",
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
                WHERE table_name='global_map'
            )
        """).fetchone()[0]

        if not already_exists:
            conn.execute("""
                CREATE TABLE global_map (
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    tile VARCHAR(8)
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
                        "INSERT INTO global_map (x, y, tile) VALUES (%s, %s, %s)",
                        (x, y, TILE_TYPES[character])
                    )

            print("Initialized DB")

        print(conn.execute("SELECT tile FROM global_map WHERE x = 2 AND y = 1").fetchone())
