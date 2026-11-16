"""CONTRÔLEUR – Capteurs, électrovannes, caméras, associés à une parcelle."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from .models import Equipement
from .schemas import EquipementIn, EquipementOut

router = APIRouter(prefix="/equipements", tags=["Équipements"], dependencies=[Depends(current_user)])

@router.get("", response_model=list[EquipementOut])
def lister(db: Session = Depends(get_db)):
    return db.query(Equipement).all()

@router.post("", response_model=EquipementOut, status_code=201)
def ajouter(d: EquipementIn, db: Session = Depends(get_db)):
    e = Equipement(**d.model_dump()); db.add(e); db.commit(); db.refresh(e); return e

@router.put("/{eid}", response_model=EquipementOut)
def modifier(eid: int, d: EquipementIn, db: Session = Depends(get_db)):
    e = db.get(Equipement, eid)
    if not e: raise HTTPException(404, "Équipement introuvable")
    for k, v in d.model_dump().items(): setattr(e, k, v)
    db.commit(); db.refresh(e); return e

@router.delete("/{eid}", status_code=204)
def supprimer(eid: int, db: Session = Depends(get_db)):
    e = db.get(Equipement, eid)
    if e: db.delete(e); db.commit()
