
"""Réception des mesures envoyées par les ESP32 via MQTT.

Topic attendu :
    sevia/parcelle/<id>/humidite

Payload accepté :
    {"humidite": 27.4}
    {"valeur": 27.4}
    {"moisture": 27.4}
    27.4
"""

import json
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

from ..core.config import settings
from ..core.database import SessionLocal
from ..features.parcelles.models import Parcelle
from ..features.humidite.models import MesureHumidite
from ..features.equipements.models import Equipement
from ..features.alertes import service as alerte_service


logger = logging.getLogger(__name__)

_client = None


def _extraire_mesure(
    topic: str,
    payload_str: str
) -> tuple[int | None, float | None]:

    parcelle_id = None
    valeur = None

    # Récupération de l'identifiant de la parcelle depuis le topic.
    morceaux = topic.split("/")

    for prefixe in ("parcelle", "parcelles"):
        if prefixe in morceaux:
            idx = morceaux.index(prefixe)

            if idx + 1 < len(morceaux):
                identifiant = morceaux[idx + 1]

                if identifiant.isdigit():
                    parcelle_id = int(identifiant)

            break

    # Lecture du contenu envoyé par l'ESP32.
    try:
        data = json.loads(payload_str)

        if isinstance(data, dict):

            if data.get("parcelle_id") is not None:
                parcelle_id = int(data["parcelle_id"])

            for cle in ("humidite", "valeur", "moisture"):
                if data.get(cle) is not None:
                    valeur = float(data[cle])
                    break

        elif isinstance(data, (int, float)):
            valeur = float(data)

    except (json.JSONDecodeError, ValueError, TypeError):
        try:
            valeur = float(payload_str.strip())
        except ValueError:
            return None, None

    if parcelle_id is None or valeur is None:
        return None, None

    # Une humidité doit être comprise entre 0 et 100 %.
    if not 0 <= valeur <= 100:
        return None, None

    return parcelle_id, round(valeur, 1)


def on_connect(client, userdata, flags, reason_code, properties):
    """Appelé lorsque le client se connecte au broker MQTT."""

    topic = (
        getattr(settings, "MQTT_TOPIC", None)
        or "sevia/parcelle/+/humidite"
    )

    client.subscribe(topic, qos=1)

    logger.info(
        "[MQTT] Connecté à %s:%s (code=%s), topic=%s",
        settings.MQTT_HOST,
        settings.MQTT_PORT,
        reason_code,
        topic,
    )


def on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties
):
    """Appelé lorsque le client perd sa connexion."""

    logger.warning(
        "[MQTT] Déconnecté du broker (code=%s).",
        reason_code,
    )


def on_message(client, userdata, msg):
    """Traite une mesure reçue depuis un ESP32."""

    payload_str = msg.payload.decode("utf-8", errors="ignore")

    logger.info(
        "[MQTT] Message reçu sur %s : %s",
        msg.topic,
        payload_str,
    )

    parcelle_id, valeur = _extraire_mesure(
        msg.topic,
        payload_str,
    )

    if parcelle_id is None or valeur is None:
        logger.warning("[MQTT] Message ignoré : format invalide.")
        return

    db = SessionLocal()

    try:
        # 1. Vérifier que la parcelle existe.
        parcelle = db.get(Parcelle, parcelle_id)

        if not parcelle:
            logger.warning(
                "[MQTT] Parcelle #%s introuvable.",
                parcelle_id,
            )
            return

        # 2. Enregistrer la mesure d'humidité.
        mesure = MesureHumidite(
            parcelle_id=parcelle_id,
            valeur=valeur,
        )

        db.add(mesure)

        # 3. Mettre à jour les capteurs associés à la parcelle.
        # Le message actuel ne permet pas d'identifier un capteur précis.
        capteurs = (
            db.query(Equipement)
            .filter(
                Equipement.parcelle_id == parcelle_id,
                Equipement.type == "capteur",
            )
            .all()
        )

        maintenant = datetime.utcnow()

        for capteur in capteurs:
            capteur.derniere_donnee = maintenant
            capteur.en_ligne = True

        # 4. Enregistrer la mesure et les modifications des équipements.
        db.commit()

        logger.info(
            "[MQTT] Mesure enregistrée : %s (#%s) -> %.1f %%",
            parcelle.nom,
            parcelle_id,
            valeur,
        )

        # 5. Vérifier les seuils d'humidité et créer une alerte si nécessaire.
        alerte = alerte_service.verifier_humidite(
            db,
            parcelle,
            valeur,
        )

        if alerte:
            logger.warning(
                "[MQTT] Alerte créée : %s",
                alerte.message,
            )

    except Exception:
        db.rollback()
        logger.exception(
            "[MQTT] Erreur pendant le traitement de la mesure."
        )

    finally:
        db.close()


def demarrer():
    """Démarre le client MQTT."""

    global _client

    if _client is not None:
        logger.info("[MQTT] Le client est déjà démarré.")
        return

    try:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )

        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message

        client.connect(
            settings.MQTT_HOST,
            settings.MQTT_PORT,
            keepalive=60,
        )

        _client = client
        client.loop_start()

        logger.info("[MQTT] Client démarré.")

    except Exception:
        _client = None
        logger.exception(
            "[MQTT] Impossible de démarrer le client."
        )


def arreter():
    """Arrête proprement le client MQTT."""

    global _client

    if _client is not None:
        _client.loop_stop()
        _client.disconnect()
        _client = None

        logger.info("[MQTT] Client arrêté.")
