"""CONTRÔLEUR – Capteurs, électrovannes, caméras, associés à une parcelle."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from ..auth.models import User
from ..parcelles.models import Exploitation
from .models import Equipement
from .schemas import EquipementIn, EquipementOut

router = APIRouter(prefix="/equipements", tags=["Équipements"], dependencies=[Depends(current_user)])

# Durée au-delà de laquelle, sans nouvelle donnée reçue, un capteur est
# considéré "hors service". À ajuster selon la fréquence réelle d'envoi
# de l'ESP32 une fois celle-ci connue.
SEUIL_EN_LIGNE_SECONDES = 60


def _exploitation_de(db: Session, user: User) -> Exploitation:
    exploitation = db.query(Exploitation).filter(Exploitation.user_id == user.id).first()
    if not exploitation:
        raise HTTPException(
            status_code=400,
            detail="Aucune exploitation associée à ce compte.",
        )
    return exploitation


def _vers_sortie(e: Equipement) -> EquipementOut:
    """Convertit un Equipement en EquipementOut, en recalculant 'en_ligne'
    pour les capteurs à partir de 'derniere_donnee' (au lieu de se fier à la
    valeur figée stockée en base). Les électrovannes/caméras gardent pour
    l'instant leur valeur stockée telle quelle."""
    sortie = EquipementOut.model_validate(e)
    if e.type == "capteur":
        en_ligne = (
            e.derniere_donnee is not None
            and datetime.utcnow() - e.derniere_donnee < timedelta(seconds=SEUIL_EN_LIGNE_SECONDES)
        )
        sortie.en_ligne = en_ligne
    return sortie


@router.get("", response_model=list[EquipementOut])
def lister(db: Session = Depends(get_db), user: User = Depends(current_user)):
    exploitation = _exploitation_de(db, user)
    equipements = (
        db.query(Equipement)
        .filter(Equipement.exploitation_id == exploitation.id)
        .all()
    )
    return [_vers_sortie(e) for e in equipements]

@router.post("", response_model=EquipementOut, status_code=201)
def ajouter(d: EquipementIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    exploitation = _exploitation_de(db, user)
    e = Equipement(**d.model_dump(), exploitation_id=exploitation.id)
    db.add(e); db.commit(); db.refresh(e); return _vers_sortie(e)

@router.put("/{eid}", response_model=EquipementOut)
def modifier(eid: int, d: EquipementIn, db: Session = Depends(get_db)):
    e = db.get(Equipement, eid)
    if not e: raise HTTPException(404, "Équipement introuvable")
    for k, v in d.model_dump().items(): setattr(e, k, v)
    db.commit(); db.refresh(e); return _vers_sortie(e)

@router.delete("/{eid}", status_code=204)
def supprimer(eid: int, db: Session = Depends(get_db)):
    e = db.get(Equipement, eid)
    if e: db.delete(e); db.commit()