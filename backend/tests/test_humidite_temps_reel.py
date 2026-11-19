"""Mesures d'humidité en temps réel : alertes de seuil haut/bas et diffusion au propriétaire."""
import asyncio
import json
import uuid

from fastapi.testclient import TestClient

from app.core import temps_reel
from app.main import app


def _compte(client, nom):
    r = client.post("/auth/inscription", json={"nom": nom, "telephone": "", "email": f"{nom}-{uuid.uuid4().hex[:8]}@x.cm",
                                                "nom_exploitation": "E", "mot_de_passe": "secret123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    expl = client.get("/exploitations", headers=h).json()[0]["id"]
    pid = client.post("/parcelles", json={"nom": f"Champ {nom}", "surface_ha": 1, "exploitation_id": expl,
                                          "seuil_humidite_min": 30, "seuil_humidite_max": 60}, headers=h).json()["id"]
    return h, pid, r.json()["utilisateur"]["id"]


def test_alertes_seuil_bas_et_haut():
    with TestClient(app) as c:
        h, pid, _ = _compte(c, "seuils")
        bas = c.post("/humidite/mesures", json={"parcelle_id": pid, "humidite": 20}, headers=h).json()
        haut = c.post("/humidite/mesures", json={"parcelle_id": pid, "humidite": 75}, headers=h).json()
        ok = c.post("/humidite/mesures", json={"parcelle_id": pid, "humidite": 45}, headers=h).json()

        assert bas["hors_seuil"] == "bas" and bas["alerte"]["message"].startswith("Sol sec")
        assert haut["hors_seuil"] == "haut" and haut["alerte"]["message"].startswith("Excès d'eau")
        assert ok["hors_seuil"] is None and ok["alerte"] is None
        messages = [a["message"] for a in c.get("/alertes", headers=h).json()]
        assert any(m.startswith("Sol sec") for m in messages) and any(m.startswith("Excès d'eau") for m in messages)
        # la mesure apparaît immédiatement dans l'aperçu
        carte = c.get("/humidite/apercu", headers=h).json()["parcelles"][0]
        assert carte["humidite_actuelle"] == 45


def test_mesure_diffusee_au_seul_proprietaire():
    with TestClient(app) as c:
        h, pid, uid = _compte(c, "moi")
        h_autre, pid_autre, uid_autre = _compte(c, "autre")

        async def scenario():
            moi, autre = temps_reel.abonner(uid), temps_reel.abonner(uid_autre)
            try:
                await asyncio.to_thread(
                    c.post, "/humidite/mesures", json={"parcelle_id": pid, "humidite": 22}, headers=h
                )
                recu = json.loads(await asyncio.wait_for(moi.file.get(), timeout=2))
                assert recu["parcelle_id"] == pid and recu["valeur"] == 22 and recu["hors_seuil"] == "bas"
                assert autre.file.empty()
            finally:
                temps_reel.desabonner(moi)
                temps_reel.desabonner(autre)

        asyncio.run(scenario())
        # et on ne peut pas envoyer de mesure sur la parcelle d'un autre
        assert c.post("/humidite/mesures", json={"parcelle_id": pid_autre, "humidite": 50}, headers=h).status_code == 404


def test_flux_refuse_sans_jeton():
    with TestClient(app) as c:
        assert c.get("/humidite/flux").status_code == 401
