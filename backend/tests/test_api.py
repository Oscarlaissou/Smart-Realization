import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient

from app.main import app


def test_parcours_complet():
    suffixe = uuid.uuid4().hex[:8]
    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "ok"}
        inscription = c.post(
            "/auth/inscription",
            json={
                "nom": "Oscar",
                "email": f"o-{suffixe}@sevia.cm",
                "nom_exploitation": "Domaine Les Collines",
                "mot_de_passe": "secret123",
            },
        )
        assert inscription.status_code == 201, inscription.text
        token = inscription.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        e = c.post(
            "/exploitations",
            json={"nom": "Domaine Les Collines Bis"},
            headers=h,
        ).json()
        p = c.post(
            "/parcelles",
            json={"nom": "Sud", "surface_ha": 2, "exploitation_id": e["id"]},
            headers=h,
        ).json()
        c.post("/humidite/mesures", json={"parcelle_id": p["id"], "humidite": 22}, headers=h)
        assert len(c.get("/alertes", headers=h).json()) == 1      # sol sec => alerte
        c.post("/fertilisation/donnees", json={"parcelle_id": p["id"], "azote": 20}, headers=h)
        assert c.get(f"/fertilisation/dose/{p['id']}", headers=h).json()["besoins_kg_ha"]["azote_kg_ha"] == 100
        assert c.get("/dashboard/indicateurs", headers=h).json()["alertes_actives"] == 1

