"""Calcul de la dose d'engrais recommandée. Version de départ très simple.
TODO (Aurelie) : remplacer par des références agronomiques par culture."""
BESOIN = {"azote": 120, "phosphore": 60, "potassium": 100}   # kg/ha cibles (exemple)

def recommander(azote: float, phosphore: float, potassium: float) -> dict:
    return {
        "azote_kg_ha": max(BESOIN["azote"] - azote, 0),
        "phosphore_kg_ha": max(BESOIN["phosphore"] - phosphore, 0),
        "potassium_kg_ha": max(BESOIN["potassium"] - potassium, 0),
    }
