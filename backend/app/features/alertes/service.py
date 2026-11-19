"""Logique métier des alertes : règles, préférences et notifications e-mail/SMS."""
from __future__ import annotations

import logging
import smtplib
import threading
import unicodedata
from datetime import datetime, timedelta
from email.message import EmailMessage

import httpx
from sqlalchemy.orm import Session

from ...core.config import settings
from .models import Alerte, PreferenceAlerte
from ..parcelles.models import Exploitation, Parcelle

logger = logging.getLogger(__name__)

# Seuils d'humidité par défaut (%), quand la parcelle n'a pas ses propres seuils.
# SOURCE UNIQUE : alertes, page Humidité et tableau de bord passent tous par seuils_humidite().
SEUIL_MIN, SEUIL_MAX = 30.0, 65.0


def seuils_humidite(parcelle: Parcelle) -> tuple[float, float]:
    """(min, max) de la parcelle (réglés depuis la page Humidité), sinon les valeurs par défaut."""
    seuil_min = getattr(parcelle, "seuil_humidite_min", None)
    seuil_max = getattr(parcelle, "seuil_humidite_max", None)
    return (
        SEUIL_MIN if seuil_min is None else float(seuil_min),
        SEUIL_MAX if seuil_max is None else float(seuil_max),
    )

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


def _en_arriere_plan(fonction, *args) -> None:
    """L'envoi SMTP/SMS prend plusieurs secondes : il ne doit retarder ni la mesure ni la page."""
    threading.Thread(target=fonction, args=args, daemon=True).start()


def verifier_humidite(db: Session, parcelle: Parcelle, humidite: float) -> Alerte | None:
    seuil_min, seuil_max = seuils_humidite(parcelle)
    if humidite < seuil_min:
        return creer_alerte(
            db,
            parcelle,
            "secheresse",
            "urgent",
            f"Sol sec · {parcelle.nom} ({humidite:.0f} %)",
        )
    if humidite > seuil_max:
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

    # 1. Signalement en direct : popup sur toutes les pages ouvertes du propriétaire
    from ...core import temps_reel

    temps_reel.publier(utilisateur.id, {
        "type": "alerte",
        "parcelle_id": parcelle.id,
        "parcelle": parcelle.nom,
        "alerte": {
            "id": alerte.id,
            "niveau": alerte.niveau,
            "message": alerte.message,
            "categorie": categorie,
            "date": alerte.date.isoformat() if alerte.date else None,
        },
    })

    # 2. E-mail à CHAQUE alerte, à l'adresse saisie dans la page Alertes (s'il y en a une)
    if utilisateur.email_alertes and settings.NOTIFICATIONS_EMAIL_ACTIVES:
        _en_arriere_plan(
            envoyer_email,
            utilisateur.email_alertes,
            f"Alerte Sevia · {CATEGORIES.get(categorie, 'Information')} · {parcelle.nom}",
            f"{alerte.message}\n\nNiveau : {alerte.niveau}\nParcelle : {parcelle.nom}\n"
            f"Date : {alerte.date:%d/%m/%Y %H:%M} (UTC)\n\n— Sevia",
        )

    # 3. SMS : selon les préférences par type d'alerte
    preference = preference_pour(db, utilisateur.id, categorie)
    if preference and preference.sms and settings.NOTIFICATIONS_SMS_ACTIVES and utilisateur.telephone:
        _en_arriere_plan(envoyer_sms, utilisateur.telephone, f"Sevia : {alerte.message}")


AIDE_IDENTIFIANTS = (
    "Le serveur e-mail refuse l'identifiant ou le mot de passe (SMTP_USER / SMTP_PASSWORD). "
    "Avec Gmail : activez la validation en deux étapes, créez un « mot de passe d'application » "
    "et mettez-le dans SMTP_PASSWORD, avec la MÊME adresse Gmail dans SMTP_USER."
)


def _identifiants_smtp() -> tuple[str, str]:
    utilisateur = (settings.SMTP_USER or "").strip()
    mot_de_passe = settings.SMTP_PASSWORD or ""
    if "gmail" in (settings.SMTP_HOST or "").lower():
        # Google affiche le mot de passe d'application en 4 blocs « abcd efgh ijkl mnop »
        mot_de_passe = mot_de_passe.replace(" ", "")
    return utilisateur, mot_de_passe


def _connexion(smtp: smtplib.SMTP) -> None:
    utilisateur, mot_de_passe = _identifiants_smtp()
    if not utilisateur:
        return
    smtp.ehlo()
    if "auth" in smtp.esmtp_features and "LOGIN" in smtp.esmtp_features["auth"].upper():
        # AUTH LOGIN : en cas de refus, le serveur répond « 535 » au lieu de couper la connexion
        smtp.esmtp_features["auth"] = "LOGIN"
    smtp.login(utilisateur, mot_de_passe)


def envoyer_email_detail(destinataire: str, sujet: str, contenu: str) -> tuple[bool, str | None]:
    """Envoie l'e-mail. Renvoie (True, None) ou (False, raison lisible par l'utilisateur)."""
    if not destinataire:
        return False, "Aucune adresse de destination."
    if not settings.SMTP_HOST:
        return False, "SMTP non configuré : renseignez SMTP_HOST dans backend/.env."

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM or (settings.SMTP_USER or "").strip()
    message["To"] = destinataire
    message["Subject"] = sujet
    message.set_content(contenu)

    try:
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                _connexion(smtp)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                _connexion(smtp)
                smtp.send_message(message)
        return True, None
    except smtplib.SMTPAuthenticationError as erreur:
        raison = f"{AIDE_IDENTIFIANTS} (code {erreur.smtp_code})"
    except smtplib.SMTPServerDisconnected:
        raison = f"Le serveur e-mail a coupé la connexion. {AIDE_IDENTIFIANTS}"
    except smtplib.SMTPRecipientsRefused:
        raison = f"Adresse de destination refusée par le serveur : {destinataire}"
    except (OSError, smtplib.SMTPConnectError) as erreur:
        raison = f"Serveur e-mail injoignable ({settings.SMTP_HOST}:{settings.SMTP_PORT}) : {erreur}"
    except smtplib.SMTPException as erreur:
        raison = f"Erreur du serveur e-mail : {erreur}"
    logger.error("E-mail non envoyé à %s : %s", destinataire, raison)
    return False, raison


def envoyer_email(destinataire: str, sujet: str, contenu: str) -> bool:
    return envoyer_email_detail(destinataire, sujet, contenu)[0]


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
