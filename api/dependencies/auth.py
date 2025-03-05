from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .. import security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def login(token: str = Depends(oauth2_scheme)) -> str:
    payload, err = security.verify_access_token(token)
    match err:
        case None:
            return payload["login"]
        case security.TokenIssue.expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        case security.TokenIssue.invalid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        case _:
            assert False, "unreachable"
