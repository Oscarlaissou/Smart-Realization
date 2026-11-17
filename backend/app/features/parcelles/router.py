from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import current_user
from ..auth.models import User
from ..equipements.models import Equipement
from .models import Parcelle, Exploitation
from .schemas import ParcelleOut, ParcelleCreate, ParcelleUpdate, AssocierEquipement, EquipementOut

router = APIRouter(prefix="/parcelles", tags=["parcelles"])


def _equipements_de(db: Session, parcelle_id: int) -> list[Equipement]:
    return db.query(Equipement).filter(Equipement.parcelle_id == parcelle_id).all()


def _exploitation_de(db: Session, user: User) -> Exploitation:
    exploitation = db.query(Exploitation).filter(Exploitation.user_id == user.id).first()
    if not exploitation:
        raise HTTPException(
            status_code=400,
            detail="Aucune exploitation associée à ce compte.",
        )
    return exploitation


@router.get("", response_model=list[ParcelleOut])
def lister_parcelles(db: Session = Depends(get_db), user: User = Depends(current_user)):
    exploitation = _exploitation_de(db, user)
    parcelles = (
        db.query(Parcelle)
        .filter(Parcelle.exploitation_id == exploitation.id)
        .order_by(Parcelle.id)
        .all()
    )
    equipements = db.query(Equipement).filter(Equipement.parcelle_id.isnot(None)).all()

    par_parcelle: dict[int, list[Equipement]] = {}
    for e in equipements:
        par_parcelle.setdefault(e.parcelle_id, []).append(e)

    resultats = []
    for p in parcelles:
        out = ParcelleOut.model_validate(p, from_attributes=True)
        out.equipements = [
            EquipementOut.model_validate(e, from_attributes=True)
            for e in par_parcelle.get(p.id, [])
        ]
        resultats.append(out)
    return resultats


@router.get("/{parcelle_id}", response_model=ParcelleOut)
def obtenir_parcelle(parcelle_id: int, db: Session = Depends(get_db)):
    parcelle = db.get(Parcelle, parcelle_id)
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")

    out = ParcelleOut.model_validate(parcelle, from_attributes=True)
    out.equipements = [
        EquipementOut.model_validate(e, from_attributes=True)
        for e in _equipements_de(db, parcelle_id)
    ]
    return out


@router.post("", response_model=ParcelleOut, status_code=201)
def creer_parcelle(
    payload: ParcelleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    exploitation = _exploitation_de(db, user)
    parcelle = Parcelle(**payload.model_dump(), exploitation_id=exploitation.id)
    db.add(parcelle)
    db.commit()
    db.refresh(parcelle)
    return ParcelleOut.model_validate(parcelle, from_attributes=True)


@router.put("/{parcelle_id}", response_model=ParcelleOut)
def modifier_parcelle(parcelle_id: int, payload: ParcelleUpdate, db: Session = Depends(get_db)):
    parcelle = db.get(Parcelle, parcelle_id)
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")

    for champ, valeur in payload.model_dump().items():
        setattr(parcelle, champ, valeur)
    db.commit()
    db.refresh(parcelle)

    out = ParcelleOut.model_validate(parcelle, from_attributes=True)
    out.equipements = [
        EquipementOut.model_validate(e, from_attributes=True)
        for e in _equipements_de(db, parcelle_id)
    ]
    return out


@router.delete("/{parcelle_id}", status_code=204)
def supprimer_parcelle(parcelle_id: int, db: Session = Depends(get_db)):
    parcelle = db.get(Parcelle, parcelle_id)
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")
    db.delete(parcelle)
    db.commit()


@router.post("/{parcelle_id}/equipements", status_code=201)
def associer_equipement(parcelle_id: int, payload: AssocierEquipement, db: Session = Depends(get_db)):
    equipement = db.get(Equipement, payload.equipement_id)
    if not equipement:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    equipement.parcelle_id = parcelle_id
    db.commit()
    return {"message": "Équipement associé"}


@router.delete("/{parcelle_id}/equipements/{equipement_id}", status_code=204)
def dissocier_equipement(parcelle_id: int, equipement_id: int, db: Session = Depends(get_db)):
    equipement = db.get(Equipement, equipement_id)
    if not equipement or equipement.parcelle_id != parcelle_id:
        raise HTTPException(status_code=404, detail="Association introuvable")
    equipement.parcelle_id = None
    db.commit()