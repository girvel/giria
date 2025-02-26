import psycopg


if __name__ == '__main__':
    conn = psycopg.connect(
        dbname="testdb",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432,
    )
    print("Connected")

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"{db_version = }")

    conn.close()
