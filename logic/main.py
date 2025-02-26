import psycopg


if __name__ == '__main__':
    with psycopg.connect(
        dbname="testdb",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
    ) as conn:
        print("Connected")

        db_version, = conn.execute("SELECT version();").fetchone()
        print(f"{db_version = }")

        already_exists = conn.execute("""
            SELECT EXISTS(
                SELECT *
                FROM information_schema.tables
                WHERE table_name='users'
            )
        """).fetchone()[0]

        if not already_exists:
            conn.execute("""
                CREATE TABLE users (
                    user_id SERIAL PRIMARY KEY,
                    name varchar(255)
                );
            """)

        conn.execute("INSERT INTO users (name) VALUES (%s)", ("Demo Demoviev", ))
        print(conn.execute("SELECT user_id, name FROM users").fetchall())
