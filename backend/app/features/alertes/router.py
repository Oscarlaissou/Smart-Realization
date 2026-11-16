"""CONTRÔLEUR – Alertes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from .models import Alerte
from .schemas import AlerteOut

router = APIRouter(prefix="/alertes", tags=["Alertes"], dependencies=[Depends(current_user)])

@router.get("", response_model=list[AlerteOut])
def lister(db: Session = Depends(get_db)):
    return db.query(Alerte).order_by(Alerte.date.desc()).limit(100).all()

@router.post("/{aid}/lue", response_model=AlerteOut)
def marquer_lue(aid: int, db: Session = Depends(get_db)):
    a = db.get(Alerte, aid); a.lue = True; db.commit(); db.refresh(a); return a
