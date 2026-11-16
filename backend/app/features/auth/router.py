"""CONTRÔLEUR – Authentification (user stories 4.1.1)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import hash_password, verify_password, create_token, current_user
from .models import User
from .schemas import UserCreate, UserOut, Token

router = APIRouter(prefix="/auth", tags=["Authentification"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(409, "E-mail déjà utilisé")
    u = User(nom=data.nom, email=data.email, mot_de_passe=hash_password(data.mot_de_passe))
    db.add(u); db.commit(); db.refresh(u)
    return u

@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=form.username).first()
    if not u or not verify_password(form.password, u.mot_de_passe):
        raise HTTPException(401, "Identifiants incorrects")
    return Token(access_token=create_token(u.id))

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
