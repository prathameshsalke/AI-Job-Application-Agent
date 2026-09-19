from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User

pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer = HTTPBearer()

def hash_password(value: str) -> str:
    return pwd.hash(value)

def verify_password(value: str, hashed: str) -> bool:
    return pwd.verify(value, hashed)

def token_for(email: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": email, "exp": exp}, settings.secret_key, algorithm="HS256")

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=["HS256"])
        email = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(401, "Invalid or expired token") from exc
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(401, "User not found")
    return user
