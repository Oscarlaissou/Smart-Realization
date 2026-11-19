"""Quantité d'engrais selon la surface (ha) et le nombre de plants (comptage caméra ou saisie)."""
import uuid

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.features.camera.models import Comptage
from app.features.fertilisation import service
from app.main import app


def _parcelle_mais(client, surface_ha=2):
    r = client.post("/auth/inscription", json={"nom": "F", "telephone": "", "email": f"f-{uuid.uuid4().hex[:8]}@x.cm",
                                                "nom_exploitation": "E", "mot_de_passe": "secret123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    expl = client.get("/exploitations", headers=h).json()[0]["id"]
    pid = client.post("/parcelles", json={"nom": "Maïs", "surface_ha": surface_ha, "exploitation_id": expl},
                      headers=h).json()["id"]
    client.post(f"/parcelles/{pid}/cultures", json={"espece": "mais"}, headers=h)   # sans accent ni majuscule
    return h, pid


def _npk(dose):
    return next(p for p in dose["produits_suggeres"] if p["nom"].startswith("NPK"))


def test_seul_le_mais_est_gere():
    assert service.culture_connue("mais") == "Maïs"
    assert service.culture_connue(None) == "Maïs"
    assert list(service.BESOINS_PAR_CULTURE) == ["Maïs"]


def test_dose_standard_sans_comptage():
    with TestClient(app) as c:
        h, pid = _parcelle_mais(c)
        d = c.get(f"/fertilisation/dose/{pid}", headers=h).json()
        assert d["culture"] == "Maïs"
        assert d["nb_plants"] is None and d["facteur"] == 1.0
        npk = _npk(d)
        assert npk["quantite_totale_kg"] == round(npk["quantite_kg_ha"] * 2, 1)
        assert npk["sacs_50kg"] == -(-npk["quantite_totale_kg"] // 50)


def test_dose_suit_le_dernier_comptage_camera():
    with TestClient(app) as c:
        h, pid = _parcelle_mais(c)
        base = _npk(c.get(f"/fertilisation/dose/{pid}", headers=h).json())["quantite_kg_ha"]
        db = SessionLocal()
        db.add(Comptage(parcelle_id=pid, image_path="x.jpg", nb_plants=80_000))   # 40 000 plants/ha
        db.commit()
        db.close()
        d = c.get(f"/fertilisation/dose/{pid}", headers=h).json()
        assert d["source_plants"] == "camera" and d["densite_plants_ha"] == 40_000
        assert d["facteur"] == round(40_000 / 53_000, 2)
        npk = _npk(d)
        assert npk["quantite_kg_ha"] < base
        assert npk["grammes_par_plant"] == round(npk["quantite_totale_kg"] * 1000 / 80_000, 1)


def test_saisie_manuelle_et_facteur_plafonne():
    with TestClient(app) as c:
        h, pid = _parcelle_mais(c)
        d = c.get(f"/fertilisation/dose/{pid}?surface_ha=1&nb_plants=500000", headers=h).json()
        assert d["source_plants"] == "saisie" and d["surface_ha"] == 1
        assert d["facteur"] == 1.5 and d["borne"] is True
