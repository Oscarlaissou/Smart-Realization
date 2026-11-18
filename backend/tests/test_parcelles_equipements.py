"""Parcelles × équipements (fusion des branches parcelles et équipements/fertilisation)."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient

from app.main import app
from tests.test_parcelles import _creer_utilisateur, _exploitation_principale


def _parcelle(client, entetes, exploitation_id, **extra):
    r = client.post(
        "/parcelles",
        json={"nom": "Champ maïs", "surface_ha": 1.5, "exploitation_id": exploitation_id, **extra},
        headers=entetes,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_champs_supplementaires_et_modification_partielle():
    with TestClient(app) as client:
        entetes, _ = _creer_utilisateur(client, "champs")
        expl = _exploitation_principale(client, entetes)
        p = _parcelle(client, entetes, expl["id"], type_sol="argileux", seuil_humidite_min=25)
        assert p["type_sol"] == "argileux" and p["seuil_humidite_min"] == 25 and p["equipements"] == []

        # Le front n'envoie que nom / surface / exploitation : les autres champs ne doivent pas être effacés
        r = client.put(
            f"/parcelles/{p['id']}",
            json={"nom": "Champ renommé", "surface_ha": 2, "exploitation_id": expl["id"]},
            headers=entetes,
        )
        assert r.status_code == 200, r.text
        assert r.json()["type_sol"] == "argileux" and r.json()["seuil_humidite_min"] == 25


def test_associer_et_dissocier_un_equipement():
    with TestClient(app) as client:
        entetes, _ = _creer_utilisateur(client, "equip")
        expl = _exploitation_principale(client, entetes)
        p = _parcelle(client, entetes, expl["id"])

        e = client.post("/equipements", json={"code": "VAN-01", "type": "electrovanne"}, headers=entetes)
        assert e.status_code == 201, e.text
        eid = e.json()["id"]

        r = client.post(f"/parcelles/{p['id']}/equipements", json={"equipement_id": eid}, headers=entetes)
        assert r.status_code == 201, r.text
        assert [x["code"] for x in r.json()["equipements"]] == ["VAN-01"]
        assert client.get("/parcelles", headers=entetes).json()[0]["equipements"][0]["id"] == eid

        assert client.delete(f"/parcelles/{p['id']}/equipements/{eid}", headers=entetes).status_code == 204
        assert client.get(f"/parcelles/{p['id']}", headers=entetes).json()["equipements"] == []


def test_un_autre_utilisateur_ne_peut_pas_associer_mon_equipement():
    with TestClient(app) as client:
        moi, _ = _creer_utilisateur(client, "moi")
        autre, _ = _creer_utilisateur(client, "autre")
        eid = client.post("/equipements", json={"code": "CAP-01", "type": "capteur"}, headers=moi).json()["id"]
        sa_parcelle = _parcelle(client, autre, _exploitation_principale(client, autre)["id"])

        r = client.post(f"/parcelles/{sa_parcelle['id']}/equipements", json={"equipement_id": eid}, headers=autre)
        assert r.status_code == 404
        assert all(x["id"] != eid for x in client.get("/equipements", headers=autre).json())
