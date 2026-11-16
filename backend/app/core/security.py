import hashlib, hmac, os, time
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(p: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", p.encode(), salt, 200_000)
    return salt.hex() + "$" + h.hex()

def verify_password(p: str, stored: str) -> bool:
    salt, h = stored.split("$")
    c = hashlib.pbkdf2_hmac("sha256", p.encode(), bytes.fromhex(salt), 200_000)
    return hmac.compare_digest(c.hex(), h)

def create_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id), "exp": time.time() + 3600 * 8}, settings.SECRET_KEY, algorithm="HS256")

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    from ..features.auth.models import User
    try:
        uid = int(jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Jeton invalide")
    u = db.get(User, uid)
    if not u:
        raise HTTPException(401, "Utilisateur introuvable")
    return u
