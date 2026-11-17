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
from ..parcelles.models import Parcelle
from ..equipements.models import Equipement
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


def _parcelles_filtrees(db: Session, parcelle: str | None, culture: str | None):
    q = db.query(Parcelle)
    if parcelle and parcelle != "Toutes les parcelles":
        q = q.filter(Parcelle.nom == parcelle)
    if culture and culture != "Toutes les cultures" and hasattr(Parcelle, "culture"):
        q = q.filter(Parcelle.culture == culture)
    parcelles = q.all()
    return parcelles, [p.id for p in parcelles]


@router.get("/indicateurs")
def indicateurs(
    periode: str = Query("30 derniers jours"),
    parcelle: str | None = Query(None),
    culture: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(current_user),
):
    date_min = _date_debut(periode)
    parcelles_obj, p_ids = _parcelles_filtrees(db, parcelle, culture)

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

    # 1. Requêtes KPI filtrées avec les colonnes exactes
    q_mesures = db.query(func.avg(Mesure.humidite)).filter(Mesure.parcelle_id.in_(p_ids))
    q_comptages = db.query(func.sum(Comptage.nb_plants)).filter(Comptage.parcelle_id.in_(p_ids))
    q_apports = db.query(func.count(Apport.id)).filter(Apport.parcelle_id.in_(p_ids), Apport.realise.is_(True))
    q_alertes = db.query(func.count(Alerte.id)).filter(Alerte.parcelle_id.in_(p_ids), Alerte.lue.is_(False))
    q_irrig_nb = db.query(func.count(Irrigation.id)).filter(Irrigation.parcelle_id.in_(p_ids))
    q_irrig_vol = db.query(func.sum(Irrigation.duree_min)).filter(Irrigation.parcelle_id.in_(p_ids))

    if date_min:
        q_mesures = q_mesures.filter(Mesure.horodatage >= date_min)
        q_comptages = q_comptages.filter(Comptage.date >= date_min)
        q_apports = q_apports.filter(Apport.date >= date_min)
        q_alertes = q_alertes.filter(Alerte.date >= date_min)
        q_irrig_nb = q_irrig_nb.filter(Irrigation.debut >= date_min)
        q_irrig_vol = q_irrig_vol.filter(Irrigation.debut >= date_min)

    humidite_moy = q_mesures.scalar() or 0
    plants_comptes = q_comptages.scalar() or 0
    apports_engrais = q_apports.scalar() or 0
    alertes_actives = q_alertes.scalar() or 0
    irrigations = q_irrig_nb.scalar() or 0
    eau_m3 = q_irrig_vol.scalar() or 0

    # 2. Détail par parcelle
    liste_parcelles = []
    for p in parcelles_obj:
        derniere = (
            db.query(Mesure.humidite)
            .filter(Mesure.parcelle_id == p.id)
            .order_by(Mesure.horodatage.desc())
            .first()
        )
        hum_p = round(float(derniere[0]), 1) if derniere else 0

        q_eau_p = db.query(func.sum(Irrigation.duree_min)).filter(Irrigation.parcelle_id == p.id)
        if date_min:
            q_eau_p = q_eau_p.filter(Irrigation.debut >= date_min)
        eau_p = q_eau_p.scalar() or 0

        if hum_p < 30:
            statut = "Irrigation"
        elif hum_p > 45:
            statut = "Trop humide"
        else:
            statut = "Optimal"

        liste_parcelles.append({
            "id": p.id,
            "nom": p.nom,
            "culture": getattr(p, "culture", "—") or "—",
            "statut": statut,
            "humidite": hum_p,
            "eau_m3": round(float(eau_p), 1),
        })

    # 3. Dernières alertes (colonne Alerte.message)
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
    total_eq = db.query(func.count(Equipement.id)).scalar() or 0
    en_ligne_eq = db.query(func.count(Equipement.id)).filter(Equipement.en_ligne.is_(True)).scalar() or 0

    # 5. Courbe d'évolution (colonne Mesure.horodatage)
    q_courbe = db.query(Mesure).filter(Mesure.parcelle_id.in_(p_ids))
    if date_min:
        q_courbe = q_courbe.filter(Mesure.horodatage >= date_min)
    mesures_courbe = q_courbe.order_by(Mesure.horodatage.desc()).limit(11).all()[::-1]

    serie_humidite = [
        {"date": m.horodatage.strftime("%d %b"), "valeur": round(float(m.humidite), 1)}
        for m in mesures_courbe
    ]

    return {
        "humidite_moyenne": round(float(humidite_moy), 1),
        "plants_comptes": int(plants_comptes),
        "apports_engrais": int(apports_engrais),
        "alertes_actives": int(alertes_actives),
        "irrigations": int(irrigations),
        "eau_m3": round(float(eau_m3), 1),
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
            "Eau": serie_humidite,
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