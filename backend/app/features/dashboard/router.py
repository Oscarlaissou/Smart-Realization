"""CONTRÔLEUR – Tableau de bord (indicateurs clés). TODO : filtres période/parcelle/culture + export PDF/Excel/CSV."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from ..humidite.models import Mesure, Irrigation
from ..camera.models import Comptage
from ..fertilisation.models import Apport
from ..alertes.models import Alerte

router = APIRouter(prefix="/dashboard", tags=["Tableau de bord"], dependencies=[Depends(current_user)])

@router.get("/indicateurs")
def indicateurs(db: Session = Depends(get_db)):
    return {
        "humidite_moyenne": db.query(func.avg(Mesure.humidite)).scalar() or 0,
        "plants_comptes": db.query(func.sum(Comptage.nb_plants)).scalar() or 0,
        "apports_engrais": db.query(func.count(Apport.id)).filter(Apport.realise.is_(True)).scalar(),
        "alertes_actives": db.query(func.count(Alerte.id)).filter(Alerte.lue.is_(False)).scalar(),
        "irrigations": db.query(func.count(Irrigation.id)).scalar(),
    }
