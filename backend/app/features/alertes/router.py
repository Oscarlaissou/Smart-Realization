"""CONTRÔLEUR – Alertes, compteur et préférences de notification."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.security import current_user
from . import service
from .models import Alerte, PreferenceAlerte
from .schemas import AlerteOut, CompteurOut, PreferenceIn, PreferenceOut
from ..parcelles.models import Exploitation, Parcelle

router = APIRouter(prefix="/alertes", tags=["Alertes"])


def _parcelles_ids(db: Session, user) -> list[int]:
    lignes = (
        db.query(Parcelle.id)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Exploitation.user_id == user.id)
        .all()
    )
    return [ligne[0] for ligne in lignes]


def _canaux(preference: PreferenceAlerte | None) -> list[str]:
    if not preference:
        return ["notification"]
    canaux = []
    if preference.notification:
        canaux.append("notification")
    if preference.email:
        canaux.append("email")
    if preference.sms:
        canaux.append("sms")
    return canaux


def _serialiser(alerte: Alerte, preference: PreferenceAlerte | None = None) -> AlerteOut:
    categorie = service.categorie_depuis_message(alerte.message)
    return AlerteOut(
        id=alerte.id,
        parcelle_id=alerte.parcelle_id,
        niveau=alerte.niveau,
        message=alerte.message,
        lue=alerte.lue,
        date=alerte.date,
        categorie=categorie,
        canaux=_canaux(preference),
    )


def _preferences_effectives(db: Session, user) -> list[PreferenceOut]:
    existantes = {
        preference.categorie: preference
        for preference in db.query(PreferenceAlerte).filter(PreferenceAlerte.user_id == user.id).all()
    }
    resultat: list[PreferenceOut] = []
    for categorie, libelle in service.CATEGORIES.items():
        preference = existantes.get(categorie)
        resultat.append(
            PreferenceOut(
                id=preference.id if preference else None,
                categorie=categorie,
                notification=preference.notification if preference else True,
                email=preference.email if preference else False,
                sms=preference.sms if preference else False,
                libelle=libelle,
            )
        )
    return resultat


@router.get("", response_model=list[AlerteOut])
def lister(
    categorie: str | None = Query(None),
    niveau: str | None = Query(None),
    non_lues: bool = Query(False),
    limite: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    ids = _parcelles_ids(db, user)
    if not ids:
        return []

    # Les règles sont rejouées à l'ouverture de la page (déduplication incluse).
    service.verifier_toutes_regles(db, ids)

    categorie_filtre = (categorie or "").strip().lower() or None

    requete = db.query(Alerte).filter(Alerte.parcelle_id.in_(ids))
    if niveau:
        requete = requete.filter(Alerte.niveau == niveau)
    alertes = requete.order_by(Alerte.date.desc()).limit(500).all()
    preferences = {
        preference.categorie: preference
        for preference in db.query(PreferenceAlerte)
        .filter(PreferenceAlerte.user_id == user.id)
        .all()
    }

    resultat = []
    for alerte in alertes:
        categorie_alerte = service.categorie_depuis_message(alerte.message)
        if categorie_filtre and categorie_alerte != categorie_filtre:
            continue
        if non_lues and alerte.lue:
            continue
        resultat.append(_serialiser(alerte, preferences.get(categorie_alerte)))
        if len(resultat) >= limite:
            break
    return resultat


@router.get("/compteur", response_model=CompteurOut)
def compteur(db: Session = Depends(get_db), user=Depends(current_user)):
    ids = _parcelles_ids(db, user)
    if not ids:
        return CompteurOut(non_lues=0, total=0)
    total = db.query(Alerte).filter(Alerte.parcelle_id.in_(ids)).count()
    non_lues = (
        db.query(Alerte)
        .filter(Alerte.parcelle_id.in_(ids), Alerte.lue.is_(False))
        .count()
    )
    return CompteurOut(non_lues=non_lues, total=total)


@router.get("/preferences", response_model=list[PreferenceOut])
def lire_preferences(db: Session = Depends(get_db), user=Depends(current_user)):
    return _preferences_effectives(db, user)


@router.post("/test-email")
def tester_email(user=Depends(current_user)):
    if not settings.SMTP_HOST:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "SMTP non configuré : renseignez SMTP_HOST dans backend/.env puis redémarrez l'API.",
        )
    if not user.email:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Aucune adresse e-mail associée à votre compte.",
        )
    envoye = service.envoyer_email(
        user.email,
        "Test Sevia · Notifications e-mail",
        "Ceci est un e-mail de test envoyé depuis Sevia. "
        "Si vous le recevez, la configuration SMTP est correcte.",
    )
    if not envoye:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Échec de l'envoi. Vérifiez SMTP_HOST, SMTP_PORT, SMTP_USER, "
            "SMTP_PASSWORD et la console de l'API.",
        )
    return {"message": f"E-mail de test envoyé à {user.email}."}


@router.put("/preferences", response_model=list[PreferenceOut])
def enregistrer_preferences(
    donnees: list[PreferenceIn],
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    for donnee in donnees:
        if donnee.categorie not in service.CATEGORIES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Type d'alerte inconnu : {donnee.categorie}",
            )
        preference = service.preference_pour(db, user.id, donnee.categorie)
        if not preference:
            preference = PreferenceAlerte(user_id=user.id, categorie=donnee.categorie)
            db.add(preference)
        preference.notification = donnee.notification
        preference.email = donnee.email
        preference.sms = donnee.sms
    db.commit()
    return _preferences_effectives(db, user)


@router.post("/verifier", response_model=CompteurOut)
def verifier_regles(db: Session = Depends(get_db), user=Depends(current_user)):
    ids = _parcelles_ids(db, user)
    service.verifier_toutes_regles(db, ids)
    total = db.query(Alerte).filter(Alerte.parcelle_id.in_(ids)).count() if ids else 0
    non_lues = (
        db.query(Alerte)
        .filter(Alerte.parcelle_id.in_(ids), Alerte.lue.is_(False))
        .count()
        if ids
        else 0
    )
    return CompteurOut(non_lues=non_lues, total=total)


@router.post("/tout-lues", status_code=204)
def marquer_tout_lu(db: Session = Depends(get_db), user=Depends(current_user)):
    ids = _parcelles_ids(db, user)
    if ids:
        db.query(Alerte).filter(Alerte.parcelle_id.in_(ids)).update(
            {Alerte.lue: True}, synchronize_session=False
        )
        db.commit()
    return Response(status_code=204)


@router.post("/{aid}/lue", response_model=AlerteOut)
def marquer_lue(aid: int, db: Session = Depends(get_db), user=Depends(current_user)):
    ids = _parcelles_ids(db, user)
    alerte = (
        db.query(Alerte)
        .filter(Alerte.id == aid, Alerte.parcelle_id.in_(ids))
        .first()
    )
    if not alerte:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alerte introuvable")
    alerte.lue = True
    db.commit()
    db.refresh(alerte)
    categorie = service.categorie_depuis_message(alerte.message)
    return _serialiser(alerte, service.preference_pour(db, user.id, categorie))
