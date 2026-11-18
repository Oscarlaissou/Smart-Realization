"""CONTRÔLEUR – Caméra (images, comptage, évolution, comparaison par date)."""
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import current_user
from ..auth.models import User
from ..parcelles.models import Exploitation, Parcelle
from .models import Comptage
from .schemas import ComptageOut, ParcelleCameraOut
from . import service as comptage_service
from . import stockage

router = APIRouter(prefix="/camera", tags=["Caméra"], dependencies=[Depends(current_user)])


def _parcelle_autorisee(db: Session, pid: int, user: User) -> None:
    """404 si la parcelle n'existe pas OU n'appartient pas à l'utilisateur connecté."""
    trouvee = (
        db.query(Parcelle.id)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Parcelle.id == pid, Exploitation.user_id == user.id)
        .first()
    )
    if trouvee is None:
        raise HTTPException(status_code=404, detail="Parcelle introuvable")


def _enregistrer_comptage(db: Session, pid: int, contenu: bytes, date: datetime | None = None) -> Comptage:
    """Valide l'image, compte les plants, la stocke (Supabase Storage ou disque), puis enregistre le comptage."""
    if not contenu:
        raise HTTPException(status_code=400, detail="Fichier vide")
    if len(contenu) > stockage.TAILLE_MAX:
        raise HTTPException(status_code=413, detail="Image trop lourde (8 Mo maximum)")
    extension = stockage.extension_reelle(contenu)
    if extension is None:
        raise HTTPException(status_code=415, detail="Format non reconnu (JPEG, PNG ou WebP attendu)")

    # L'analyse YOLO peut durer longtemps (téléchargement + chargement du modèle au 1er appel).
    # On rend la connexion à la base au pool avant : sinon Supabase la coupe pour inactivité
    # et l'INSERT échoue. La session en reprend une neuve (pool_pre_ping) juste après.
    db.close()
    try:
        analyse = comptage_service.analyser_image(contenu)   # avant d'écrire quoi que ce soit sur disque
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    chemin = stockage.enregistrer_image(pid, contenu, extension)
    chemin_det = None
    try:
        if analyse.image_annotee:
            chemin_det = stockage.enregistrer_detections(chemin, analyse.image_annotee)
        c = Comptage(
            parcelle_id=pid,
            image_path=chemin,
            detections_path=chemin_det,
            nb_plants=analyse.nb_plants,
        )
        if date is not None:
            c.date = date
        db.add(c)
        db.commit()
        db.refresh(c)
    except Exception:
        db.rollback()
        stockage.supprimer_images(chemin, chemin_det)  # pas de fichier orphelin si l'envoi ou la base échoue
        raise
    return c


@router.post("/{pid}/images", response_model=ComptageOut, status_code=201)
async def recevoir_image(
    pid: int,
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Réception d'une image (future ESP32-CAM, F9.3) : stockage + comptage."""
    _parcelle_autorisee(db, pid, user)
    contenu = await fichier.read()
    # L'inférence YOLO est lourde : on la sort de la boucle asyncio pour ne pas bloquer les autres requêtes
    return await run_in_threadpool(_enregistrer_comptage, db, pid, contenu)


@router.post("/{pid}/importer", response_model=list[ComptageOut], status_code=201)
def importer_images_test(
    pid: int,
    fichier: str | None = None,
    date: datetime | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """DÉVELOPPEMENT : simule la caméra avec les images du dossier image/ (racine du projet).

    - sans paramètre : importe toutes les images du dossier ;
    - ?fichier=plan1.jpg : importe uniquement cette image ;
    - ?date=2026-11-01T08:00:00 : force la date (pour tester l'évolution / la comparaison F7.4).
    Appeler deux fois importe deux fois : les comptages ne sont pas dédupliqués.
    """
    _parcelle_autorisee(db, pid, user)
    disponibles = stockage.lister_images_test()
    if fichier:
        voulu = stockage.DOSSIER_IMAGES_TEST / Path(fichier).name  # .name bloque les ../
        if voulu not in disponibles:
            raise HTTPException(status_code=404, detail=f"« {Path(fichier).name} » introuvable dans image/")
        disponibles = [voulu]
    if not disponibles:
        raise HTTPException(status_code=404, detail="Aucune image trouvée dans le dossier image/ à la racine du projet")
    return [_enregistrer_comptage(db, pid, p.read_bytes(), date) for p in disponibles]


@router.get("/{pid}/comptages", response_model=list[ComptageOut])
def evolution(pid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _parcelle_autorisee(db, pid, user)
    return db.query(Comptage).filter_by(parcelle_id=pid).order_by(Comptage.date).all()


@router.get("/parcelles", response_model=list[ParcelleCameraOut])
def parcelles_de_l_utilisateur(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Parcelles de l'utilisateur connecté (pastilles de la page « Suivi par caméra »)."""
    return (
        db.query(Parcelle)
        .join(Exploitation, Parcelle.exploitation_id == Exploitation.id)
        .filter(Exploitation.user_id == user.id)
        .order_by(Parcelle.id)
        .all()
    )