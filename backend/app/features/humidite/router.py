import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ...core import temps_reel
from ...core.database import SessionLocal, get_db
from ...core.security import bearer_scheme, current_user
from ..auth.models import User
from ..parcelles.models import Parcelle, Exploitation
from .models import MesureHumidite, ArrosageManuel
from ..alertes.service import seuils_humidite
from ...core.acces import parcelle_de, parcelles_de
from .mesures import enregistrer_mesure

router = APIRouter(prefix="/humidite", tags=["Humidité & Irrigation"])


class ArrosageIn(BaseModel):
    parcelle_id: int
    methode: str = "Goutte-à-goutte"
    volume_litres: float = 0.0
    duree_minutes: int = 0
    notes: str = ""


class SeuilsIn(BaseModel):
    seuil_humidite_min: float
    seuil_humidite_max: float


def _calculer_recommandation(
    humidite: float | None,
    min_s: float,
    max_s: float,
    surface_m2: float,
    culture: str = "",
) -> dict:
    fenetre = "Tôt le matin (05h30 – 07h30) ou en soirée après 18h00"
    conseil_culture = (
        f"Culture ({culture}) : maintenir l'humidité entre {round(min_s)} % et {round(max_s)} % pour éviter le stress hydrique."
        if culture
        else f"Maintenir l'humidité du sol entre {round(min_s)} % et {round(max_s)} %."
    )

    if humidite is None:
        return {
            "statut": "en_attente",
            "niveau_urgence": "optimal",
            "badge_urgence": "En attente MQTT",
            "volume_conseille_litres": 0,
            "volume_m3": 0.0,
            "dose_l_m2": 0.0,
            "duree_estimee_min": 0,
            "autonomie_titre": "En attente de sonde",
            "autonomie_detail": "Aucune mesure MQTT reçue pour cette parcelle.",
            "fenetre_horaire": fenetre,
            "conseil_culture": conseil_culture,
            "conseil": "En attente d'une première mesure capteur.",
        }

    cible = (min_s + max_s) / 2
    if humidite < min_s:
        deficit = max(0.0, cible - humidite)
        # Estimation : ~0.15 L par m² et par point de pourcentage manquant
        volume = max(10, round(surface_m2 * deficit * 0.15))
        dose = round(volume / max(surface_m2, 1.0), 2)
        # Débit moyen estimé à 12 L/min pour la durée indicative
        duree = max(5, round(volume / 12))
        return {
            "statut": "critique",
            "niveau_urgence": "urgent",
            "badge_urgence": "Arrosage requis",
            "volume_conseille_litres": volume,
            "volume_m3": round(volume / 1000, 2),
            "dose_l_m2": dose,
            "duree_estimee_min": duree,
            "autonomie_titre": "Déficit hydrique détecté",
            "autonomie_detail": f"Seuil minimal ({round(min_s)} %) franchi. Intervention recommandée aujourd'hui.",
            "fenetre_horaire": fenetre,
            "conseil_culture": conseil_culture,
            "conseil": f"Sol sec ({humidite}%). Arrosage conseillé : ~{volume} L pour atteindre {round(cible)}%.",
        }

    if humidite < cible:
        heures_estimees = max(6, round((humidite - min_s) * 3))
        return {
            "statut": "a_surveiller",
            "niveau_urgence": "optimal",
            "badge_urgence": "À surveiller",
            "volume_conseille_litres": 0,
            "volume_m3": 0.0,
            "dose_l_m2": 0.0,
            "duree_estimee_min": 0,
            "autonomie_titre": f"Autonomie estimée : ~{heures_estimees} h",
            "autonomie_detail": f"Réserve correcte avant d'atteindre le seuil d'alerte de {round(min_s)} %.",
            "fenetre_horaire": fenetre,
            "conseil_culture": conseil_culture,
            "conseil": f"Humidité correcte ({humidite}%), surveiller l'évolution.",
        }

    if humidite <= max_s:
        heures_estimees = max(12, round((humidite - min_s) * 3.5))
        return {
            "statut": "optimal",
            "niveau_urgence": "optimal",
            "badge_urgence": "Plage optimale",
            "volume_conseille_litres": 0,
            "volume_m3": 0.0,
            "dose_l_m2": 0.0,
            "duree_estimee_min": 0,
            "autonomie_titre": f"Autonomie estimée : ~{heures_estimees} h",
            "autonomie_detail": "Aucune irrigation nécessaire pour le moment.",
            "fenetre_horaire": fenetre,
            "conseil_culture": conseil_culture,
            "conseil": f"Humidité optimale ({humidite}%). Aucun arrosage requis.",
        }

    return {
        "statut": "sature",
        "niveau_urgence": "exces",
        "badge_urgence": "Sol saturé",
        "volume_conseille_litres": 0,
        "volume_m3": 0.0,
        "dose_l_m2": 0.0,
        "duree_estimee_min": 0,
        "autonomie_titre": "Réserve maximale atteinte",
        "autonomie_detail": f"Humidité supérieure au seuil maximal ({round(max_s)} %). Suspendre tout apport.",
        "fenetre_horaire": "Suspendre l'arrosage jusqu'au retour sous le seuil maximal",
        "conseil_culture": conseil_culture,
        "conseil": f"Sol très humide ({humidite}%). Suspendre tout arrosage.",
    }


@router.get("/apercu")
def apercu_humidite(db: Session = Depends(get_db), user: User = Depends(current_user)):
    # Uniquement les parcelles de l'utilisateur (plus de repli sur toutes les parcelles de la base)
    parcelles = parcelles_de(db, user)

    depuis_24h = datetime.utcnow() - timedelta(hours=24)
    depuis_7j = datetime.utcnow() - timedelta(days=7)
    cartes = []

    for p in parcelles:
        derniere = (
            db.query(MesureHumidite)
            .filter(MesureHumidite.parcelle_id == p.id)
            .order_by(MesureHumidite.enregistre_le.desc())
            .first()
        )
        historique = (
            db.query(MesureHumidite)
            .filter(MesureHumidite.parcelle_id == p.id, MesureHumidite.enregistre_le >= depuis_24h)
            .order_by(MesureHumidite.enregistre_le.asc())
            .all()
        )

        val = derniere.valeur if derniere else None
        min_s, max_s = seuils_humidite(p)
        surf = getattr(p, "surface_m2", None) or ((getattr(p, "surface_ha", 0) or 0) * 10000) or 100.0

        cultures_rel = getattr(p, "cultures", None)
        if cultures_rel:
            culture = ", ".join(c.espece for c in cultures_rel if getattr(c, "espece", None))
        else:
            culture = getattr(p, "culture", "") or ""

        reco = _calculer_recommandation(val, min_s, max_s, surf, culture)

        cartes.append({
            "id": p.id,
            "nom": p.nom,
            "culture": culture,
            "surface_m2": surf,
            "humidite_actuelle": val,
            "derniere_mesure_le": derniere.enregistre_le.isoformat() if derniere else None,
            "seuil_min": min_s,
            "seuil_max": max_s,
            **reco,
            "courbe_24h": [
                {
                    "id": m.id,
                    "heure": m.enregistre_le.strftime("%H:%M"),
                    "horodatage": m.enregistre_le.isoformat(),
                    "valeur": m.valeur,
                }
                for m in historique
            ],
        })

    parcelle_ids = [p.id for p in parcelles]
    arrosages = (
        db.query(ArrosageManuel)
        .filter(ArrosageManuel.parcelle_id.in_(parcelle_ids))
        .order_by(ArrosageManuel.date_arrosage.desc())
        .limit(50)
        .all()
        if parcelle_ids
        else []
    )

    arrosages_7j = [a for a in arrosages if a.date_arrosage and a.date_arrosage >= depuis_7j]
    volume_7j = round(sum(float(a.volume_litres or 0) for a in arrosages_7j))
    noms_parcelles = {p.id: p.nom for p in parcelles}

    # Comptage sécurisé des alertes actives
    alertes_actives = 0
    try:
        from ..alertes.models import Alerte
        if parcelle_ids:
            alertes_actives = (
                db.query(Alerte)
                .filter(Alerte.parcelle_id.in_(parcelle_ids), Alerte.lue == False)  # noqa: E712
                .count()
            )
    except Exception:
        alertes_actives = 0

    return {
        "utilisateur": {"nom": user.nom, "role": user.role},
        "alertes_actives": alertes_actives,
        "bilan_hebdo": {
            "volume_litres": volume_7j,
            "nb_apports": len(arrosages_7j),
            "economie_estimee_pct": 28 if arrosages_7j else 0,
        },
        "parcelles": cartes,
        "arrosages": [
            {
                "id": a.id,
                "parcelle_id": a.parcelle_id,
                "parcelle": noms_parcelles.get(a.parcelle_id, f"Parcelle #{a.parcelle_id}"),
                "methode": a.methode,
                "volume_litres": a.volume_litres,
                "duree_minutes": a.duree_minutes,
                "humidite_avant": a.humidite_avant,
                "notes": a.notes,
                "date_arrosage": a.date_arrosage.isoformat() if a.date_arrosage else None,
            }
            for a in arrosages
        ],
    }


@router.post("/arrosages", status_code=201)
def declarer_arrosage(donnees: ArrosageIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    parcelle_de(db, donnees.parcelle_id, user)
    derniere = (
        db.query(MesureHumidite)
        .filter(MesureHumidite.parcelle_id == donnees.parcelle_id)
        .order_by(MesureHumidite.enregistre_le.desc())
        .first()
    )
    arrosage = ArrosageManuel(
        parcelle_id=donnees.parcelle_id,
        user_id=user.id,
        methode=donnees.methode,
        volume_litres=donnees.volume_litres,
        duree_minutes=donnees.duree_minutes,
        humidite_avant=derniere.valeur if derniere else None,
        notes=donnees.notes,
    )
    db.add(arrosage)
    db.commit()
    db.refresh(arrosage)
    return {"id": arrosage.id, "message": "Arrosage enregistré avec succès."}


@router.patch("/parcelles/{parcelle_id}/seuils")
def modifier_seuils(parcelle_id: int, donnees: SeuilsIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    parcelle = parcelle_de(db, parcelle_id, user)
    if donnees.seuil_humidite_min >= donnees.seuil_humidite_max:
        raise HTTPException(400, "Le seuil minimal doit être inférieur au seuil maximal.")

    parcelle.seuil_humidite_min = donnees.seuil_humidite_min
    parcelle.seuil_humidite_max = donnees.seuil_humidite_max
    db.commit()
    return {"message": "Seuils mis à jour."}

# ---------------------------------------------------------------------------
# Mesures en temps réel
# ---------------------------------------------------------------------------
class MesureIn(BaseModel):
    parcelle_id: int
    humidite: float = Field(ge=0, le=100)


@router.post("/mesures", status_code=201)
def recevoir_mesure(donnees: MesureIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Envoi d'une mesure par l'API (test sans capteur, passerelle). Même traitement que MQTT :
    enregistrement, alertes de seuil haut/bas et diffusion immédiate aux pages ouvertes."""
    parcelle = parcelle_de(db, donnees.parcelle_id, user)
    return enregistrer_mesure(db, parcelle, donnees.humidite)


@router.get("/flux")
async def flux_mesures(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """Flux Server-Sent Events : chaque nouvelle mesure d'une parcelle de l'utilisateur est poussée
    immédiatement (événement « mesure »), avec l'alerte éventuelle. Un commentaire « ping » part
    toutes les 15 s pour garder la connexion ouverte.

    Pas de Depends(get_db) ici : la session serait gardée ouverte pendant toute la durée du flux."""
    db = SessionLocal()
    try:
        user_id = current_user(credentials, db).id
    finally:
        db.close()

    abonne = temps_reel.abonner(user_id)

    async def evenements():
        try:
            yield "retry: 3000\n\n"
            silence = 0
            # Vérifié chaque seconde : page fermée ? serveur en cours d'arrêt (Ctrl+C, --reload) ?
            while not temps_reel.ARRET.is_set() and not await request.is_disconnected():
                try:
                    message = await asyncio.wait_for(abonne.file.get(), timeout=1)
                    silence = 0
                    yield f"event: mesure\ndata: {message}\n\n"
                except asyncio.TimeoutError:
                    silence += 1
                    if silence >= 15:          # garde la connexion ouverte (proxys, navigateurs)
                        silence = 0
                        yield ": ping\n\n"
        finally:
            temps_reel.desabonner(abonne)

    return StreamingResponse(
        evenements(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
