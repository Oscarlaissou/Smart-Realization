"""Convertit le dataset « maize tassels counting UAV » (points VIA en CSV) en dataset YOLO découpé en tuiles.

Le dataset fournit UN POINT au centre de chaque panicule (≈ 1 panicule = 1 plant de maïs).
YOLO a besoin de cadres : on place un carré de TAILLE_BOITE px (pleine résolution) autour de chaque point.
Les photos de drone font 5472x3648 avec des panicules de ~80 px : on réduit d'un facteur ECHELLE puis
on découpe en tuiles TUILE x TUILE, exactement comme le fera service.py au moment du comptage.

Usage (depuis la racine du projet) :
    backend\\.venv\\Scripts\\python backend/training/preparer_dataset.py
"""
import csv
import json
import random
from pathlib import Path

import cv2

RACINE = Path(__file__).resolve().parents[2]
SOURCE = RACINE / "maize_tassels_counting_uav_dataset"
SORTIE = RACINE / "datasets" / "mais_yolo"

ECHELLE = 0.5        # doit être identique à YOLO_ECHELLE dans le .env
TUILE = 640          # doit être identique à YOLO_IMGSZ
CHEVAUCHEMENT = 64   # recouvrement entre tuiles (px, après réduction)
TAILLE_BOITE = 80    # côté du carré autour d'un point, en px pleine résolution
PART_TUILES_VIDES = 0.1  # on garde 10 % des tuiles sans panicule (exemples négatifs)


def positions(longueur: int, tuile: int, pas: int) -> list[int]:
    """Origines des tuiles sur un axe, la dernière collée au bord."""
    if longueur <= tuile:
        return [0]
    pos = list(range(0, longueur - tuile, pas))
    pos.append(longueur - tuile)
    return pos


def lire_points(csv_path: Path) -> list[tuple[float, float]]:
    pts = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for ligne in csv.DictReader(f):
            forme = json.loads(ligne["region_shape_attributes"] or "{}")
            if forme.get("name") == "point":
                pts.append((forme["cx"], forme["cy"]))
    return pts


def lire_liste(fichier: Path) -> list[str]:
    """train.txt / val.txt : « /images/X.JPG<TAB>/labels/X.csv » -> « X »."""
    noms = []
    for ligne in fichier.read_text(encoding="utf-8-sig").splitlines():
        if ligne.strip():
            noms.append(Path(ligne.split("\t")[0].strip()).stem)
    return noms


def traiter(nom: str, split: str, rng: random.Random) -> tuple[int, int]:
    image = cv2.imread(str(SOURCE / "images" / f"{nom}.JPG"))
    if image is None:
        print(f"  ! image illisible : {nom}")
        return 0, 0
    image = cv2.resize(image, None, fx=ECHELLE, fy=ECHELLE, interpolation=cv2.INTER_AREA)
    h, w = image.shape[:2]
    points = [(x * ECHELLE, y * ECHELLE) for x, y in lire_points(SOURCE / "labels" / f"{nom}.csv")]
    demi = TAILLE_BOITE * ECHELLE / 2
    pas = TUILE - CHEVAUCHEMENT

    n_tuiles = n_boites = 0
    for y0 in positions(h, TUILE, pas):
        for x0 in positions(w, TUILE, pas):
            lignes = []
            for cx, cy in points:
                if not (x0 <= cx < x0 + TUILE and y0 <= cy < y0 + TUILE):
                    continue
                # cadre rogné aux bords de la tuile
                x1, y1 = max(cx - demi, x0), max(cy - demi, y0)
                x2, y2 = min(cx + demi, x0 + TUILE), min(cy + demi, y0 + TUILE)
                bx, by = (x1 + x2) / 2 - x0, (y1 + y2) / 2 - y0
                lignes.append(f"0 {bx / TUILE:.6f} {by / TUILE:.6f} {(x2 - x1) / TUILE:.6f} {(y2 - y1) / TUILE:.6f}")
            if not lignes and rng.random() > PART_TUILES_VIDES:
                continue
            base = f"{nom.replace(' ', '_')}_{x0}_{y0}"
            cv2.imwrite(str(SORTIE / "images" / split / f"{base}.jpg"),
                        image[y0:y0 + TUILE, x0:x0 + TUILE], [cv2.IMWRITE_JPEG_QUALITY, 92])
            (SORTIE / "labels" / split / f"{base}.txt").write_text("\n".join(lignes))
            n_tuiles += 1
            n_boites += len(lignes)
    return n_tuiles, n_boites


def main():
    rng = random.Random(0)
    for split in ("train", "val"):
        (SORTIE / "images" / split).mkdir(parents=True, exist_ok=True)
        (SORTIE / "labels" / split).mkdir(parents=True, exist_ok=True)
        noms = lire_liste(SOURCE / f"{split}.txt")
        total_t = total_b = 0
        for i, nom in enumerate(noms, 1):
            t, b = traiter(nom, split, rng)
            total_t += t
            total_b += b
            if i % 20 == 0:
                print(f"  {split} : {i}/{len(noms)} images")
        print(f"{split} : {len(noms)} images -> {total_t} tuiles, {total_b} panicules")

    (SORTIE / "data.yaml").write_text(
        f"path: {SORTIE.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n  0: plant\n",
        encoding="utf-8",
    )
    print(f"Dataset prêt : {SORTIE / 'data.yaml'}")


if __name__ == "__main__":
    main()
