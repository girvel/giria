from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from .. import security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class LoginData(BaseModel):
    login: str
    id: int

async def login(request: Request) -> LoginData:
    token = request.cookies.get("jwt")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No JWT token in cookies; unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload, err = security.verify_access_token(token)
    match err:
        case None:
            return LoginData(**payload)
        case security.TokenIssue.expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expired token",
            )
        case security.TokenIssue.invalid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token",
            )
        case _:
            assert False, "unreachable"
