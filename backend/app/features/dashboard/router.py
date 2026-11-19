"""CONTRÔLEUR – Tableau de bord (indicateurs clés). Filtres période/parcelle/culture + export CSV/Excel."""
from datetime import datetime, timedelta
import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from ..parcelles.models import Exploitation, Parcelle, Culture
from ..equipements.models import Equipement
from ..equipements.router import statut_en_ligne
from ..alertes.service import seuils_humidite
from ..humidite.models import Mesure, Irrigation
from ..camera.models import Comptage
from ..fertilisation.models import Apport
from ..alertes.models import Alerte

router = APIRouter(prefix="/dashboard", tags=["Tableau de bord"], dependencies=[Depends(current_user)])


def _date_debut(periode: str):
    maintenant = datetime.utcnow()
    if periode == "7 derniers jours":
        return maintenant - timedelta(days=7)
    if periode == "30 derniers jours":
        return maintenant - timedelta(days=30)
    return None


def _ids_exploitations(db: Session, user) -> list[int]:
    return [e.id for e in db.query(Exploitation.id).filter(Exploitation.user_id == user.id).all()]


def _parcelles_filtrees(db: Session, user, parcelle: str | None, culture: str | None):
    # Uniquement les parcelles de l'utilisateur connecté
    q = db.query(Parcelle).filter(Parcelle.exploitation_id.in_(_ids_exploitations(db, user)))
    if parcelle and parcelle != "Toutes les parcelles":
        q = q.filter(Parcelle.nom == parcelle)
    if culture and culture != "Toutes les cultures":
        q = q.filter(Parcelle.cultures.any(Culture.espece == culture))
    parcelles = q.all()
    return parcelles, [p.id for p in parcelles]


def _litres_irrigation(irr) -> float:
    vol = getattr(irr, "volume_litres", None)
    if vol is not None and float(vol) > 0:
        return float(vol)
    return float(getattr(irr, "duree_minutes", 0) or 0) * 60.0


@router.get("/indicateurs")
def indicateurs(
    periode: str = Query("30 derniers jours"),
    parcelle: str | None = Query(None),
    culture: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    date_min = _date_debut(periode)
    parcelles_obj, p_ids = _parcelles_filtrees(db, user, parcelle, culture)

    if not p_ids:
        return {
            "humidite_moyenne": 0,
            "plants_comptes": 0,
            "apports_engrais": 0,
            "alertes_actives": 0,
            "irrigations": 0,
            "eau_m3": 0,
            "parcelles": [],
            "alertes": [],
            "evolution": {"Eau": [], "Humidité": [], "Plants": [], "Engrais": []},
        }

    # 1. Requêtes KPI filtrées
    q_mesures = db.query(func.avg(Mesure.valeur)).filter(Mesure.parcelle_id.in_(p_ids))
    q_comptages = db.query(func.sum(Comptage.nb_plants)).filter(Comptage.parcelle_id.in_(p_ids))
    q_apports = db.query(func.count(Apport.id)).filter(Apport.parcelle_id.in_(p_ids), Apport.realise.is_(True))
    q_alertes = db.query(func.count(Alerte.id)).filter(Alerte.parcelle_id.in_(p_ids), Alerte.lue.is_(False))
    q_irrig = db.query(Irrigation).filter(Irrigation.parcelle_id.in_(p_ids))

    if date_min:
        q_mesures = q_mesures.filter(Mesure.enregistre_le >= date_min)
        q_comptages = q_comptages.filter(Comptage.date >= date_min)
        q_apports = q_apports.filter(Apport.date >= date_min)
        q_alertes = q_alertes.filter(Alerte.date >= date_min)
        q_irrig = q_irrig.filter(Irrigation.date_arrosage >= date_min)

    humidite_moy = q_mesures.scalar() or 0
    plants_comptes = q_comptages.scalar() or 0
    apports_engrais = q_apports.scalar() or 0
    alertes_actives = q_alertes.scalar() or 0

    liste_irrigations = q_irrig.order_by(Irrigation.date_arrosage.asc()).all()
    irrigations = len(liste_irrigations)
    total_litres = sum(_litres_irrigation(irr) for irr in liste_irrigations)
    eau_m3 = round(total_litres / 1000.0, 2)

    # 2. Détail par parcelle
    liste_parcelles = []
    for p in parcelles_obj:
        derniere = (
            db.query(Mesure.valeur)
            .filter(Mesure.parcelle_id == p.id)
            .order_by(Mesure.enregistre_le.desc())
            .first()
        )
        hum_p = round(float(derniere[0]), 1) if derniere else 0

        litres_p = sum(_litres_irrigation(irr) for irr in liste_irrigations if irr.parcelle_id == p.id)
        eau_p_m3 = round(litres_p / 1000.0, 2)

        seuil_min, seuil_max = seuils_humidite(p)

        if hum_p < seuil_min:
            statut = "Irrigation"
        elif hum_p > seuil_max:
            statut = "Trop humide"
        else:
            statut = "Optimal"

        liste_parcelles.append({
            "id": p.id,
            "nom": p.nom,
            "culture": ", ".join(c.espece for c in p.cultures) if p.cultures else "—",
            "statut": statut,
            "humidite": hum_p,
            "eau_m3": eau_p_m3,
        })

    # 3. Dernières alertes
    q_liste_alertes = db.query(Alerte).filter(Alerte.parcelle_id.in_(p_ids), Alerte.lue.is_(False))
    if date_min:
        q_liste_alertes = q_liste_alertes.filter(Alerte.date >= date_min)

    alertes_db = q_liste_alertes.order_by(Alerte.date.desc()).limit(5).all()
    liste_alertes = [
        {
            "id": a.id,
            "niveau": a.niveau,
            "titre": a.message,
            "detail": a.date.strftime("%d/%m %H:%M") if a.date else "",
        }
        for a in alertes_db
    ]

    # 4. Équipements en ligne
    # Équipements de l'utilisateur, statut calculé comme sur la page Équipements
    equipements_user = (
        db.query(Equipement).filter(Equipement.exploitation_id.in_(_ids_exploitations(db, user))).all()
    )
    total_eq = len(equipements_user)
    en_ligne_eq = sum(1 for e in equipements_user if statut_en_ligne(e))

    # 5. Courbes d'évolution (Humidité MQTT & Eau apportée en m³)
    q_courbe = db.query(Mesure).filter(Mesure.parcelle_id.in_(p_ids))
    if date_min:
        q_courbe = q_courbe.filter(Mesure.enregistre_le >= date_min)
    mesures_courbe = q_courbe.order_by(Mesure.enregistre_le.desc()).limit(11).all()[::-1]

    serie_humidite = [
        {"date": m.enregistre_le.strftime("%d %b"), "valeur": round(float(m.valeur), 1)}
        for m in mesures_courbe
    ]

    serie_eau = [
        {
            "date": irr.date_arrosage.strftime("%d %b") if irr.date_arrosage else "—",
            "valeur": round(_litres_irrigation(irr) / 1000.0, 2),
        }
        for irr in liste_irrigations[-11:]
    ]

    return {
        "humidite_moyenne": round(float(humidite_moy), 1),
        "plants_comptes": int(plants_comptes),
        "apports_engrais": int(apports_engrais),
        "alertes_actives": int(alertes_actives),
        "irrigations": int(irrigations),
        "eau_m3": eau_m3,
        "domaine": {
            "nom": "Domaine Les Collines",
            "nb_parcelles": len(parcelles_obj),
            "equipements_en_ligne": en_ligne_eq,
            "equipements_total": total_eq,
        },
        "utilisateur": {
            "nom": getattr(user, "nom", "Exploitant"),
            "role": "Exploitant",
        },
        "parcelles": liste_parcelles,
        "alertes": liste_alertes,
        "evolution": {
            "Eau": serie_eau,
            "Humidité": serie_humidite,
            "Plants": serie_humidite,
            "Engrais": serie_humidite,
        },
    }


@router.get("/export")
def exporter_dashboard(
    format: str = Query("csv"),
    periode: str = Query("30 derniers jours"),
    parcelle: str | None = Query(None),
    culture: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    data = indicateurs(periode=periode, parcelle=parcelle, culture=culture, db=db, user=user)

    tampon = io.StringIO()
    tampon.write("\ufeff")
    writer = csv.writer(tampon, delimiter=";")
    writer.writerow(["Parcelle", "Culture", "Statut", "Humidite (%)", "Eau (m3)"])
    for p in data["parcelles"]:
        writer.writerow([p["nom"], p["culture"], p["statut"], p["humidite"], p["eau_m3"]])

    extension = "csv" if format.lower() == "csv" else "xls"
    return StreamingResponse(
        iter([tampon.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="sevia-dashboard.{extension}"'},
    )