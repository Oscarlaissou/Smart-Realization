"""CONTRÔLEUR – Humidité et irrigation (mesures, recommandations, cycles, journal)."""
from datetime import datetime, timedelta
import unicodedata
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from .models import Mesure, CycleIrrigation, Irrigation
from ..parcelles.models import Parcelle
from ..alertes.models import Alerte
from .schemas import *
from ..alertes import service as alerte_service
from . import service as irrigation_service

router = APIRouter(prefix="/humidite", tags=["Humidité et irrigation"])

COEFFICIENTS_CULTURES = {
    "tomate": 1.15,
    "plantain": 1.20,
    "banane": 1.20,
    "mais": 1.05,
    "manioc": 0.85,
}


def _normaliser(texte: str) -> str:
    sans_accent = "".join(
        c for c in unicodedata.normalize("NFD", texte or "")
        if unicodedata.category(c) != "Mn"
    )
    return sans_accent.lower().strip()


@router.get("/contexte")
def contexte_humidite(db: Session = Depends(get_db), user=Depends(current_user)):
    alertes_actives = db.query(func.count(Alerte.id)).filter(Alerte.lue.is_(False)).scalar() or 0
    return {
        "utilisateur": {
            "nom": getattr(user, "nom", None) or getattr(user, "email", "Exploitant"),
            "role": getattr(user, "role", None) or "Exploitant",
        },
        "alertes_actives": int(alertes_actives),
    }


@router.get("/parcelles", dependencies=[Depends(current_user)])
def lister_parcelles(db: Session = Depends(get_db)):
    parcelles = db.query(Parcelle).order_by(Parcelle.id.asc()).all()
    return [
        {
            "id": p.id,
            "nom": p.nom,
            "surface_ha": float(p.surface_ha or 0),
            "culture": ", ".join(c.espece for c in p.cultures) if p.cultures else "Culture non définie",
        }
        for p in parcelles
    ]


@router.get("/recommandations/{pid}", dependencies=[Depends(current_user)])
def recommandations_parcelle(
    pid: int,
    seuil_min: float = Query(30.0, ge=5, le=80),
    seuil_max: float = Query(45.0, ge=10, le=95),
    db: Session = Depends(get_db),
):
    parcelle = db.get(Parcelle, pid)
    if not parcelle:
        raise HTTPException(404, "Parcelle introuvable")

    espece = parcelle.cultures[0].espece if parcelle.cultures else "Culture générale"
    cle_culture = _normaliser(espece)
    coeff_culture = next(
        (coef for nom, coef in COEFFICIENTS_CULTURES.items() if nom in cle_culture),
        1.0,
    )

    # Surface en m² (valeur par défaut 2 500 m² si non renseignée en base)
    surface_ha = float(parcelle.surface_ha) if parcelle.surface_ha and parcelle.surface_ha > 0 else 0.25
    surface_m2 = surface_ha * 10_000

    mesures = (
        db.query(Mesure)
        .filter(Mesure.parcelle_id == pid)
        .order_by(Mesure.horodatage.desc())
        .limit(12)
        .all()
    )
    humidite_actuelle = float(mesures[0].humidite) if mesures else 0.0
    cible_optimale = (seuil_min + seuil_max) / 2.0

    # 1. Calcul du besoin en eau (Litres, m³, dose au m² et durée estimée)
    if humidite_actuelle < seuil_min:
        deficit_pct = max(0.0, cible_optimale - humidite_actuelle)
        dose_l_m2 = round(deficit_pct * 0.25 * coeff_culture, 1)
        volume_litres = int(round(dose_l_m2 * surface_m2))
        volume_m3 = round(volume_litres / 1000.0, 2)
        duree_estimee_min = max(5, int(round(volume_litres / 60.0)))
        niveau_urgence = "urgent"
        badge_urgence = "Apport recommandé"
        conseil_culture = (
            f"Déficit hydrique détecté sur {espece}. Apporter {volume_litres:,} L "
            f"en 2 passages espacés pour favoriser l'infiltration racinaire sans ruissellement."
        ).replace(",", " ")
    elif humidite_actuelle <= seuil_max:
        dose_l_m2 = 0.0
        volume_litres = 0
        volume_m3 = 0.0
        duree_estimee_min = 0
        niveau_urgence = "optimal"
        badge_urgence = "Parcelle autonome"
        conseil_culture = (
            f"Réserve en eau idéale pour {espece}. Aucun arrosage nécessaire : "
            f"maintenir le paillage au pied pour limiter l'évaporation."
        )
    else:
        dose_l_m2 = 0.0
        volume_litres = 0
        volume_m3 = 0.0
        duree_estimee_min = 0
        niveau_urgence = "exces"
        badge_urgence = "Suspendre l'apport"
        conseil_culture = (
            f"Humidité supérieure au seuil haut pour {espece}. Suspendre tout apport "
            f"pendant 24 à 48 h et vérifier le drainage pour éviter l'asphyxie racinaire."
        )

    # 2. Tendance d'assèchement et autonomie hydrique restante
    taux_horaire = -0.5
    if len(mesures) >= 2:
        delta_h = float(mesures[0].humidite) - float(mesures[-1].humidite)
        heures = (mesures[0].horodatage - mesures[-1].horodatage).total_seconds() / 3600.0
        if heures >= 0.5 and delta_h < -0.1:
            taux_horaire = round(delta_h / heures, 2)

    if humidite_actuelle <= seuil_min:
        autonomie_titre = "Seuil critique atteint"
        autonomie_detail = f"Humidité actuelle ({round(humidite_actuelle)} %) sous le minimum de {int(seuil_min)} %"
    else:
        heures_restantes = round((humidite_actuelle - seuil_min) / abs(taux_horaire), 1)
        autonomie_titre = f"~{heures_restantes} h d'autonomie"
        autonomie_detail = f"Variation estimée : {taux_horaire} % / heure avant le seuil de {int(seuil_min)} %"

    # 3. Fenêtre horaire conseillée
    heure_locale = datetime.now().hour
    if 11 <= heure_locale <= 16:
        fenetre_horaire = "Éviter le plein soleil · Privilégier ce soir (18h00 – 20h00)"
    elif 5 <= heure_locale <= 8:
        fenetre_horaire = "Créneau idéal en cours (05h30 – 08h30) : évaporation minimale"
    else:
        fenetre_horaire = "Créneau optimal : tôt demain (05h30 – 07h30) ou en soirée (après 18h00)"

    # 4. Bilan hydrique des 7 derniers jours (pour le journal)
    il_y_a_7j = datetime.utcnow() - timedelta(days=7)
    irrigations_7j = db.query(Irrigation).filter(Irrigation.debut >= il_y_a_7j).all()
    volume_7j_litres = sum((irr.duree_min or 0) * 60 for irr in irrigations_7j)

    return {
        "parcelle_id": pid,
        "espece": espece,
        "surface_ha": surface_ha,
        "volume_litres": volume_litres,
        "volume_m3": volume_m3,
        "dose_l_m2": dose_l_m2,
        "duree_estimee_min": duree_estimee_min,
        "niveau_urgence": niveau_urgence,
        "badge_urgence": badge_urgence,
        "autonomie_titre": autonomie_titre,
        "autonomie_detail": autonomie_detail,
        "fenetre_horaire": fenetre_horaire,
        "conseil_culture": conseil_culture,
        "bilan_hebdo": {
            "volume_litres": volume_7j_litres,
            "nb_apports": len(irrigations_7j),
            "economie_estimee_pct": 18,
        },
    }


@router.post("/mesures", response_model=MesureOut, status_code=201)
def recevoir_mesure(d: MesureIn, db: Session = Depends(get_db)):
    p = db.get(Parcelle, d.parcelle_id)
    if not p:
        raise HTTPException(404, "Parcelle introuvable")
    m = Mesure(**d.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    alerte_service.verifier_humidite(db, p, d.humidite)
    if irrigation_service.doit_irriguer(d.humidite):
        irrigation_service.demarrer(db, p.id, duree_min=30, mode="automatique")
    return m


@router.get("/mesures/{pid}", response_model=list[MesureOut], dependencies=[Depends(current_user)])
def historique(pid: int, limite: int = 100, db: Session = Depends(get_db)):
    return db.query(Mesure).filter_by(parcelle_id=pid).order_by(Mesure.horodatage.desc()).limit(limite).all()


@router.get("/irrigations", response_model=list[IrrigationOut], dependencies=[Depends(current_user)])
def journal(db: Session = Depends(get_db)):
    return db.query(Irrigation).order_by(Irrigation.debut.desc()).limit(200).all()


@router.get("/cycles", response_model=list[CycleOut], dependencies=[Depends(current_user)])
def lister_cycles(db: Session = Depends(get_db)):
    return db.query(CycleIrrigation).order_by(CycleIrrigation.id.asc()).all()


@router.post("/cycles", response_model=CycleOut, status_code=201, dependencies=[Depends(current_user)])
def programmer_cycle(d: CycleIn, db: Session = Depends(get_db)):
    parcelle = db.get(Parcelle, d.parcelle_id)
    if not parcelle:
        raise HTTPException(404, "Parcelle introuvable")

    heure_propre = d.heure.strip()[:5]
    if len(heure_propre) != 5 or ":" not in heure_propre:
        raise HTTPException(400, "Format d'heure invalide (attendu HH:MM)")

    c = CycleIrrigation(
        parcelle_id=d.parcelle_id,
        heure=heure_propre,
        duree_min=max(1, d.duree_min),
        jours=d.jours.strip() or "Tous les jours",
        actif=d.actif,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.patch("/cycles/{cid}", response_model=CycleOut, dependencies=[Depends(current_user)])
def basculer_cycle(cid: int, db: Session = Depends(get_db)):
    c = db.get(CycleIrrigation, cid)
    if not c:
        raise HTTPException(404, "Cycle introuvable")
    c.actif = not c.actif
    db.commit()
    db.refresh(c)
    return c


@router.delete("/cycles/{cid}", status_code=204, dependencies=[Depends(current_user)])
def supprimer_cycle(cid: int, db: Session = Depends(get_db)):
    c = db.get(CycleIrrigation, cid)
    if not c:
        raise HTTPException(404, "Cycle introuvable")
    db.delete(c)
    db.commit()