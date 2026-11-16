"""CONTRÔLEUR – Caméra (images, comptage, évolution, comparaison par date)."""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.security import current_user
from .models import Comptage
from .schemas import ComptageOut
from . import service as comptage_service

router = APIRouter(prefix="/camera", tags=["Caméra"], dependencies=[Depends(current_user)])

@router.post("/{pid}/images", response_model=ComptageOut, status_code=201)
async def recevoir_image(pid: int, fichier: UploadFile = File(...), db: Session = Depends(get_db)):
    n = comptage_service.compter_plants(await fichier.read())
    c = Comptage(parcelle_id=pid, nb_plants=n, image_path=fichier.filename or "")
    db.add(c); db.commit(); db.refresh(c); return c

@router.get("/{pid}/comptages", response_model=list[ComptageOut])
def evolution(pid: int, db: Session = Depends(get_db)):
    return db.query(Comptage).filter_by(parcelle_id=pid).order_by(Comptage.date).all()
