import json
import logging
import paho.mqtt.client as mqtt
from ...core.config import settings
from ...core.database import SessionLocal
from ..parcelles.models import Parcelle
from ..alertes.models import Alerte
from .models import MesureHumidite

logger = logging.getLogger("sevia.mqtt")
_client = None


def _extraire_mesure(topic: str, payload_str: str) -> tuple[int | None, float | None]:
    parcelle_id = None
    valeur = None

    # Extraction depuis le topic : sevia/parcelles/<id>/humidite
    morceaux = topic.split("/")
    if len(morceaux) >= 3 and morceaux[1] == "parcelles" and morceaux[2].isdigit():
        parcelle_id = int(morceaux[2])

    try:
        data = json.loads(payload_str)
        if isinstance(data, dict):
            parcelle_id = data.get("parcelle_id", parcelle_id)
            valeur = data.get("humidite") if "humidite" in data else data.get("valeur")
        elif isinstance(data, (int, float)):
            valeur = float(data)
    except json.JSONDecodeError:
        try:
            valeur = float(payload_str.strip())
        except ValueError:
            return None, None

    if parcelle_id is None or valeur is None:
        return None, None
    return int(parcelle_id), round(float(valeur), 1)


def _on_message(client, userdata, msg):
    parcelle_id, valeur = _extraire_mesure(msg.topic, msg.payload.decode("utf-8", errors="ignore"))
    if parcelle_id is None or valeur is None:
        return

    db = SessionLocal()
    try:
        parcelle = db.query(Parcelle).filter(Parcelle.id == parcelle_id).first()
        if not parcelle:
            return

        db.add(MesureHumidite(parcelle_id=parcelle_id, valeur=valeur))

        seuil_min = getattr(parcelle, "seuil_humidite_min", 30.0) or 30.0
        if valeur < seuil_min:
            # Évite de recréer une alerte si une alerte non lue existe déjà pour cette parcelle
            alerte_existante = (
                db.query(Alerte)
                .filter(Alerte.parcelle_id == parcelle_id, Alerte.lue == False)  # noqa: E712
                .first()
            )
            if not alerte_existante:
                db.add(
                    Alerte(
                        parcelle_id=parcelle_id,
                        titre=f"Stress hydrique — {parcelle.nom}",
                        message=f"Humidité mesurée à {valeur}% (seuil minimal : {seuil_min}%). Arrosage recommandé.",
                        niveau="critique",
                    )
                )

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur traitement MQTT : {e}")
    finally:
        db.close()


def demarrer_mqtt():
    global _client
    if not settings.MQTT_ENABLED:
        return

    try:
        _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        _client = mqtt.Client()

    if settings.MQTT_USERNAME:
        _client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

    _client.on_connect = lambda c, u, f, rc, *args: c.subscribe(settings.MQTT_TOPIC)
    _client.on_message = _on_message
    _client.connect_async(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
    _client.loop_start()


def arreter_mqtt():
    global _client
    if _client:
        _client.loop_stop()
        _client.disconnect()