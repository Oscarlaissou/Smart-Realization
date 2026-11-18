"""Mesure la précision du COMPTAGE (pas seulement de la détection) sur des images de validation entières,
avec exactement le code utilisé par l'API (app/features/camera/service.py).

Usage (depuis le dossier backend/, pour que le .env soit lu) :
    .venv\\Scripts\\python training/evaluer_comptage.py            # 20 images de val
    .venv\\Scripts\\python training/evaluer_comptage.py --n 106    # toute la validation
"""
import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "backend"))

from app.core.config import settings  # noqa: E402
from app.features.camera import service  # noqa: E402
from preparer_dataset import SOURCE, lire_liste, lire_points  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=20)
    args = p.parse_args()

    settings.YOLO_ENABLED = True
    noms = lire_liste(SOURCE / "val.txt")[: args.n]
    erreurs = []
    for nom in noms:
        reel = len(lire_points(SOURCE / "labels" / f"{nom}.csv"))
        compte = service.analyser_image((SOURCE / "images" / f"{nom}.JPG").read_bytes()).nb_plants
        erreurs.append(compte - reel)
        print(f"{nom:20s} réel={reel:4d}  compté={compte:4d}  écart={compte - reel:+d}")

    reels = [len(lire_points(SOURCE / "labels" / f"{n}.csv")) for n in noms]
    mae = sum(abs(e) for e in erreurs) / len(erreurs)
    print(f"\nErreur moyenne absolue : {mae:.1f} plants / image "
          f"({100 * mae / (sum(reels) / len(reels)):.1f} % du nombre moyen)")


if __name__ == "__main__":
    main()
