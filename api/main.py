from fastapi import FastAPI
import psycopg
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
