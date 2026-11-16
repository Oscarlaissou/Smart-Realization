import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
from fastapi.testclient import TestClient
from app.main import app

def test_parcours_complet():
    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "ok"}
        c.post("/auth/register", json={"nom": "Oscar", "email": "o@sevia.cm", "mot_de_passe": "secret123"})
        t = c.post("/auth/login", data={"username": "o@sevia.cm", "password": "secret123"}).json()["access_token"]
        h = {"Authorization": f"Bearer {t}"}
        e = c.post("/exploitations", json={"nom": "Domaine Les Collines"}, headers=h).json()
        p = c.post("/parcelles", json={"nom": "Sud", "surface_ha": 2, "exploitation_id": e["id"]}, headers=h).json()
        c.post("/humidite/mesures", json={"parcelle_id": p["id"], "humidite": 22})
        assert len(c.get("/alertes", headers=h).json()) == 1      # sol sec => alerte
        c.post("/fertilisation/donnees", json={"parcelle_id": p["id"], "azote": 20}, headers=h)
        assert c.get(f"/fertilisation/dose/{p['id']}", headers=h).json()["azote_kg_ha"] == 100
        assert c.get("/dashboard/indicateurs", headers=h).json()["alertes_actives"] == 1
