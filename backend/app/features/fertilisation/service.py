"""Calcul de la dose d'engrais recommandée — culture prise en charge : le MAÏS uniquement.

Deux niveaux :
- Une base par défaut, les besoins du maïs (pas besoin d'analyse
  de sol pour avoir une première estimation).
- Si une analyse de sol existe (DonneeAgro), on l'utilise pour affiner :
  le manque calculé tient compte de ce qui est déjà présent dans le sol.

Valeurs à titre indicatif (cibles usuelles en kg/ha) — à affiner avec de
vraies références agronomiques si besoin.
"""

import math
import unicodedata

CULTURE = "Maïs"   # seule culture gérée par l'application

# Besoins du maïs en éléments purs (kg/ha)
BESOINS_PAR_CULTURE = {
    CULTURE: {"azote": 120, "phosphore": 60, "potassium": 100},
}
CIBLE_PAR_DEFAUT = BESOINS_PAR_CULTURE[CULTURE]


def recommander(culture: str | None, azote: float, phosphore: float, potassium: float) -> dict:
    """Manque en kg/ha pour le maïs, en tenant compte de ce qui est déjà
    dans le sol (azote/phosphore/potassium, 0 si pas d'analyse)."""
    cible = BESOINS_PAR_CULTURE.get(culture, CIBLE_PAR_DEFAUT)
    return {
        "azote_kg_ha": max(cible["azote"] - azote, 0),
        "phosphore_kg_ha": max(cible["phosphore"] - phosphore, 0),
        "potassium_kg_ha": max(cible["potassium"] - potassium, 0),
    }


# Engrais couramment utilisés pour le maïs au Cameroun — valeurs indicatives
# (composition en % d'élément pur). NPK 15-15-15 + Urée : recommandation citée
# pour le maïs (fiches techniques APNI/4R, programme de conseil en fertilisation).
PRODUITS_PAR_CULTURE = {
    CULTURE: [
        {"nom": "NPK 15-15-15", "azote": 0.15, "phosphore": 0.15, "potassium": 0.15},
        {"nom": "Urée (46% azote)", "azote": 0.46},
    ],
}
PRODUITS_PAR_DEFAUT = PRODUITS_PAR_CULTURE[CULTURE]


LIBELLE_ELEMENT = {"azote": "N", "phosphore": "P", "potassium": "K"}


def suggerer_produits(culture: str | None, manque_par_ha: dict) -> list[dict]:
    """Pour chaque engrais courant du maïs : sa composition
    (ex: '15% N · 15% P · 15% K') et la quantité du PRODUIT à épandre par
    hectare. Quand un produit couvre plusieurs éléments, on retient la plus
    grande des quantités nécessaires (pour ne laisser aucun des éléments en
    dessous du besoin)."""
    produits = PRODUITS_PAR_CULTURE.get(culture, PRODUITS_PAR_DEFAUT)
    resultats = []
    for produit in produits:
        composition, quantites = [], []
        for element in ("azote", "phosphore", "potassium"):
            if element in produit:
                pourcentage = produit[element]
                composition.append(f"{round(pourcentage * 100)}% {LIBELLE_ELEMENT[element]}")
                quantites.append(manque_par_ha[f"{element}_kg_ha"] / pourcentage)
        resultats.append({
            "nom": produit["nom"],
            "composition": " · ".join(composition),
            "quantite_kg_ha": round(max(quantites), 1) if quantites else 0,
        })
    return resultats

# ---------------------------------------------------------------------------
# Ajustement selon le nombre de plants (comptage caméra ou saisie)
# ---------------------------------------------------------------------------
# Densité de référence du maïs (plants/ha) pour laquelle les besoins ci-dessus sont donnés :
# ~53 000 plants/ha (écartement 75 x 25 cm).
DENSITE_REFERENCE = {CULTURE: 53_000}
DENSITE_PAR_DEFAUT = DENSITE_REFERENCE[CULTURE]
# On ne suit pas aveuglément le comptage : facteur borné pour éviter une dose absurde
# (image partielle, erreur de comptage...).
FACTEUR_MIN, FACTEUR_MAX = 0.5, 1.5
POIDS_SAC_KG = 50


def _cle(texte: str | None) -> str:
    sans_accent = "".join(c for c in unicodedata.normalize("NFD", texte or "") if unicodedata.category(c) != "Mn")
    return sans_accent.lower().strip()


def culture_connue(culture: str | None) -> str:
    """L'application ne gère que le maïs : la recommandation est toujours celle du maïs."""
    return CULTURE


def ajuster_densite(culture: str | None, surface_ha: float, nb_plants: int | None) -> dict:
    """Facteur appliqué aux doses/ha selon la densité réelle de plants (nb_plants / surface)."""
    reference = DENSITE_REFERENCE.get(culture, DENSITE_PAR_DEFAUT)
    if not nb_plants or surface_ha <= 0:
        return {"densite_plants_ha": None, "densite_reference": reference, "facteur": 1.0, "borne": False}
    densite = nb_plants / surface_ha
    brut = densite / reference
    facteur = min(max(brut, FACTEUR_MIN), FACTEUR_MAX)
    return {
        "densite_plants_ha": round(densite),
        "densite_reference": reference,
        "facteur": round(facteur, 2),
        "borne": facteur != brut,
    }


def quantites_a_epandre(produits: list[dict], facteur: float, surface_ha: float, nb_plants: int | None) -> list[dict]:
    """Ajoute à chaque produit : dose/ha ajustée, total pour la parcelle, nombre de sacs, grammes par plant."""
    resultats = []
    for produit in produits:
        par_ha = round(produit["quantite_kg_ha"] * facteur, 1)
        total = round(par_ha * surface_ha, 1)
        resultats.append({
            **produit,
            "quantite_kg_ha_base": produit["quantite_kg_ha"],
            "quantite_kg_ha": par_ha,
            "quantite_totale_kg": total,
            "sacs_50kg": math.ceil(total / POIDS_SAC_KG) if total > 0 else 0,
            "grammes_par_plant": round(total * 1000 / nb_plants, 1) if nb_plants else None,
        })
    return resultats
