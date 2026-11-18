"""Réception des mesures envoyées par les ESP32.
Topic attendu : sevia/parcelle/<id>/humidite   payload : {"humidite": 27.4}"""
import json, threading
from datetime import datetime
import paho.mqtt.client as mqtt
from ..core.config import settings
from ..core.database import SessionLocal
from ..features.humidite.models import Mesure
from ..features.parcelles.models import Parcelle
from ..features.equipements.models import Equipement
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

            # Marque comme "vivants" les capteurs de cette parcelle : on ne
            # sait pas encore (le payload ne le dit pas) lequel précisément
            # a envoyé la mesure, donc on met à jour tous les capteurs
            # associés à la parcelle. Suffisant tant qu'il y en a un seul
            # par parcelle pendant les tests.
            capteurs = (
                db.query(Equipement)
                .filter(Equipement.parcelle_id == pid, Equipement.type == "capteur")
                .all()
            )
            for c in capteurs:
                c.derniere_donnee = datetime.utcnow()
            if capteurs:
                db.commit()
    finally:
        db.close()

def demarrer():
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.on_message = _on_message
    c.connect(settings.MQTT_HOST, settings.MQTT_PORT)
    c.subscribe("sevia/parcelle/+/humidite")
    threading.Thread(target=c.loop_forever, daemon=True).start()