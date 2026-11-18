"""Logique métier des alertes : règles, préférences et notifications e-mail/SMS."""
from __future__ import annotations

import logging
import smtplib
import unicodedata
from datetime import datetime, timedelta
from email.message import EmailMessage

import httpx
from sqlalchemy.orm import Session

from ...core.config import settings
from .models import Alerte, PreferenceAlerte
from ..parcelles.models import Exploitation, Parcelle

logger = logging.getLogger(__name__)

SEUIL_MIN, SEUIL_MAX = 30, 45

CATEGORIES = {
    "secheresse": "Sécheresse",
    "exces_eau": "Excès d'eau",
    "capteur": "Capteur",
    "fuite": "Fuite",
    "vanne": "Vanne",
}

PREFIXES_MESSAGES = {
    "secheresse": ("sol sec",),
    "exces_eau": ("excès d'eau", "exces d'eau", "excès d’eau"),
    "capteur": ("capteur", "aucune donnée", "aucune donnee", "caméra", "camera"),
    "fuite": ("fuite",),
    "vanne": ("vanne",),
}


def _normaliser(texte: str) -> str:
    sans_accent = "".join(
        c
        for c in unicodedata.normalize("NFD", texte or "")
        if unicodedata.category(c) != "Mn"
    )
    return sans_accent.lower().strip()


def categorie_depuis_message(message: str) -> str:
    texte = _normaliser(message)
    for categorie, prefixes in PREFIXES_MESSAGES.items():
        if any(_normaliser(prefixe) in texte for prefixe in prefixes):
            return categorie
    return "systeme"


def _alerte_recente(
    db: Session, parcelle_id: int | None, categorie: str, heures: float
) -> Alerte | None:
    if parcelle_id is None:
        return None
    depuis = datetime.utcnow() - timedelta(hours=heures)
    alertes = (
        db.query(Alerte)
        .filter(Alerte.parcelle_id == parcelle_id, Alerte.date >= depuis)
        .order_by(Alerte.date.desc())
        .all()
    )
    for alerte in alertes:
        if categorie_depuis_message(alerte.message) == categorie:
            return alerte
    return None


def creer_alerte(
    db: Session,
    parcelle: Parcelle | None,
    categorie: str,
    niveau: str,
    message: str,
    dedup_heures: float = 1,
    envoyer: bool = True,
) -> Alerte | None:
    parcelle_id = parcelle.id if parcelle else None
    if _alerte_recente(db, parcelle_id, categorie, dedup_heures):
        return None

    alerte = Alerte(
        parcelle_id=parcelle_id,
        niveau=niveau,
        message=message[:250],
    )
    db.add(alerte)
    db.commit()
    db.refresh(alerte)

    if envoyer and parcelle:
        try:
            envoyer_notifications(db, alerte, parcelle)
        except Exception:  # une panne d'e-mail/SMS ne doit jamais bloquer la mesure
            logger.exception("Impossible d'envoyer les notifications de l'alerte %s", alerte.id)

    return alerte


def verifier_humidite(db: Session, parcelle: Parcelle, humidite: float) -> Alerte | None:
    if humidite < SEUIL_MIN:
        return creer_alerte(
            db,
            parcelle,
            "secheresse",
            "urgent",
            f"Sol sec · {parcelle.nom} ({humidite:.0f} %)",
        )
    if humidite > SEUIL_MAX:
        return creer_alerte(
            db,
            parcelle,
            "exces_eau",
            "attention",
            f"Excès d'eau · {parcelle.nom} ({humidite:.0f} %)",
        )
    return None


def verifier_capteurs_hors_service(
    db: Session,
    parcelle_ids: list[int],
    seuil_heures: float = 3,
    inclure_capteurs_silencieux: bool = True,
) -> list[Alerte]:
    """Crée les alertes « capteur/vanne/caméra hors service » encore absentes."""
    from ..equipements.models import Equipement
    from ..humidite.models import Mesure

    if not parcelle_ids:
        return []

    creees: list[Alerte] = []
    equipements = (
        db.query(Equipement)
        .filter(Equipement.parcelle_id.in_(parcelle_ids))
        .all()
    )

    for equipement in equipements:
        parcelle = db.get(Parcelle, equipement.parcelle_id)
        if not parcelle:
            continue

        type_normalise = _normaliser(equipement.type)
        if not equipement.en_ligne:
            if "vanne" in type_normalise:
                categorie, niveau, libelle = "vanne", "urgent", "Vanne"
            elif "camera" in type_normalise:
                categorie, niveau, libelle = "capteur", "attention", "Caméra"
            else:
                categorie, niveau, libelle = "capteur", "urgent", "Capteur"
            alerte = creer_alerte(
                db,
                parcelle,
                categorie,
                niveau,
                f"{libelle} {equipement.code} hors service · {parcelle.nom}",
                dedup_heures=6,
            )
            if alerte:
                creees.append(alerte)
            continue

        if inclure_capteurs_silencieux and "capteur" in type_normalise:
            derniere = (
                db.query(Mesure)
                .filter(Mesure.parcelle_id == parcelle.id)
                .order_by(Mesure.horodatage.desc())
                .first()
            )
            if derniere and datetime.utcnow() - derniere.horodatage > timedelta(hours=seuil_heures):
                heures = int((datetime.utcnow() - derniere.horodatage).total_seconds() // 3600)
                alerte = creer_alerte(
                    db,
                    parcelle,
                    "capteur",
                    "attention",
                    f"Capteur {equipement.code} silencieux · {parcelle.nom} (aucune donnée depuis {heures} h)",
                    dedup_heures=6,
                )
                if alerte:
                    creees.append(alerte)

    return creees


def verifier_toutes_regles(db: Session, parcelle_ids: list[int]) -> list[Alerte]:
    """Rejoue les règles sur les dernières mesures et l'état des équipements."""
    from ..humidite.models import Mesure

    creees: list[Alerte] = []
    for parcelle_id in parcelle_ids:
        parcelle = db.get(Parcelle, parcelle_id)
        if not parcelle:
            continue
        derniere = (
            db.query(Mesure)
            .filter(Mesure.parcelle_id == parcelle_id)
            .order_by(Mesure.horodatage.desc())
            .first()
        )
        if derniere:
            alerte = verifier_humidite(db, parcelle, derniere.humidite)
            if alerte:
                creees.append(alerte)

    creees.extend(verifier_capteurs_hors_service(db, parcelle_ids))
    return creees


def preference_pour(db: Session, user_id: int, categorie: str) -> PreferenceAlerte | None:
    return (
        db.query(PreferenceAlerte)
        .filter(
            PreferenceAlerte.user_id == user_id,
            PreferenceAlerte.categorie == categorie,
        )
        .first()
    )


def envoyer_notifications(db: Session, alerte: Alerte, parcelle: Parcelle | None) -> None:
    if not parcelle:
        return
    exploitation = db.get(Exploitation, parcelle.exploitation_id)
    if not exploitation:
        return

    from ..auth.models import User

    utilisateur = db.get(User, exploitation.user_id)
    if not utilisateur:
        return

    categorie = categorie_depuis_message(alerte.message)
    preference = preference_pour(db, utilisateur.id, categorie)
    if not preference:
        return

    if preference.email and settings.NOTIFICATIONS_EMAIL_ACTIVES:
        envoyer_email(
            utilisateur.email,
            f"Alerte Sevia · {CATEGORIES.get(categorie, 'Information')}",
            f"{alerte.message}\n\nNiveau : {alerte.niveau}\nParcelle : {parcelle.nom}",
        )

    if preference.sms and settings.NOTIFICATIONS_SMS_ACTIVES and utilisateur.telephone:
        envoyer_sms(utilisateur.telephone, f"Sevia : {alerte.message}")


def envoyer_email(destinataire: str, sujet: str, contenu: str) -> bool:
    if not settings.SMTP_HOST or not destinataire:
        return False

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(contenu)

    try:
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
                if settings.SMTP_USER:
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                if settings.SMTP_USER:
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                smtp.send_message(message)
        return True
    except Exception:
        logger.exception("Échec de l'envoi de l'e-mail d'alerte à %s", destinataire)
        return False


def envoyer_sms(destinataire: str, contenu: str) -> bool:
    if not destinataire:
        return False

    fournisseur = (settings.SMS_PROVIDER or "").lower().strip()

    try:
        if fournisseur == "twilio" and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            url = (
                f"https://api.twilio.com/2010-04-01/Accounts/"
                f"{settings.TWILIO_ACCOUNT_SID}/Messages.json"
            )
            reponse = httpx.post(
                url,
                data={
                    "From": settings.TWILIO_FROM_NUMBER,
                    "To": destinataire,
                    "Body": contenu,
                },
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                timeout=10,
            )
            reponse.raise_for_status()
            return True

        if fournisseur == "africastalking" and settings.AFRICASTALKING_API_KEY:
            reponse = httpx.post(
                "https://api.africastalking.com/version1/messaging",
                headers={
                    "apiKey": settings.AFRICASTALKING_API_KEY,
                    "Accept": "application/json",
                },
                data={
                    "username": settings.AFRICASTALKING_USERNAME,
                    "to": destinataire,
                    "message": contenu,
                    "from": settings.AFRICASTALKING_FROM,
                },
                timeout=10,
            )
            reponse.raise_for_status()
            return True
    except Exception:
        logger.exception("Échec de l'envoi du SMS d'alerte à %s", destinataire)

    return False
