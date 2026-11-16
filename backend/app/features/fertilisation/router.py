"""CONTRÔLEUR – Fertilisation (données agronomiques, doses, apports, calendrier)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from .models import DonneeAgro, Apport
from .schemas import *
from . import service as dose_service

router = APIRouter(prefix="/fertilisation", tags=["Fertilisation"], dependencies=[Depends(current_user)])

@router.post("/donnees", response_model=DonneeAgroOut, status_code=201)
def saisir_donnees(d: DonneeAgroIn, db: Session = Depends(get_db)):
    x = DonneeAgro(**d.model_dump()); db.add(x); db.commit(); db.refresh(x); return x

@router.get("/dose/{pid}")
def dose_recommandee(pid: int, db: Session = Depends(get_db)):
    x = db.query(DonneeAgro).filter_by(parcelle_id=pid).order_by(DonneeAgro.id.desc()).first()
    if not x: return {"message": "Aucune donnée agronomique"}
    return dose_service.recommander(x.azote, x.phosphore, x.potassium)

@router.post("/apports", response_model=ApportOut, status_code=201)
def enregistrer_apport(d: ApportIn, db: Session = Depends(get_db)):
    from datetime import datetime
    data = d.model_dump(); data["date"] = data["date"] or datetime.utcnow()
    a = Apport(**data); db.add(a); db.commit(); db.refresh(a); return a

@router.get("/apports", response_model=list[ApportOut])
def calendrier(db: Session = Depends(get_db)):
    return db.query(Apport).order_by(Apport.date).all()
