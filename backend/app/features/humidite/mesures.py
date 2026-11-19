"""Enregistrement d'une mesure d'humidité : point d'entrée UNIQUE (MQTT et API).

1. enregistre la mesure et marque les capteurs de la parcelle comme « vivants » ;
2. pousse AUSSITÔT la mesure aux pages ouvertes du propriétaire (événement « mesure ») ;
3. compare ensuite aux seuils de la parcelle et, si une alerte « Sol sec » / « Excès d'eau » est créée,
   la pousse dans un second événement (« alerte »).

Ordre choisi pour la réactivité : avec Supabase, chaque aller-retour vers la base coûte ~1 s depuis
le poste de développement. On limite donc les requêtes AVANT la diffusion (aucun refresh, une seule
mise à jour groupée des capteurs) et on fait la vérification des alertes APRÈS.
"""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from ...core import temps_reel
from ..alertes import service as alerte_service
from ..equipements.models import Equipement
from ..parcelles.models import Exploitation, Parcelle
from .models import MesureHumidite

log = logging.getLogger(__name__)


def enregistrer_mesure(db: Session, parcelle: Parcelle, valeur: float, user_id: int | None = None) -> dict:
    """user_id : propriétaire de la parcelle s'il est déjà connu (évite une requête)."""
    maintenant = datetime.utcnow()
    valeur = round(float(valeur), 1)

    # Tout ce dont l'événement a besoin est lu AVANT le commit (le commit « expire » les objets
    # et chaque accès suivant coûterait un aller-retour de plus vers Supabase).
    parcelle_id, nom = parcelle.id, parcelle.nom
    seuil_min, seuil_max = alerte_service.seuils_humidite(parcelle)
    if user_id is None and parcelle.exploitation_id:
        exploitation = db.get(Exploitation, parcelle.exploitation_id)
        user_id = exploitation.user_id if exploitation else None

    mesure = MesureHumidite(parcelle_id=parcelle_id, valeur=valeur, enregistre_le=maintenant)
    db.add(mesure)
    db.flush()                         # obtient l'identifiant de la mesure
    mesure_id = mesure.id
    # Statut « en ligne » des capteurs de la parcelle : une seule requête UPDATE
    db.query(Equipement).filter(
        Equipement.parcelle_id == parcelle_id, Equipement.type == "capteur"
    ).update({Equipement.derniere_donnee: maintenant}, synchronize_session=False)
    db.commit()

    hors_seuil = "bas" if valeur < seuil_min else "haut" if valeur > seuil_max else None
    evenement = {
        "type": "mesure",
        "parcelle_id": parcelle_id,
        "parcelle": nom,
        "mesure_id": mesure_id,
        "valeur": valeur,
        "date": maintenant.isoformat(),
        "seuil_min": seuil_min,
        "seuil_max": seuil_max,
        "hors_seuil": hors_seuil,          # "bas" | "haut" | None
        "alerte": None,
    }
    if user_id is not None:
        temps_reel.publier(user_id, evenement)   # la page se met à jour tout de suite

    # Seuils dépassés : alerte (anti-doublon, e-mail/SMS selon les préférences), APRÈS la diffusion
    if hors_seuil:
        try:
            alerte = alerte_service.verifier_humidite(db, parcelle, valeur)
        except Exception:   # une panne d'alerte ne doit jamais faire perdre la mesure
            db.rollback()
            log.exception("Vérification des seuils impossible pour la parcelle %s", parcelle_id)
            alerte = None
        if alerte:   # e-mail + popup en direct : envoyés par le service Alertes (creer_alerte)
            evenement["alerte"] = {"id": alerte.id, "niveau": alerte.niveau, "message": alerte.message}
    return evenement
