import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .settings import settings
#sec

bearer = HTTPBearer(auto_error=True)

def current_customer(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        return jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=['HS256'], issuer='oficina-auth')
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail='Token inválido ou expirado') from exc
