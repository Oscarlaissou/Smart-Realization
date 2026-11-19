import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient

from app.main import app


def _utilisateur(client: TestClient):
    suffixe = uuid.uuid4().hex[:10]
    reponse = client.post(
        "/auth/inscription",
        json={
            "nom": "Alerte Test",
            "email": f"alertes-{suffixe}@sevia.cm",
            "nom_exploitation": f"Domaine {suffixe}",
            "mot_de_passe": "secret123",
        },
    )
    assert reponse.status_code == 201, reponse.text
    entetes = {"Authorization": f"Bearer {reponse.json()['access_token']}"}
    exploitation = client.get("/exploitations", headers=entetes).json()[0]
    parcelle = client.post(
        "/parcelles",
        json={"nom": "Parcelle alertes", "surface_ha": 2, "exploitation_id": exploitation["id"]},
        headers=entetes,
    ).json()
    return entetes, parcelle


def test_regles_alertes_et_compteur():
    with TestClient(app) as client:
        entetes, parcelle = _utilisateur(client)

        mesure = client.post(
            "/humidite/mesures",
            json={"parcelle_id": parcelle["id"], "humidite": 22},
            headers=entetes,
        )
        assert mesure.status_code == 201
        # Une seconde mesure basse ne doit pas dupliquer l'alerte.
        client.post("/humidite/mesures", json={"parcelle_id": parcelle["id"], "humidite": 21}, headers=entetes)

        alertes = client.get("/alertes", headers=entetes)
        assert alertes.status_code == 200, alertes.text
        secheresses = [a for a in alertes.json() if a["categorie"] == "secheresse"]
        assert len(secheresses) == 1
        assert secheresses[0]["niveau"] == "urgent"
        assert secheresses[0]["lue"] is False

        compteur = client.get("/alertes/compteur", headers=entetes)
        assert compteur.json()["non_lues"] >= 1

        marquee = client.post(f"/alertes/{secheresses[0]['id']}/lue", headers=entetes)
        assert marquee.status_code == 200
        assert marquee.json()["lue"] is True

        non_lues = client.get("/alertes?non_lues=true", headers=entetes)
        assert all(a["lue"] is False for a in non_lues.json())

        client.post("/alertes/tout-lues", headers=entetes)
        assert client.get("/alertes/compteur", headers=entetes).json()["non_lues"] == 0


def test_email_de_test_sans_smtp(monkeypatch):
    from app.features.alertes import service

    monkeypatch.setattr(service.settings, "SMTP_HOST", "")

    with TestClient(app) as client:
        entetes, _ = _utilisateur(client)
        reponse = client.post("/alertes/test-email", headers=entetes)
        assert reponse.status_code == 400
        assert reponse.json()["detail"] == "Problème lors de l'envoi du mail."


def test_capteur_hors_service_et_preferences():
    with TestClient(app) as client:
        entetes, parcelle = _utilisateur(client)

        equipement = client.post(
            "/equipements",
            json={
                "code": f"C-{uuid.uuid4().hex[:4]}",
                "type": "capteur",
                "parcelle_id": parcelle["id"],
                "en_ligne": False,
            },
            headers=entetes,
        )
        assert equipement.status_code == 201, equipement.text

        # Une alerte d'un autre type ne doit pas apparaître dans le filtre.
        client.post(
            "/humidite/mesures",
            json={"parcelle_id": parcelle["id"], "humidite": 20},
            headers=entetes,
        )

        verification = client.post("/alertes/verifier", headers=entetes)
        assert verification.status_code == 200

        alertes = client.get("/alertes?categorie=capteur", headers=entetes)
        assert alertes.status_code == 200
        assert len(alertes.json()) >= 1
        assert all(a["categorie"] == "capteur" for a in alertes.json())

        secheresses = client.get("/alertes?categorie=secheresse", headers=entetes)
        assert secheresses.status_code == 200
        assert all(a["categorie"] == "secheresse" for a in secheresses.json())

        preferences = client.get("/alertes/preferences", headers=entetes)
        assert preferences.status_code == 200
        assert {p["categorie"] for p in preferences.json()} == {
            "secheresse",
            "exces_eau",
            "capteur",
            "fuite",
            "vanne",
        }

        nouvelle = [
            {
                "categorie": "secheresse",
                "notification": True,
                "email": True,
                "sms": True,
            },
            {"categorie": "capteur", "notification": True, "email": True, "sms": False},
        ]
        enregistrees = client.put("/alertes/preferences", json=nouvelle, headers=entetes)
        assert enregistrees.status_code == 200, enregistrees.text
        par_categorie = {p["categorie"]: p for p in enregistrees.json()}
        assert par_categorie["secheresse"]["email"] is True
        assert par_categorie["secheresse"]["sms"] is True
        assert par_categorie["capteur"]["sms"] is False

        invalide = client.put(
            "/alertes/preferences",
            json=[{"categorie": "inconnue", "notification": True}],
            headers=entetes,
        )
        assert invalide.status_code == 400

