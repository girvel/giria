from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from .. import security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def login(request: Request) -> str:
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
            return payload["login"]
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
