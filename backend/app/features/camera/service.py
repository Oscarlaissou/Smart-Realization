"""Comptage des plants de maïs sur une image de drone avec YOLO (F7.2).

Le modèle (backend/models/mais.pt) est entraîné par backend/training/entrainer.py pour détecter les
panicules de maïs : une panicule = un plant. Les photos de drone sont très grandes (≈ 5472x3648) et les
panicules petites, donc on reproduit le traitement de l'entraînement :
  1. réduction de l'image (YOLO_ECHELLE) ;
  2. découpage en tuiles YOLO_IMGSZ x YOLO_IMGSZ qui se chevauchent (YOLO_CHEVAUCHEMENT) ;
  3. détection sur chaque tuile, puis fusion : une détection n'est gardée que par la tuile où son centre
     tombe dans la zone « centrale » (pas de double comptage dans les recouvrements) + NMS de sécurité.

Piloté par le .env (voir core/config.py). Désactivé (YOLO_ENABLED=false), analyser_image() renvoie 0.
"""
import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from ...core.config import settings

log = logging.getLogger(__name__)

# backend/app/features/camera/service.py -> parents[3] = backend
DOSSIER_MODELES = Path(__file__).resolve().parents[3] / "models"   # backend/models/ (mais.pt, etc.)

SEUIL_NMS = 0.5
TUILES_PAR_LOT = 8

_modele = None
_verrou = threading.Lock()   # un seul chargement / une seule inférence à la fois


@dataclass
class Resultat:
    nb_plants: int
    image_annotee: bytes | None = None   # JPEG avec les détections dessinées (None si YOLO désactivé)


def _classes() -> list[int] | None:
    brut = settings.YOLO_CLASSES.strip()
    return [int(c) for c in brut.split(",")] if brut else None


def _charger_modele():
    """Chargement paresseux : le modèle n'est lu qu'au premier comptage."""
    global _modele
    if _modele is None:
        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise RuntimeError(
                "YOLO_ENABLED=true mais ultralytics n'est pas installé : "
                "pip install ultralytics opencv-python-headless"
            ) from e
        local = DOSSIER_MODELES / settings.YOLO_MODEL
        if not local.is_file():
            # Pas de repli silencieux sur un modèle générique : il ne sait pas compter le maïs.
            raise RuntimeError(
                f"Modèle de comptage introuvable : {local}. Faire « git pull » (le fichier est "
                "versionné) ou le régénérer avec backend/training/entrainer.py."
            )
        _modele = YOLO(str(local))
        log.info("Modèle YOLO chargé : %s", settings.YOLO_MODEL)
    return _modele


def _positions(longueur: int, tuile: int, pas: int) -> list[int]:
    """Origines des tuiles sur un axe, la dernière collée au bord (même règle qu'à l'entraînement)."""
    if longueur <= tuile:
        return [0]
    pos = list(range(0, longueur - tuile, pas))
    pos.append(longueur - tuile)
    return pos


def _zone_centrale(debut: int, tuile: int, longueur: int, marge: float) -> tuple[float, float]:
    """Zone d'une tuile où elle est « responsable » des détections ; pas de marge sur les bords de l'image."""
    bas = debut + marge if debut > 0 else float("-inf")
    haut = debut + tuile - marge if debut + tuile < longueur else float("inf")
    return bas, haut


def _detecter(image) -> list[tuple[float, float, float, float, float]]:
    """Détection tuilée sur l'image (déjà réduite). Renvoie [(x1, y1, x2, y2, score)] en coordonnées image."""
    import cv2

    modele = _charger_modele()
    tuile = settings.YOLO_IMGSZ
    h, w = image.shape[:2]
    pas = max(tuile - settings.YOLO_CHEVAUCHEMENT, 1)
    marge = settings.YOLO_CHEVAUCHEMENT / 2

    origines = [(x0, y0) for y0 in _positions(h, tuile, pas) for x0 in _positions(w, tuile, pas)]
    boites: list[tuple[float, float, float, float, float]] = []

    for i in range(0, len(origines), TUILES_PAR_LOT):
        lot = origines[i:i + TUILES_PAR_LOT]
        morceaux = [image[y0:y0 + tuile, x0:x0 + tuile] for x0, y0 in lot]
        resultats = modele.predict(
            morceaux,
            conf=settings.YOLO_CONFIANCE,
            imgsz=tuile,
            classes=_classes(),
            max_det=1000,
            verbose=False,
        )
        for (x0, y0), r in zip(lot, resultats):
            bx0, bx1 = _zone_centrale(x0, tuile, w, marge)
            by0, by1 = _zone_centrale(y0, tuile, h, marge)
            for (x1, y1, x2, y2), score in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist()):
                cx, cy = x0 + (x1 + x2) / 2, y0 + (y1 + y2) / 2
                if bx0 <= cx < bx1 and by0 <= cy < by1:
                    boites.append((x0 + x1, y0 + y1, x0 + x2, y0 + y2, score))

    if not boites:
        return []
    # NMS de sécurité (détections très proches de la frontière entre deux tuiles)
    rects = [[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in boites]
    gardes = cv2.dnn.NMSBoxes(rects, [b[4] for b in boites], settings.YOLO_CONFIANCE, SEUIL_NMS)
    return [boites[int(i)] for i in (gardes.flatten() if len(gardes) else [])]


def analyser_image(image_bytes: bytes) -> Resultat:
    """Compte les plants et dessine les détections. Lève ValueError si l'image est illisible."""
    if not settings.YOLO_ENABLED:
        return Resultat(nb_plants=0)

    import cv2
    import numpy as np

    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image illisible ou corrompue")

    echelle = settings.YOLO_ECHELLE
    if echelle != 1:
        image = cv2.resize(image, None, fx=echelle, fy=echelle, interpolation=cv2.INTER_AREA)

    with _verrou:
        boites = _detecter(image)

    # Image annotée à la taille réduite (plus légère à stocker et à afficher)
    annotee = image.copy()
    epaisseur = max(1, round(min(annotee.shape[:2]) / 600))
    for x1, y1, x2, y2, _ in boites:
        cv2.rectangle(annotee, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), epaisseur)

    ok, tampon = cv2.imencode(".jpg", annotee, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return Resultat(nb_plants=len(boites), image_annotee=tampon.tobytes() if ok else None)


def compter_plants(image_bytes: bytes) -> int:
    """Compatibilité avec l'ancienne signature."""
    return analyser_image(image_bytes).nb_plants
