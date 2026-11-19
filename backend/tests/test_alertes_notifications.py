"""Chaque alerte émise : e-mail à l'adresse saisie (s'il y en a une) + diffusion en direct (popup)."""
import asyncio
import json
import uuid

from fastapi.testclient import TestClient

from app.core import temps_reel
from app.core.config import settings
from app.features.alertes import service
from app.main import app


def _compte(c):
    r = c.post("/auth/inscription", json={"nom": "N", "telephone": "", "email": f"n-{uuid.uuid4().hex[:8]}@x.cm",
                                           "nom_exploitation": "E", "mot_de_passe": "secret123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    expl = c.get("/exploitations", headers=h).json()[0]["id"]
    pid = c.post("/parcelles", json={"nom": "Champ", "surface_ha": 1, "exploitation_id": expl}, headers=h).json()["id"]
    return h, pid, r.json()["utilisateur"]["id"]


def _capturer_emails(monkeypatch):
    envoyes = []
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(service, "envoyer_email", lambda dest, sujet, corps: envoyes.append((dest, sujet, corps)) or True)
    monkeypatch.setattr(service, "_en_arriere_plan", lambda f, *args: f(*args))   # synchrone pour le test
    return envoyes


def test_email_a_chaque_alerte_si_une_adresse_est_saisie(monkeypatch):
    envoyes = _capturer_emails(monkeypatch)
    with TestClient(app) as c:
        h, pid, _ = _compte(c)
        # sans adresse : alerte créée mais aucun e-mail
        c.post("/humidite/mesures", json={"parcelle_id": pid, "humidite": 10}, headers=h)
        assert envoyes == []

        r = c.put("/auth/moi", json={"nom": "N", "email_alertes": "alertes@ferme.cm"}, headers=h)
        assert r.status_code == 200 and r.json()["email_alertes"] == "alertes@ferme.cm"
        c.post("/humidite/mesures", json={"parcelle_id": pid, "humidite": 90}, headers=h)   # excès d'eau
        assert len(envoyes) == 1
        dest, sujet, corps = envoyes[0]
        assert dest == "alertes@ferme.cm" and "Excès d'eau" in sujet and "90 %" in corps

        # la page Paramètres (sans ce champ) ne doit pas effacer l'adresse
        c.put("/auth/moi", json={"nom": "N2", "telephone": "", "role": "Exploitant agricole", "langue": "fr"}, headers=h)
        assert c.get("/auth/moi", headers=h).json()["email_alertes"] == "alertes@ferme.cm"
        # vider le champ = plus d'e-mail
        assert c.put("/auth/moi", json={"nom": "N2", "email_alertes": ""}, headers=h).json()["email_alertes"] is None


def test_chaque_alerte_est_diffusee_en_direct(monkeypatch):
    _capturer_emails(monkeypatch)
    with TestClient(app) as c:
        h, pid, uid = _compte(c)

        async def scenario():
            abonne = temps_reel.abonner(uid)
            try:
                await asyncio.to_thread(c.post, "/humidite/mesures", json={"parcelle_id": pid, "humidite": 12}, headers=h)
                recus = [json.loads(await asyncio.wait_for(abonne.file.get(), timeout=2)) for _ in range(2)]
            finally:
                temps_reel.desabonner(abonne)
            types = [e["type"] for e in recus]
            assert types == ["mesure", "alerte"]
            alerte = recus[1]["alerte"]
            assert alerte["message"].startswith("Sol sec") and alerte["categorie"] == "secheresse"

        asyncio.run(scenario())
