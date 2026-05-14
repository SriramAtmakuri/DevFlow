import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database.engine import engine
from database.models import metadata

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "devflow-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def _blocklist_key(token: str) -> str:
    return f"devflow:blocked:{hashlib.sha256(token.encode()).hexdigest()[:32]}"


def revoke_token(token: str) -> bool:
    from cache.redis_cache import get_redis
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = int(payload.get("exp", 0))
        ttl = max(exp - int(datetime.utcnow().timestamp()), 1)
        r = get_redis()
        if r:
            r.setex(_blocklist_key(token), ttl, "1")
        return True
    except Exception:
        return False


def _is_revoked(token: str) -> bool:
    from cache.redis_cache import get_redis
    r = get_redis()
    if not r:
        return False
    try:
        return bool(r.exists(_blocklist_key(token)))
    except Exception:
        return False


def init_users_table():
    metadata.create_all(engine)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Optional[dict]:
    if not credentials:
        return None
    token = credentials.credentials
    if _is_revoked(token):
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": int(user_id), "username": payload.get("username")}
    except JWTError:
        return None


def require_auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    user = get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def register_user(email: str, username: str, password: str) -> dict:
    hashed = pwd_context.hash(password)
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("INSERT INTO users (email, username, hashed_password) VALUES (:email, :username, :hashed) RETURNING id"),
                {"email": email, "username": username, "hashed": hashed},
            )
            user_id = result.scalar()
        return {"id": user_id, "email": email, "username": username}
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Email or username already exists")


def authenticate_user(email: str, password: str) -> dict:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE email=:email"), {"email": email})
        row = result.fetchone()
    if not row or not pwd_context.verify(password, row._mapping["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    m = row._mapping
    return {"id": m["id"], "email": m["email"], "username": m["username"]}
