"""Entraîne YOLO sur le dataset préparé par preparer_dataset.py et copie le meilleur modèle dans backend/models/.

Usage (depuis la racine du projet) :
    backend\\.venv\\Scripts\\python backend/training/entrainer.py            # CPU, limité à HEURES_MAX
    backend\\.venv\\Scripts\\python backend/training/entrainer.py --device 0 # GPU (Colab, etc.)
"""
import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

RACINE = Path(__file__).resolve().parents[2]
DATA = RACINE / "datasets" / "mais_yolo" / "data.yaml"
RUNS = RACINE / "backend" / "training" / "runs"
DESTINATION = RACINE / "backend" / "models" / "mais.pt"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--modele", default="yolo11n.pt", help="poids de départ (pré-entraînés COCO)")
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--heures", type=float, default=3.0, help="durée max ; prioritaire sur --epochs")
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--device", default="cpu")
    args = p.parse_args()

    modele = YOLO(args.modele)
    modele.train(
        data=str(DATA),
        imgsz=640,
        epochs=args.epochs,
        time=args.heures,
        batch=args.batch,
        device=args.device,
        workers=4,
        cache="ram",
        patience=10,
        max_det=1000,        # une tuile peut contenir beaucoup de panicules
        mosaic=1.0,
        close_mosaic=5,
        flipud=0.5,          # vue de dessus : l'orientation n'a pas de sens
        fliplr=0.5,
        degrees=90,
        project=str(RUNS),
        name="mais",
        exist_ok=True,
        plots=True,
    )

    meilleur = RUNS / "mais" / "weights" / "best.pt"
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(meilleur, DESTINATION)
    print(f"Modèle copié : {DESTINATION}")


if __name__ == "__main__":
    main()
