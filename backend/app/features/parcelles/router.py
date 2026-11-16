"""CONTRÔLEUR – Exploitations, parcelles, cultures (CRUD)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from .models import Exploitation, Parcelle, Culture
from .schemas import *

router = APIRouter(tags=["Exploitations et parcelles"], dependencies=[Depends(current_user)])

@router.post("/exploitations", response_model=ExploitationOut, status_code=201)
def creer_exploitation(d: ExploitationIn, db: Session = Depends(get_db), user=Depends(current_user)):
    e = Exploitation(**d.model_dump(), user_id=user.id); db.add(e); db.commit(); db.refresh(e); return e

@router.get("/exploitations", response_model=list[ExploitationOut])
def lister_exploitations(db: Session = Depends(get_db), user=Depends(current_user)):
    return db.query(Exploitation).filter_by(user_id=user.id).all()

@router.post("/parcelles", response_model=ParcelleOut, status_code=201)
def creer_parcelle(d: ParcelleIn, db: Session = Depends(get_db)):
    p = Parcelle(**d.model_dump()); db.add(p); db.commit(); db.refresh(p); return p

@router.get("/parcelles", response_model=list[ParcelleOut])
def lister_parcelles(db: Session = Depends(get_db)):
    return db.query(Parcelle).all()

@router.put("/parcelles/{pid}", response_model=ParcelleOut)
def modifier_parcelle(pid: int, d: ParcelleIn, db: Session = Depends(get_db)):
    p = db.get(Parcelle, pid)
    if not p: raise HTTPException(404, "Parcelle introuvable")
    for k, v in d.model_dump().items(): setattr(p, k, v)
    db.commit(); db.refresh(p); return p

@router.delete("/parcelles/{pid}", status_code=204)
def supprimer_parcelle(pid: int, db: Session = Depends(get_db)):
    p = db.get(Parcelle, pid)
    if not p: raise HTTPException(404, "Parcelle introuvable")
    db.delete(p); db.commit()

@router.post("/parcelles/{pid}/cultures", response_model=CultureOut, status_code=201)
def ajouter_culture(pid: int, d: CultureIn, db: Session = Depends(get_db)):
    c = Culture(**d.model_dump(), parcelle_id=pid); db.add(c); db.commit(); db.refresh(c); return c
