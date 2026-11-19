"""CONTRÔLEUR – Fertilisation (données agronomiques, doses, apports, calendrier)."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from ..auth.models import User
from ..parcelles.models import Parcelle, Exploitation
from .models import DonneeAgro, Apport
from ..camera.models import Comptage
from .schemas import *
from . import service as dose_service

router = APIRouter(prefix="/fertilisation", tags=["Fertilisation"], dependencies=[Depends(current_user)])


from ...core.acces import ids_parcelles, parcelle_de


@router.post("/donnees", response_model=DonneeAgroOut, status_code=201)
def saisir_donnees(d: DonneeAgroIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    parcelle_de(db, d.parcelle_id, user)
    x = DonneeAgro(**d.model_dump()); db.add(x); db.commit(); db.refresh(x); return x


@router.get("/donnees/{pid}", response_model=DonneeAgroOut | None)
def dernieres_donnees(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Dernière analyse de sol enregistrée pour cette parcelle (ou null s'il
    n'y en a pas encore) — sert à pré-remplir le formulaire."""
    parcelle_de(db, pid, user)
    return (
        db.query(DonneeAgro)
        .filter_by(parcelle_id=pid)
        .order_by(DonneeAgro.id.desc())
        .first()
    )


@router.get("/dose/{pid}")
def dose_recommandee(
    pid: int,
    surface_ha: float | None = Query(None, gt=0, le=100_000, description="Surface à fertiliser (défaut : surface de la parcelle)"),
    nb_plants: int | None = Query(None, ge=0, description="Nombre de plants (défaut : dernier comptage caméra)"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Quantité d'engrais à épandre selon la culture, l'analyse de sol, la surface (ha)
    et le nombre de plants (densité réelle comparée à la densité de référence)."""
    parcelle = parcelle_de(db, pid, user)

    derniere = (
        db.query(DonneeAgro)
        .filter_by(parcelle_id=pid)
        .order_by(DonneeAgro.id.desc())
        .first()
    )
    azote = derniere.azote if derniere else 0
    phosphore = derniere.phosphore if derniere else 0
    potassium = derniere.potassium if derniere else 0

    culture = dose_service.CULTURE   # seule culture gérée : le maïs

    surface = surface_ha if surface_ha is not None else (parcelle.surface_ha or 0)

    # Nombre de plants : valeur saisie, sinon dernier comptage de la page Caméra
    source_plants, date_comptage = None, None
    if nb_plants is not None:
        source_plants = "saisie"
    else:
        dernier_comptage = (
            db.query(Comptage).filter(Comptage.parcelle_id == pid).order_by(Comptage.date.desc()).first()
        )
        if dernier_comptage and dernier_comptage.nb_plants > 0:
            nb_plants, source_plants, date_comptage = dernier_comptage.nb_plants, "camera", dernier_comptage.date

    par_hectare = dose_service.recommander(culture, azote, phosphore, potassium)
    densite = dose_service.ajuster_densite(culture, surface, nb_plants)
    produits = dose_service.quantites_a_epandre(
        dose_service.suggerer_produits(culture, par_hectare), densite["facteur"], surface, nb_plants
    )

    return {
        "a_partir_dune_analyse": derniere is not None,
        "culture": culture,
        "surface_ha": surface,
        "surface_parcelle_ha": parcelle.surface_ha or 0,
        "nb_plants": nb_plants,
        "source_plants": source_plants,          # "camera" | "saisie" | None
        "date_comptage": date_comptage,
        **densite,
        "besoins_kg_ha": par_hectare,
        "produits_suggeres": produits,
    }


@router.post("/apports", response_model=ApportOut, status_code=201)
def enregistrer_apport(d: ApportIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    parcelle_de(db, d.parcelle_id, user)
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
    requete = db.query(Apport).filter(Apport.parcelle_id.in_(ids_parcelles(db, user))).order_by(Apport.date)
    if realise is not None:
        requete = requete.filter(Apport.realise == realise)
    return requete.all()