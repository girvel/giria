from datetime import datetime, timedelta
from enum import Enum

import bcrypt
from jose import jwt, JWTError, ExpiredSignatureError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

SECRET_KEY = "no-secret"
ALGORITHM = "HS256"
TOKEN_LIFETIME_SEC = 3600 * 24

def create_access_token(data: dict) -> str:
    return jwt.encode(
        data | {"exp": datetime.utcnow() + timedelta(seconds=TOKEN_LIFETIME_SEC)},
        SECRET_KEY,  # TODO! secret key
        algorithm=ALGORITHM,
    )

class TokenIssue(Enum):
    invalid = 0
    expired = 1

def verify_access_token(token: str) -> tuple[dict, None] | tuple[None, TokenIssue]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]), None
    except ExpiredSignatureError:
        return None, TokenIssue.expired
    except JWTError:
        return None, TokenIssue.invalid
