"""
Minimal JWT verification for sovd-api's write endpoints.

This is deliberately simple: a single shared secret, no user database,
no roles. It exists to demonstrate the *pattern* (write operations must
be authenticated, read operations don't have to be) rather than a full
production auth system — a real deployment would use the same AWS IoT
Core device identity / API Gateway authorizer pattern named in the
project spec, not a hardcoded secret.
"""

import os
from fastapi import Header, HTTPException
from jose import JWTError, jwt

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-secret-change-in-real-deployment")
JWT_ALGORITHM = "HS256"


def require_auth(authorization: str = Header(None)):
    """
    FastAPI dependency: raises 401 if the Authorization header is
    missing or the token is invalid. Use on any endpoint that changes
    state (writes), not on read-only endpoints.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")