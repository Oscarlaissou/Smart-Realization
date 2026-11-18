"""Réception des mesures envoyées par les ESP32.
Topic attendu : sevia/parcelle/<id>/humidite   payload : {"humidite": 27.4}"""
import json, threading
import paho.mqtt.client as mqtt
from ..core.config import settings
from ..core.database import SessionLocal
from ..features.humidite.models import Mesure
from ..features.parcelles.models import Parcelle
from ..features.alertes import service as alerte_service

def _on_message(client, userdata, msg):
    try:
        pid = int(msg.topic.split("/")[2]); h = float(json.loads(msg.payload)["humidite"])
    except Exception:
        return
    db = SessionLocal()
    try:
        p = db.get(Parcelle, pid)
        if p:
            db.add(Mesure(parcelle_id=pid, humidite=h)); db.commit()
            alerte_service.verifier_humidite(db, p, h)
    finally:
        db.close()

def demarrer():
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.on_message = _on_message
    c.connect(settings.MQTT_BROKER, settings.MQTT_PORT)
    c.subscribe("sevia/parcelle/+/humidite")
    threading.Thread(target=c.loop_forever, daemon=True).start()
