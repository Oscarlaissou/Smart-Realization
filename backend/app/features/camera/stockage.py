"""Stockage des images de la caméra (F7.1).

Deux modes, choisis automatiquement :
- Supabase Storage si SUPABASE_URL et SUPABASE_SERVICE_KEY sont dans le .env (mode normal : les images
  survivent à un redéploiement ou à un vidage du disque) ;
- disque local (backend/uploads/, servi par /media) sinon, pratique pour développer sans clé.

En base on ne garde qu'un chemin RELATIF, identique dans les deux modes :
"camera/3/20261117T101500_a1b2c3d4.jpg". Seule url_publique() change selon le mode.
"""
import logging
import uuid
from datetime import datetime
from pathlib import Path

import httpx

from ...core.config import settings

log = logging.getLogger(__name__)

# backend/app/features/camera/stockage.py -> parents[4] = racine du projet
RACINE_PROJET = Path(__file__).resolve().parents[4]
DOSSIER_IMAGES_TEST = RACINE_PROJET / "image"            # images de test (pas de caméra pour l'instant)
DOSSIER_UPLOADS = RACINE_PROJET / "backend" / "uploads"  # mode local uniquement (à mettre dans .gitignore)

TAILLE_MAX = 8 * 1024 * 1024  # 8 Mo
EXTENSIONS_TEST = {".jpg", ".jpeg", ".png", ".webp"}
TYPES_MIME = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


# ---------- Détection du format ----------
def extension_reelle(contenu: bytes) -> str | None:
    """Détecte le vrai format d'après les premiers octets (ne fait pas confiance au nom du fichier)."""
    if contenu[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if contenu[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if contenu[:4] == b"RIFF" and contenu[8:12] == b"WEBP":
        return ".webp"
    return None


# ---------- Supabase Storage (API REST) ----------
def supabase_actif() -> bool:
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY)


def _api() -> str:
    return settings.SUPABASE_URL.rstrip("/") + "/storage/v1"


def _entetes() -> dict:
    cle = settings.SUPABASE_SERVICE_KEY
    entetes = {"apikey": cle}
    if cle.startswith("eyJ"):                 # ancienne clé service_role (JWT)
        entetes["Authorization"] = f"Bearer {cle}"
    return entetes                            # nouvelle clé sb_secret_… : l'en-tête apikey suffit


def _ecrire(chemin: str, contenu: bytes, type_mime: str) -> None:
    if supabase_actif():
        r = httpx.post(
            f"{_api()}/object/{settings.SUPABASE_BUCKET}/{chemin}",
            headers={**_entetes(), "Content-Type": type_mime},
            content=contenu,
            timeout=30,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"Supabase Storage a refusé l'envoi ({r.status_code}) : {r.text}")
    else:
        cible = DOSSIER_UPLOADS / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_bytes(contenu)


# ---------- API utilisée par le router ----------
def enregistrer_image(parcelle_id: int, contenu: bytes, extension: str) -> str:
    """Envoie l'image et retourne son chemin relatif (celui à mettre en base)."""
    nom = f"{datetime.utcnow():%Y%m%dT%H%M%S}_{uuid.uuid4().hex[:8]}{extension}"
    chemin = f"camera/{parcelle_id}/{nom}"
    _ecrire(chemin, contenu, TYPES_MIME[extension])
    return chemin


def chemin_detections(chemin_relatif: str) -> str:
    """camera/3/xxx.jpg -> camera/3/xxx_det.jpg (image avec les détections YOLO)."""
    return str(Path(chemin_relatif).with_suffix("")).replace("\\", "/") + "_det.jpg"


def enregistrer_detections(chemin_relatif: str, contenu_jpeg: bytes) -> str:
    """Envoie l'image annotée et retourne son chemin relatif."""
    chemin = chemin_detections(chemin_relatif)
    _ecrire(chemin, contenu_jpeg, "image/jpeg")
    return chemin


def supprimer_images(*chemins: str | None) -> None:
    """Nettoyage au mieux (ne lève jamais) : utilisé quand l'écriture en base échoue."""
    chemins = [c for c in chemins if c]
    if not chemins:
        return
    try:
        if supabase_actif():
            httpx.request(
                "DELETE",
                f"{_api()}/object/{settings.SUPABASE_BUCKET}",
                headers=_entetes(),
                json={"prefixes": chemins},
                timeout=15,
            )
        else:
            for c in chemins:
                (DOSSIER_UPLOADS / c).unlink(missing_ok=True)
    except Exception:
        log.warning("Suppression impossible pour %s", chemins, exc_info=True)


def url_publique(chemin_relatif: str) -> str:
    """URL à donner au front. Supabase : bucket public. Local : montage /media (relative à l'API)."""
    if not chemin_relatif:
        return ""
    if supabase_actif():
        return f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{chemin_relatif}"
    return f"/media/{chemin_relatif}"


# ---------- Images de test (dossier image/ à la racine) ----------
def lister_images_test() -> list[Path]:
    if not DOSSIER_IMAGES_TEST.is_dir():
        return []
    return sorted(
        p for p in DOSSIER_IMAGES_TEST.iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSIONS_TEST
    )