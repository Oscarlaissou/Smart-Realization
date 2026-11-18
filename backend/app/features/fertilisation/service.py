"""Calcul de la dose d'engrais recommandée.

Deux niveaux :
- Une base par défaut, selon la culture de la parcelle (pas besoin d'analyse
  de sol pour avoir une première estimation).
- Si une analyse de sol existe (DonneeAgro), on l'utilise pour affiner :
  le manque calculé tient compte de ce qui est déjà présent dans le sol.

Valeurs à titre indicatif (cibles usuelles en kg/ha) — à affiner avec de
vraies références agronomiques si besoin.
"""

BESOINS_PAR_CULTURE = {
    "Maïs": {"azote": 120, "phosphore": 60, "potassium": 100},
    "Tomate": {"azote": 150, "phosphore": 80, "potassium": 150},
    "Manioc": {"azote": 60, "phosphore": 40, "potassium": 80},
    # Potassium relevé à 200 kg/ha : des essais menés au Cameroun montrent
    # que le plantain/la banane plantain ont un besoin particulièrement
    # élevé en potassium (NPK testé à 200-40-200 kg/ha, IITA/PROPAS).
    "Plantain": {"azote": 200, "phosphore": 40, "potassium": 200},
}
CIBLE_PAR_DEFAUT = {"azote": 120, "phosphore": 60, "potassium": 100}


def recommander(culture: str | None, azote: float, phosphore: float, potassium: float) -> dict:
    """Manque en kg/ha, pour la culture donnée (ou une cible générique si la
    culture n'est pas connue/pas dans la liste), en tenant compte de ce qui
    est déjà dans le sol (azote/phosphore/potassium, 0 si pas d'analyse)."""
    cible = BESOINS_PAR_CULTURE.get(culture, CIBLE_PAR_DEFAUT)
    return {
        "azote_kg_ha": max(cible["azote"] - azote, 0),
        "phosphore_kg_ha": max(cible["phosphore"] - phosphore, 0),
        "potassium_kg_ha": max(cible["potassium"] - potassium, 0),
    }


# Engrais couramment utilisés au Cameroun, selon la culture — valeurs
# indicatives (composition en % d'élément pur), à affiner avec de vraies
# références agronomiques si besoin. Un produit n'est pas forcément utile
# pour toutes les cultures (ex : le manioc n'a pas les mêmes engrais
# courants que le maïs).
PRODUITS_PAR_CULTURE = {
    # NPK 15-15-15 + Urée : recommandation citée pour le maïs au Cameroun
    # (fiches techniques APNI/4R, programme de conseil en fertilisation).
    "Maïs": [
        {"nom": "NPK 15-15-15", "azote": 0.15, "phosphore": 0.15, "potassium": 0.15},
        {"nom": "Urée (46% azote)", "azote": 0.46},
    ],
    # NPK 20-10-10 : utilisé dans une étude sur la tomate à l'Est-Cameroun.
    "Tomate": [
        {"nom": "NPK 20-10-10", "azote": 0.20, "phosphore": 0.10, "potassium": 0.10},
        {"nom": "Urée (46% azote)", "azote": 0.46},
    ],
    "Manioc": [
        {"nom": "NPK 15-15-15", "azote": 0.15, "phosphore": 0.15, "potassium": 0.15},
        {"nom": "Chlorure de potassium (60% potassium)", "potassium": 0.60},
    ],
    "Plantain": [
        {"nom": "NPK 12-6-20", "azote": 0.12, "phosphore": 0.06, "potassium": 0.20},
        {"nom": "Chlorure de potassium (60% potassium)", "potassium": 0.60},
    ],
}
PRODUITS_PAR_DEFAUT = [
    {"nom": "NPK 15-15-15", "azote": 0.15, "phosphore": 0.15, "potassium": 0.15},
]


LIBELLE_ELEMENT = {"azote": "N", "phosphore": "P", "potassium": "K"}


def suggerer_produits(culture: str | None, manque_par_ha: dict) -> list[dict]:
    """Pour chaque produit courant de cette culture : sa composition
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