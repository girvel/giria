from datetime import datetime, timedelta

import bcrypt
from jose import jwt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

def create_access_token(data: dict) -> str:
    return jwt.encode(
        data | {"exp": datetime.utcnow() + timedelta(minutes=60)},
        "no-secret",  # TODO! secret key
        algorithm="HS256",
    )
