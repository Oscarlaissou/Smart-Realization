import logging
import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db
from ..features.auth.models import User

from .config import settings

# Clé lue dans backend/.env via settings (os.getenv ne voit PAS le .env : la clé par défaut,
# publique car écrite dans le dépôt, était utilisée et permettait de forger des jetons).
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

_CLES_PUBLIQUES = {"sevia_cle_secrete_supabase_2026_fixe", "changez-moi", ""}
if SECRET_KEY in _CLES_PUBLIQUES and os.getenv("SEVIA_TESTS") != "1":
    logging.getLogger(__name__).warning(
        "SECRET_KEY n'est pas définie dans backend/.env : les jetons sont signés avec une clé publique. "
        "Ajouter une valeur secrète longue (ex. python -c \"import secrets; print(secrets.token_urlsafe(48))\")."
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return pwd_context.hash(mot_de_passe)




def verifier_mot_de_passe(mot_de_passe: str, mot_de_passe_hash: str | None) -> bool:
    if not mot_de_passe_hash:
        return False
    try:
        return pwd_context.verify(mot_de_passe, mot_de_passe_hash)
    except Exception:
        return False

def creer_token(user_id: int, email: str) -> str:
    expiration = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton manquant")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton invalide")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")
    return user