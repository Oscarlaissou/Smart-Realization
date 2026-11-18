"""CONTRÔLEUR – Exploitations, parcelles et cultures (CRUD + validations)."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import current_user
from .models import Exploitation, Parcelle, Culture
from ..equipements.models import Equipement
from ..equipements.router import statut_en_ligne
from .schemas import (
    AssocierEquipement,
    CultureIn,
    EquipementResume,
    CultureOut,
    ExploitationIn,
    ExploitationOut,
    ParcelleIn,
    ParcelleOut,
)

router = APIRouter(tags=["Exploitations et parcelles"])


def _exploitation_du_user(db: Session, eid: int, user) -> Exploitation:
    exploitation = db.get(Exploitation, eid)
    if not exploitation or exploitation.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exploitation introuvable")
    return exploitation


def _parcelle_du_user(db: Session, pid: int, user) -> Parcelle:
    parcelle = (
        db.query(Parcelle)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Parcelle.id == pid, Exploitation.user_id == user.id)
        .first()
    )
    if not parcelle:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parcelle introuvable")
    return parcelle


def _culture_du_user(db: Session, cid: int, user) -> Culture:
    culture = (
        db.query(Culture)
        .join(Parcelle, Culture.parcelle_id == Parcelle.id)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Culture.id == cid, Exploitation.user_id == user.id)
        .first()
    )
    if not culture:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Culture introuvable")
    return culture


def _supprimer_dependances_parcelle(db: Session, parcelle_id: int) -> None:
    """Supprime (ou détache) les données liées avant une suppression de parcelle."""
    from ..alertes.models import Alerte
    from ..camera.models import Comptage
    from ..equipements.models import Equipement
    from ..fertilisation.models import Apport, DonneeAgro
    from ..humidite.models import Irrigation, Mesure

    db.query(Alerte).filter(Alerte.parcelle_id == parcelle_id).delete(synchronize_session=False)
    db.query(Mesure).filter(Mesure.parcelle_id == parcelle_id).delete(synchronize_session=False)
    db.query(Irrigation).filter(Irrigation.parcelle_id == parcelle_id).delete(synchronize_session=False)
    db.query(Comptage).filter(Comptage.parcelle_id == parcelle_id).delete(synchronize_session=False)
    db.query(DonneeAgro).filter(DonneeAgro.parcelle_id == parcelle_id).delete(synchronize_session=False)
    db.query(Apport).filter(Apport.parcelle_id == parcelle_id).delete(synchronize_session=False)
    db.query(Equipement).filter(Equipement.parcelle_id == parcelle_id).update(
        {Equipement.parcelle_id: None}, synchronize_session=False
    )
    db.query(Culture).filter(Culture.parcelle_id == parcelle_id).delete(synchronize_session=False)


def _ids_exploitations(db: Session, user) -> list[int]:
    return [e.id for e in db.query(Exploitation.id).filter(Exploitation.user_id == user.id).all()]


def _resume(e: Equipement) -> EquipementResume:
    return EquipementResume(id=e.id, code=e.code, type=e.type, en_ligne=statut_en_ligne(e))


def _sortie(db: Session, parcelle: Parcelle) -> ParcelleOut:
    """ParcelleOut + équipements associés (pas de relationship SQLAlchemy vers Equipement)."""
    out = ParcelleOut.model_validate(parcelle)
    out.equipements = [
        _resume(e)
        for e in db.query(Equipement).filter(Equipement.parcelle_id == parcelle.id).order_by(Equipement.id)
    ]
    return out


def _sorties(db: Session, parcelles: list[Parcelle]) -> list[ParcelleOut]:
    ids = [p.id for p in parcelles]
    par_parcelle: dict[int, list[Equipement]] = {}
    if ids:
        for e in db.query(Equipement).filter(Equipement.parcelle_id.in_(ids)).order_by(Equipement.id):
            par_parcelle.setdefault(e.parcelle_id, []).append(e)
    resultats = []
    for p in parcelles:
        out = ParcelleOut.model_validate(p)
        out.equipements = [_resume(e) for e in par_parcelle.get(p.id, [])]
        resultats.append(out)
    return resultats


# ---------------------------------------------------------------------------
# Exploitations
# ---------------------------------------------------------------------------
@router.get("/exploitations", response_model=list[ExploitationOut])
def lister_exploitations(db: Session = Depends(get_db), user=Depends(current_user)):
    return (
        db.query(Exploitation)
        .filter(Exploitation.user_id == user.id)
        .order_by(Exploitation.id.asc())
        .all()
    )


@router.post("/exploitations", response_model=ExploitationOut, status_code=201)
def creer_exploitation(
    donnees: ExploitationIn,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    exploitation = Exploitation(**donnees.model_dump(), user_id=user.id)
    db.add(exploitation)
    db.commit()
    db.refresh(exploitation)
    return exploitation


@router.get("/exploitations/{eid}", response_model=ExploitationOut)
def lire_exploitation(eid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    return _exploitation_du_user(db, eid, user)


@router.put("/exploitations/{eid}", response_model=ExploitationOut)
def modifier_exploitation(
    eid: int,
    donnees: ExploitationIn,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    exploitation = _exploitation_du_user(db, eid, user)
    for cle, valeur in donnees.model_dump().items():
        setattr(exploitation, cle, valeur)
    db.commit()
    db.refresh(exploitation)
    return exploitation


@router.delete("/exploitations/{eid}", status_code=204)
def supprimer_exploitation(eid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    exploitation = _exploitation_du_user(db, eid, user)
    parcelles = db.query(Parcelle).filter(Parcelle.exploitation_id == exploitation.id).all()
    for parcelle in parcelles:
        _supprimer_dependances_parcelle(db, parcelle.id)
        db.delete(parcelle)
    db.delete(exploitation)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Parcelles
# ---------------------------------------------------------------------------
@router.get("/parcelles", response_model=list[ParcelleOut])
def lister_parcelles(
    exploitation_id: int | None = Query(None, gt=0),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    requete = (
        db.query(Parcelle)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Exploitation.user_id == user.id)
    )
    if exploitation_id is not None:
        requete = requete.filter(Parcelle.exploitation_id == exploitation_id)
    return _sorties(db, requete.order_by(Parcelle.id.asc()).all())


@router.post("/parcelles", response_model=ParcelleOut, status_code=201)
def creer_parcelle(
    donnees: ParcelleIn,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    _exploitation_du_user(db, donnees.exploitation_id, user)
    parcelle = Parcelle(**donnees.model_dump())
    db.add(parcelle)
    db.commit()
    db.refresh(parcelle)
    return _sortie(db, parcelle)


@router.get("/parcelles/{pid}", response_model=ParcelleOut)
def lire_parcelle(pid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    return _sortie(db, _parcelle_du_user(db, pid, user))


@router.put("/parcelles/{pid}", response_model=ParcelleOut)
def modifier_parcelle(
    pid: int,
    donnees: ParcelleIn,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    parcelle = _parcelle_du_user(db, pid, user)
    _exploitation_du_user(db, donnees.exploitation_id, user)
    # exclude_unset : un champ non envoyé (ex. seuils réglés depuis la page Humidité) n'est pas effacé
    for cle, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(parcelle, cle, valeur)
    db.commit()
    db.refresh(parcelle)
    return _sortie(db, parcelle)


@router.delete("/parcelles/{pid}", status_code=204)
def supprimer_parcelle(pid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    parcelle = _parcelle_du_user(db, pid, user)
    _supprimer_dependances_parcelle(db, parcelle.id)
    db.delete(parcelle)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Équipements associés à une parcelle
# ---------------------------------------------------------------------------
@router.post("/parcelles/{pid}/equipements", response_model=ParcelleOut, status_code=201)
def associer_equipement(
    pid: int,
    donnees: AssocierEquipement,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    parcelle = _parcelle_du_user(db, pid, user)
    equipement = db.get(Equipement, donnees.equipement_id)
    if not equipement or equipement.exploitation_id not in _ids_exploitations(db, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Équipement introuvable")
    equipement.parcelle_id = parcelle.id
    db.commit()
    return _sortie(db, parcelle)


@router.delete("/parcelles/{pid}/equipements/{eid}", status_code=204)
def dissocier_equipement(pid: int, eid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    _parcelle_du_user(db, pid, user)
    equipement = db.get(Equipement, eid)
    if not equipement or equipement.parcelle_id != pid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Association introuvable")
    equipement.parcelle_id = None
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Cultures
# ---------------------------------------------------------------------------
@router.get("/parcelles/{pid}/cultures", response_model=list[CultureOut])
def lister_cultures(pid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    _parcelle_du_user(db, pid, user)
    return db.query(Culture).filter(Culture.parcelle_id == pid).order_by(Culture.id.asc()).all()


@router.post("/parcelles/{pid}/cultures", response_model=CultureOut, status_code=201)
def ajouter_culture(
    pid: int,
    donnees: CultureIn,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    _parcelle_du_user(db, pid, user)
    culture = Culture(**donnees.model_dump(), parcelle_id=pid)
    db.add(culture)
    db.commit()
    db.refresh(culture)
    return culture


@router.put("/cultures/{cid}", response_model=CultureOut)
def modifier_culture(
    cid: int,
    donnees: CultureIn,
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    culture = _culture_du_user(db, cid, user)
    for cle, valeur in donnees.model_dump().items():
        setattr(culture, cle, valeur)
    db.commit()
    db.refresh(culture)
    return culture


@router.delete("/cultures/{cid}", status_code=204)
def supprimer_culture(cid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    culture = _culture_du_user(db, cid, user)
    db.delete(culture)
    db.commit()
    return Response(status_code=204)
