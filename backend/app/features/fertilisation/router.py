"""CONTRÔLEUR – Fertilisation (données agronomiques, doses, apports, calendrier)."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from ..auth.models import User
from ..parcelles.models import Parcelle, Exploitation
from .models import DonneeAgro, Apport
from .schemas import *
from . import service as dose_service

router = APIRouter(prefix="/fertilisation", tags=["Fertilisation"], dependencies=[Depends(current_user)])


def _exploitation_de(db: Session, user: User) -> Exploitation:
    exploitation = db.query(Exploitation).filter(Exploitation.user_id == user.id).first()
    if not exploitation:
        raise HTTPException(status_code=400, detail="Aucune exploitation associée à ce compte.")
    return exploitation


def _parcelle_de_lexploitation(db: Session, pid: int, exploitation: Exploitation) -> Parcelle:
    parcelle = (
        db.query(Parcelle)
        .filter(Parcelle.id == pid, Parcelle.exploitation_id == exploitation.id)
        .first()
    )
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")
    return parcelle


@router.post("/donnees", response_model=DonneeAgroOut, status_code=201)
def saisir_donnees(d: DonneeAgroIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    exploitation = _exploitation_de(db, user)
    _parcelle_de_lexploitation(db, d.parcelle_id, exploitation)
    x = DonneeAgro(**d.model_dump()); db.add(x); db.commit(); db.refresh(x); return x


@router.get("/donnees/{pid}", response_model=DonneeAgroOut | None)
def dernieres_donnees(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Dernière analyse de sol enregistrée pour cette parcelle (ou null s'il
    n'y en a pas encore) — sert à pré-remplir le formulaire."""
    exploitation = _exploitation_de(db, user)
    _parcelle_de_lexploitation(db, pid, exploitation)
    return (
        db.query(DonneeAgro)
        .filter_by(parcelle_id=pid)
        .order_by(DonneeAgro.id.desc())
        .first()
    )


@router.get("/dose/{pid}")
def dose_recommandee(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    exploitation = _exploitation_de(db, user)
    parcelle = _parcelle_de_lexploitation(db, pid, exploitation)

    derniere = (
        db.query(DonneeAgro)
        .filter_by(parcelle_id=pid)
        .order_by(DonneeAgro.id.desc())
        .first()
    )
    azote = derniere.azote if derniere else 0
    phosphore = derniere.phosphore if derniere else 0
    potassium = derniere.potassium if derniere else 0

    par_hectare = dose_service.recommander(parcelle.culture, azote, phosphore, potassium)
    surface = parcelle.surface_ha or 0

    produits = dose_service.suggerer_produits(parcelle.culture, par_hectare)
    for p in produits:
        p["quantite_totale_kg"] = round(p["quantite_kg_ha"] * surface, 1)

    return {
        "a_partir_dune_analyse": derniere is not None,
        "culture": parcelle.culture,
        "surface_ha": surface,
        "produits_suggeres": produits,
    }


@router.post("/apports", response_model=ApportOut, status_code=201)
def enregistrer_apport(d: ApportIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    exploitation = _exploitation_de(db, user)
    _parcelle_de_lexploitation(db, d.parcelle_id, exploitation)
    data = d.model_dump(); data["date"] = data["date"] or datetime.utcnow()
    a = Apport(**data); db.add(a); db.commit(); db.refresh(a); return a


@router.get("/apports", response_model=list[ApportOut])
def lister_apports(
    realise: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Tous les apports de l'exploitation connectée. realise=true -> déjà
    faits (historique) ; realise=false -> planifiés (calendrier/rappels) ;
    omis -> les deux."""
    exploitation = _exploitation_de(db, user)
    ids_parcelles = [
        pid for (pid,) in db.query(Parcelle.id)
        .filter(Parcelle.exploitation_id == exploitation.id)
        .all()
    ]
    requete = db.query(Apport).filter(Apport.parcelle_id.in_(ids_parcelles)).order_by(Apport.date)
    if realise is not None:
        requete = requete.filter(Apport.realise == realise)
    return requete.all()