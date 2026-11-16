"""Décision d'irrigation. Mode automatique : arroser si humidité < seuil min.
TODO (Aurelie/Emmanuelle) : publier la commande MQTT vers l'électrovanne."""
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Irrigation
from ..alertes.service import SEUIL_MIN

def doit_irriguer(humidite: float) -> bool:
    return humidite < SEUIL_MIN

def demarrer(db: Session, parcelle_id: int, duree_min: int, mode="manuel") -> Irrigation:
    irr = Irrigation(parcelle_id=parcelle_id, duree_min=duree_min, mode=mode, debut=datetime.utcnow())
    db.add(irr); db.commit(); db.refresh(irr)
    return irr
