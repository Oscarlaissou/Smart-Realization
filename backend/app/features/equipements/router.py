"""CONTRÔLEUR – Capteurs, électrovannes, caméras, associés à une parcelle."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from ..auth.models import User
from ..parcelles.models import Exploitation, Parcelle
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


def _ids_exploitations(db: Session, user: User) -> list[int]:
    return [e.id for e in db.query(Exploitation.id).filter(Exploitation.user_id == user.id).all()]


def statut_en_ligne(e: Equipement) -> bool:
    """Capteurs : en ligne si une donnée est arrivée récemment ('derniere_donnee', mise à jour
    par le listener MQTT). Électrovannes/caméras : valeur stockée telle quelle pour l'instant.
    Utilisé aussi par parcelles/router.py."""
    if e.type == "capteur":
        return e.derniere_donnee is not None and (
            datetime.utcnow() - e.derniere_donnee < timedelta(seconds=SEUIL_EN_LIGNE_SECONDES)
        )
    return bool(e.en_ligne)


def _vers_sortie(e: Equipement) -> EquipementOut:
    sortie = EquipementOut.model_validate(e)
    sortie.en_ligne = statut_en_ligne(e)
    return sortie


@router.get("", response_model=list[EquipementOut])
def lister(db: Session = Depends(get_db), user: User = Depends(current_user)):
    _exploitation_de(db, user)   # 400 explicite si le compte n'a encore aucune exploitation
    equipements = (
        db.query(Equipement)
        .filter(Equipement.exploitation_id.in_(_ids_exploitations(db, user)))
        .order_by(Equipement.id)
        .all()
    )
    return [_vers_sortie(e) for e in equipements]

@router.post("", response_model=EquipementOut, status_code=201)
def ajouter(d: EquipementIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    exploitation_id = _exploitation_de(db, user).id
    if d.parcelle_id is not None:
        # L'équipement rejoint l'exploitation de sa parcelle (qui doit appartenir à l'utilisateur)
        parcelle = db.get(Parcelle, d.parcelle_id)
        if not parcelle or parcelle.exploitation_id not in _ids_exploitations(db, user):
            raise HTTPException(404, "Parcelle introuvable")
        exploitation_id = parcelle.exploitation_id
    e = Equipement(**d.model_dump(), exploitation_id=exploitation_id)
    db.add(e); db.commit(); db.refresh(e); return _vers_sortie(e)

def _equipement_de(db: Session, eid: int, user: User) -> Equipement:
    """L'équipement s'il appartient à une exploitation de l'utilisateur, sinon 404."""
    e = db.get(Equipement, eid)
    if not e or e.exploitation_id not in _ids_exploitations(db, user):
        raise HTTPException(404, "Équipement introuvable")
    return e


@router.put("/{eid}", response_model=EquipementOut)
def modifier(eid: int, d: EquipementIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    e = _equipement_de(db, eid, user)
    if d.parcelle_id is not None:
        parcelle = db.get(Parcelle, d.parcelle_id)
        if not parcelle or parcelle.exploitation_id not in _ids_exploitations(db, user):
            raise HTTPException(404, "Parcelle introuvable")
        e.exploitation_id = parcelle.exploitation_id
    for k, v in d.model_dump().items(): setattr(e, k, v)
    db.commit(); db.refresh(e); return _vers_sortie(e)

@router.delete("/{eid}", status_code=204)
def supprimer(eid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    e = _equipement_de(db, eid, user)
    db.delete(e); db.commit()