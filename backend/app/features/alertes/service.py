"""Logique métier des alertes. TODO (équipe) : envoyer notification / SMS / e-mail."""
from sqlalchemy.orm import Session
from .models import Alerte
from ..parcelles.models import Parcelle

SEUIL_MIN, SEUIL_MAX = 30, 45

def verifier_humidite(db: Session, parcelle: Parcelle, humidite: float):
    if humidite < SEUIL_MIN:
        a = Alerte(parcelle_id=parcelle.id, niveau="urgent", message=f"Sol sec · {parcelle.nom} ({humidite:.0f} %)")
    elif humidite > SEUIL_MAX:
        a = Alerte(parcelle_id=parcelle.id, niveau="attention", message=f"Excès d'eau · {parcelle.nom} ({humidite:.0f} %)")
    else:
        return None
    db.add(a); db.commit()
    return a
