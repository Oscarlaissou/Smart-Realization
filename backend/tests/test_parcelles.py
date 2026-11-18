import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient

from app.main import app


def _creer_utilisateur(client: TestClient, prefixe: str = "tofa"):
    suffixe = uuid.uuid4().hex[:10]
    donnees = {
        "nom": "Tofa Test",
        "telephone": "+237600000000",
        "email": f"{prefixe}-{suffixe}@sevia.cm",
        "nom_exploitation": f"Exploitation {suffixe}",
        "mot_de_passe": "secret123",
    }
    reponse = client.post("/auth/inscription", json=donnees)
    assert reponse.status_code == 201, reponse.text
    token = reponse.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, reponse.json()["utilisateur"]


def _exploitation_principale(client: TestClient, entetes: dict) -> dict:
    reponse = client.get("/exploitations", headers=entetes)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()[0]


def test_crud_complet_exploitations_parcelles_cultures():
    with TestClient(app) as client:
        entetes, _ = _creer_utilisateur(client, "crud")

        creation_exploitation = client.post(
            "/exploitations",
            json={"nom": "Ferme des Tests", "localisation": "Yaoundé"},
            headers=entetes,
        )
        assert creation_exploitation.status_code == 201, creation_exploitation.text
        exploitation = creation_exploitation.json()
        assert exploitation["nom"] == "Ferme des Tests"

        modification_exploitation = client.put(
            f"/exploitations/{exploitation['id']}",
            json={"nom": "Ferme des Tests rénovée", "localisation": "Douala"},
            headers=entetes,
        )
        assert modification_exploitation.status_code == 200
        assert modification_exploitation.json()["localisation"] == "Douala"

        creation_parcelle = client.post(
            "/parcelles",
            json={
                "nom": "Parcelle Test",
                "surface_ha": 2.5,
                "exploitation_id": exploitation["id"],
            },
            headers=entetes,
        )
        assert creation_parcelle.status_code == 201, creation_parcelle.text
        parcelle = creation_parcelle.json()
        assert parcelle["surface_ha"] == 2.5
        assert parcelle["cultures"] == []

        lecture = client.get(f"/parcelles/{parcelle['id']}", headers=entetes)
        assert lecture.status_code == 200
        assert lecture.json()["nom"] == "Parcelle Test"

        liste = client.get(
            f"/parcelles?exploitation_id={exploitation['id']}", headers=entetes
        )
        assert liste.status_code == 200
        assert len(liste.json()) == 1

        modification_parcelle = client.put(
            f"/parcelles/{parcelle['id']}",
            json={
                "nom": "Parcelle Test modifiée",
                "surface_ha": 3,
                "exploitation_id": exploitation["id"],
            },
            headers=entetes,
        )
        assert modification_parcelle.status_code == 200
        assert modification_parcelle.json()["nom"] == "Parcelle Test modifiée"
        assert modification_parcelle.json()["surface_ha"] == 3

        creation_culture = client.post(
            f"/parcelles/{parcelle['id']}/cultures",
            json={"espece": "Maïs", "date_semis": "2026-10-01T00:00:00"},
            headers=entetes,
        )
        assert creation_culture.status_code == 201, creation_culture.text
        culture = creation_culture.json()
        assert culture["espece"] == "Maïs"
        assert culture["parcelle_id"] == parcelle["id"]

        cultures = client.get(f"/parcelles/{parcelle['id']}/cultures", headers=entetes)
        assert cultures.status_code == 200
        assert len(cultures.json()) == 1
        assert cultures.json()[0]["espece"] == "Maïs"

        modification_culture = client.put(
            f"/cultures/{culture['id']}",
            json={"espece": "Tomate", "date_semis": "2026-11-01T00:00:00"},
            headers=entetes,
        )
        assert modification_culture.status_code == 200
        assert modification_culture.json()["espece"] == "Tomate"

        fiche = client.get(f"/parcelles/{parcelle['id']}", headers=entetes)
        assert fiche.json()["cultures"][0]["espece"] == "Tomate"

        suppression_culture = client.delete(f"/cultures/{culture['id']}", headers=entetes)
        assert suppression_culture.status_code == 204
        assert client.get(f"/parcelles/{parcelle['id']}/cultures", headers=entetes).json() == []

        suppression_parcelle = client.delete(f"/parcelles/{parcelle['id']}", headers=entetes)
        assert suppression_parcelle.status_code == 204
        assert client.get(f"/parcelles/{parcelle['id']}", headers=entetes).status_code == 404

        suppression_exploitation = client.delete(
            f"/exploitations/{exploitation['id']}", headers=entetes
        )
        assert suppression_exploitation.status_code == 204
        assert client.get(f"/exploitations/{exploitation['id']}", headers=entetes).status_code == 404


def test_validations_et_suppression_en_cascade():
    with TestClient(app) as client:
        entetes, _ = _creer_utilisateur(client, "valid")
        exploitation = _exploitation_principale(client, entetes)

        nom_vide = client.post(
            "/exploitations", json={"nom": "   ", "localisation": ""}, headers=entetes
        )
        assert nom_vide.status_code == 422

        surface_invalide = client.post(
            "/parcelles",
            json={"nom": "Test", "surface_ha": -1, "exploitation_id": exploitation["id"]},
            headers=entetes,
        )
        assert surface_invalide.status_code == 422

        parcelle = client.post(
            "/parcelles",
            json={"nom": "Parcelle cascade", "surface_ha": 1, "exploitation_id": exploitation["id"]},
            headers=entetes,
        ).json()
        culture = client.post(
            f"/parcelles/{parcelle['id']}/cultures",
            json={"espece": "Manioc"},
            headers=entetes,
        )
        assert culture.status_code == 201
        client.post(
            "/humidite/mesures",
            json={"parcelle_id": parcelle["id"], "humidite": 22},
        )

        suppression = client.delete(f"/exploitations/{exploitation['id']}", headers=entetes)
        assert suppression.status_code == 204
        assert client.get(f"/parcelles/{parcelle['id']}", headers=entetes).status_code == 404


def test_isolation_entre_utilisateurs():
    with TestClient(app) as client:
        entetes_a, _ = _creer_utilisateur(client, "alice")
        entetes_b, _ = _creer_utilisateur(client, "bob")
        exploitation_a = _exploitation_principale(client, entetes_a)

        parcelle_a = client.post(
            "/parcelles",
            json={"nom": "Parcelle privée", "surface_ha": 1, "exploitation_id": exploitation_a["id"]},
            headers=entetes_a,
        ).json()

        assert client.get(f"/parcelles/{parcelle_a['id']}", headers=entetes_b).status_code == 404
        assert client.put(
            f"/parcelles/{parcelle_a['id']}",
            json={"nom": "Intrusion", "surface_ha": 9, "exploitation_id": exploitation_a["id"]},
            headers=entetes_b,
        ).status_code == 404
        assert client.delete(f"/parcelles/{parcelle_a['id']}", headers=entetes_b).status_code == 404
        assert client.post(
            f"/parcelles/{parcelle_a['id']}/cultures",
            json={"espece": "Maïs"},
            headers=entetes_b,
        ).status_code == 404

        exploitation_b = _exploitation_principale(client, entetes_b)
        assert exploitation_b["id"] != exploitation_a["id"]
        assert client.post(
            "/parcelles",
            json={"nom": "Vol", "surface_ha": 1, "exploitation_id": exploitation_a["id"]},
            headers=entetes_b,
        ).status_code == 404

