"""CONTRÔLEUR – Humidité et irrigation (mesures, cycles, journal)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from .models import Mesure, CycleIrrigation, Irrigation
from ..parcelles.models import Parcelle
from .schemas import *
from ..alertes import service as alerte_service
from . import service as irrigation_service

router = APIRouter(prefix="/humidite", tags=["Humidité et irrigation"])

# Utilisé par les capteurs (ou les tests) : pas d'authentification utilisateur.
@router.post("/mesures", response_model=MesureOut, status_code=201)
def recevoir_mesure(d: MesureIn, db: Session = Depends(get_db)):
    p = db.get(Parcelle, d.parcelle_id)
    if not p: raise HTTPException(404, "Parcelle introuvable")
    m = Mesure(**d.model_dump()); db.add(m); db.commit(); db.refresh(m)
    alerte_service.verifier_humidite(db, p, d.humidite)
    return m

@router.get("/mesures/{pid}", response_model=list[MesureOut], dependencies=[Depends(current_user)])
def historique(pid: int, limite: int = 100, db: Session = Depends(get_db)):
    return db.query(Mesure).filter_by(parcelle_id=pid).order_by(Mesure.horodatage.desc()).limit(limite).all()

@router.post("/irrigations/{pid}", response_model=IrrigationOut, dependencies=[Depends(current_user)])
def lancer(pid: int, duree_min: int = 30, db: Session = Depends(get_db)):
    return irrigation_service.demarrer(db, pid, duree_min)

@router.get("/irrigations", response_model=list[IrrigationOut], dependencies=[Depends(current_user)])
def journal(db: Session = Depends(get_db)):
    return db.query(Irrigation).order_by(Irrigation.debut.desc()).limit(200).all()

@router.get("/cycles", response_model=list[CycleOut], dependencies=[Depends(current_user)])
def lister_cycles(db: Session = Depends(get_db)):
    return db.query(CycleIrrigation).all()

@router.post("/cycles", response_model=CycleOut, status_code=201, dependencies=[Depends(current_user)])
def programmer_cycle(d: CycleIn, db: Session = Depends(get_db)):
    c = CycleIrrigation(**d.model_dump()); db.add(c); db.commit(); db.refresh(c); return c
