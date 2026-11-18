import json
import uuid
import paho.mqtt.client as mqtt
from ..core.config import settings
from ..core.database import SessionLocal
from ..features.parcelles.models import Parcelle
from ..features.humidite.models import MesureHumidite

_client = None


def _extraire_mesure(topic: str, payload_str: str) -> tuple[int | None, float | None]:
    parcelle_id = None
    valeur = None

    morceaux = topic.split("/")
    if "parcelles" in morceaux:
        idx = morceaux.index("parcelles")
        if idx + 1 < len(morceaux) and morceaux[idx + 1].isdigit():
            parcelle_id = int(morceaux[idx + 1])

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
    return parcelle_id, round(valeur, 1)


def on_connect(client, userdata, flags, rc, *args):
    topic = getattr(settings, "MQTT_TOPIC", "sevia_collines/#") or "sevia_collines/#"
    client.subscribe(topic, qos=1)
    print(f"[MQTT] Connecté à {settings.MQTT_HOST}:{settings.MQTT_PORT} (rc={rc}) | Topic='{topic}'", flush=True)


def on_disconnect(client, userdata, *args):
    print("[MQTT] Déconnecté du broker, tentative de reconnexion...", flush=True)


def on_message(client, userdata, msg):
    payload_str = msg.payload.decode("utf-8", errors="ignore")
    print(f"[MQTT] Reçu sur '{msg.topic}' : {payload_str}", flush=True)

    parcelle_id, valeur = _extraire_mesure(msg.topic, payload_str)
    if parcelle_id is None or valeur is None:
        print("[MQTT] Payload ignoré (attendu: parcelle_id et humidite).", flush=True)
        return

    db = SessionLocal()
    try:
        parcelle = db.query(Parcelle).filter(Parcelle.id == parcelle_id).first()
        if not parcelle:
            dispos = [(p.id, p.nom) for p in db.query(Parcelle).all()]
            print(f"[MQTT] Parcelle #{parcelle_id} introuvable. IDs en base : {dispos}", flush=True)
            return

        db.add(MesureHumidite(parcelle_id=parcelle_id, valeur=valeur))
        db.commit()
        print(f"[MQTT] Enregistré : {parcelle.nom} (#{parcelle_id}) -> {valeur} %", flush=True)

        # Règles d'alerte (sol sec / excès d'eau, anti-doublon, notifications) : module Alertes
        try:
            from ..features.alertes import service as alerte_service

            if alerte_service.verifier_humidite(db, parcelle, valeur):
                print(f"[MQTT] Alerte créée pour {parcelle.nom}.", flush=True)
        except Exception as err_alerte:
            db.rollback()
            print(f"[MQTT] Erreur création alerte : {err_alerte}", flush=True)
    except Exception as e:
        db.rollback()
        print(f"[MQTT] Erreur SQL : {e}", flush=True)
    finally:
        db.close()


def demarrer():
    global _client
    if _client is not None:
        return
    if not getattr(settings, "MQTT_ENABLED", True):
        return

    client_id = f"sevia-api-{uuid.uuid4().hex[:8]}"
    try:
        _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        _client = mqtt.Client(client_id=client_id)

    if getattr(settings, "MQTT_USERNAME", None):
        _client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

    _client.on_connect = on_connect
    _client.on_disconnect = on_disconnect
    _client.on_message = on_message

    _client.connect_async(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
    _client.loop_start()


def arreter():
    global _client
    if _client:
        _client.loop_stop()
        _client.disconnect()
        _client = None