from fastapi import FastAPI
import psycopg

app = FastAPI()
db = psycopg.Connection.connect(
    dbname="testdb",
    user="postgres",
    password="postgres",
    host="db",
    port=5432,
)


@app.get("/")
def hello_world():
    return {"Hello": "World1"}

# TODO! async
# TODO! return type
@app.get("/global_map")
def global_map():
    with db.cursor() as cursor:
        return cursor.execute("""SELECT * FROM global_map""").fetchall()
