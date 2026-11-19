"""Non-régression des 4 incohérences critiques corrigées (capteurs, tableau de bord, seuils, jetons)."""
import uuid

from fastapi.testclient import TestClient
from jose import jwt

from app.core import security
from app.core.config import settings
from app.core.database import SessionLocal
from app.features.humidite.models import MesureHumidite
from app.main import app
from app.mqtt.listener import _extraire_mesure


def _compte(client: TestClient, nom: str):
    email = f"{nom}-{uuid.uuid4().hex[:8]}@sevia.cm"
    r = client.post(
        "/auth/inscription",
        json={"nom": nom, "telephone": "", "email": email, "nom_exploitation": "E", "mot_de_passe": "secret123"},
    )
    assert r.status_code == 201, r.text
    entetes = {"Authorization": f"Bearer {r.json()['access_token']}"}
    exploitation = client.get("/exploitations", headers=entetes).json()[0]["id"]
    return entetes, exploitation


def _parcelle(client, entetes, exploitation, nom, **extra):
    r = client.post(
        "/parcelles",
        json={"nom": nom, "surface_ha": 1, "exploitation_id": exploitation, **extra},
        headers=entetes,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _mesure(parcelle_id: int, valeur: float):
    db = SessionLocal()
    db.add(MesureHumidite(parcelle_id=parcelle_id, valeur=valeur))
    db.commit()
    db.close()


def test_le_message_du_firmware_esp32_est_lu():
    # Format exact publié par firmware/sevia_capteur/sevia_capteur.ino
    assert _extraire_mesure("sevia/parcelle/7/humidite", '{"humidite": 27.4}') == (7, 27.4)
    assert _extraire_mesure("sevia/parcelles/7/humidite", '{"humidite": 27.4}') == (7, 27.4)
    assert _extraire_mesure("sevia/autre/humidite", '{"humidite": 27.4}') == (None, None)


def test_le_tableau_de_bord_ne_montre_que_mes_parcelles():
    with TestClient(app) as client:
        alice, expl_a = _compte(client, "alice")
        bob, expl_b = _compte(client, "bob")
        _parcelle(client, alice, expl_a, "Champ d'Alice")
        _parcelle(client, bob, expl_b, "Champ de Bob")
        client.post("/equipements", json={"code": "CAP-A", "type": "capteur"}, headers=alice)

        donnees = client.get("/dashboard/indicateurs", headers=bob).json()
        assert [p["nom"] for p in donnees["parcelles"]] == ["Champ de Bob"]
        assert donnees["domaine"]["equipements_total"] == 0


def test_les_alertes_suivent_les_seuils_de_la_parcelle():
    with TestClient(app) as client:
        moi, expl = _compte(client, "seuils")
        defaut = _parcelle(client, moi, expl, "Seuils par défaut")
        regle = _parcelle(client, moi, expl, "Seuils réglés", seuil_humidite_min=20, seuil_humidite_max=50)
        _mesure(defaut, 55)   # 30-65 % par défaut : optimal, aucune alerte
        _mesure(regle, 55)    # 20-50 % : excès d'eau

        messages = [a["message"] for a in client.get("/alertes", headers=moi).json()]
        assert not any("Seuils par défaut" in m for m in messages)
        assert any(m.startswith("Excès d'eau · Seuils réglés") for m in messages)

        cartes = {c["nom"]: c for c in client.get("/humidite/apercu", headers=moi).json()["parcelles"]}
        assert cartes["Seuils par défaut"]["statut"] == "optimal"
        assert cartes["Seuils réglés"]["statut"] == "sature"


def test_les_jetons_sont_signes_avec_la_cle_du_env():
    assert security.SECRET_KEY == settings.SECRET_KEY
    faux = jwt.encode({"sub": "1"}, "sevia_cle_secrete_supabase_2026_fixe", algorithm="HS256")
    if settings.SECRET_KEY != "sevia_cle_secrete_supabase_2026_fixe":
        with TestClient(app) as client:
            r = client.get("/auth/moi", headers={"Authorization": f"Bearer {faux}"})
            assert r.status_code == 401
