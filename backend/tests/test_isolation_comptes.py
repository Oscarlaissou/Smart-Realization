"""Isolation entre comptes : un utilisateur n'accède QU'À ses propres données, sur toutes les pages.

Alice crée des données de chaque type ; Bob tente de les lire, modifier ou supprimer
avec les identifiants d'Alice. Chaque tentative doit échouer (404) et les listes de Bob
ne doivent jamais contenir quoi que ce soit d'Alice.
"""
import json
import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.features.alertes.models import Alerte
from app.features.camera.models import Comptage
from app.features.humidite.models import MesureHumidite
from app.main import app

SECRET = "ALICE-SECRET"


def _compte(client, nom):
    r = client.post(
        "/auth/inscription",
        json={"nom": nom, "telephone": "", "email": f"{nom}-{uuid.uuid4().hex[:8]}@sevia.cm",
              "nom_exploitation": f"Exploitation {nom}", "mot_de_passe": "secret123"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _donnees_alice(client, h):
    expl = client.post("/exploitations", json={"nom": f"Ferme {SECRET}"}, headers=h).json()["id"]
    pid = client.post("/parcelles", json={"nom": f"Parcelle {SECRET}", "surface_ha": 2,
                                          "exploitation_id": expl}, headers=h).json()["id"]
    cid = client.post(f"/parcelles/{pid}/cultures", json={"espece": f"Maïs {SECRET}"}, headers=h).json()["id"]
    eid = client.post("/equipements", json={"code": f"CAP-{SECRET}", "type": "capteur",
                                            "parcelle_id": pid}, headers=h).json()["id"]
    assert client.post("/humidite/arrosages", json={"parcelle_id": pid, "volume_litres": 50,
                                                    "notes": SECRET}, headers=h).status_code == 201
    assert client.post("/fertilisation/donnees", json={"parcelle_id": pid, "azote": 10}, headers=h).status_code == 201
    assert client.post("/fertilisation/apports", json={"parcelle_id": pid, "engrais": f"NPK {SECRET}",
                                                       "dose_kg_ha": 100, "realise": True}, headers=h).status_code == 201
    db = SessionLocal()
    db.add(MesureHumidite(parcelle_id=pid, valeur=12))
    db.add(Comptage(parcelle_id=pid, image_path=f"camera/{pid}/{SECRET}.jpg", nb_plants=321))
    db.add(Alerte(parcelle_id=pid, niveau="urgent", message=f"Sol sec · {SECRET}", date=datetime.utcnow()))
    db.commit()
    aid = db.query(Alerte).filter(Alerte.parcelle_id == pid).first().id
    db.close()
    return {"expl": expl, "pid": pid, "cid": cid, "eid": eid, "aid": aid}


def test_un_utilisateur_n_accede_qu_a_ses_donnees():
    with TestClient(app) as c:
        alice, bob = _compte(c, "alice"), _compte(c, "bob")
        a = _donnees_alice(c, alice)
        p, e = a["pid"], a["eid"]

        # 1. Lectures, modifications et suppressions ciblant les données d'Alice : toutes refusées
        tentatives = [
            ("GET", f"/exploitations/{a['expl']}", None),
            ("PUT", f"/exploitations/{a['expl']}", {"nom": "piratée"}),
            ("DELETE", f"/exploitations/{a['expl']}", None),
            ("GET", f"/parcelles/{p}", None),
            ("PUT", f"/parcelles/{p}", {"nom": "piratée", "surface_ha": 1, "exploitation_id": a["expl"]}),
            ("DELETE", f"/parcelles/{p}", None),
            ("POST", f"/parcelles/{p}/equipements", {"equipement_id": e}),
            ("DELETE", f"/parcelles/{p}/equipements/{e}", None),
            ("GET", f"/parcelles/{p}/cultures", None),
            ("POST", f"/parcelles/{p}/cultures", {"espece": "piratée"}),
            ("PUT", f"/cultures/{a['cid']}", {"espece": "piratée"}),
            ("DELETE", f"/cultures/{a['cid']}", None),
            ("PUT", f"/equipements/{e}", {"code": "piraté", "type": "capteur"}),
            ("DELETE", f"/equipements/{e}", None),
            ("POST", "/humidite/arrosages", {"parcelle_id": p, "volume_litres": 1}),
            ("PATCH", f"/humidite/parcelles/{p}/seuils", {"seuil_humidite_min": 1, "seuil_humidite_max": 2}),
            ("POST", f"/alertes/{a['aid']}/lue", None),
            ("POST", "/fertilisation/donnees", {"parcelle_id": p, "azote": 1}),
            ("GET", f"/fertilisation/donnees/{p}", None),
            ("GET", f"/fertilisation/dose/{p}", None),
            ("POST", "/fertilisation/apports", {"parcelle_id": p, "engrais": "x", "dose_kg_ha": 1}),
            ("GET", f"/camera/{p}/comptages", None),
            ("POST", f"/camera/{p}/importer", None),
        ]
        for methode, chemin, corps in tentatives:
            r = c.request(methode, chemin, headers=bob, json=corps)
            assert r.status_code in (403, 404), f"{methode} {chemin} -> {r.status_code} {r.text[:120]}"
        # Associer son propre équipement à la parcelle d'Alice / y rattacher un équipement
        mon_eq = c.post("/equipements", json={"code": "BOB-1", "type": "vanne"}, headers=bob).json()["id"]
        assert c.post(f"/parcelles/{p}/equipements", json={"equipement_id": mon_eq}, headers=bob).status_code == 404
        assert c.put(f"/equipements/{mon_eq}", json={"code": "BOB-1", "type": "vanne", "parcelle_id": p},
                     headers=bob).status_code == 404

        # 2. Aucune page de Bob ne contient de donnée d'Alice
        pages = ["/exploitations", "/parcelles", "/equipements", "/humidite/apercu", "/alertes",
                 "/alertes/compteur", "/fertilisation/apports", "/camera/parcelles",
                 "/dashboard/indicateurs", "/dashboard/export", "/auth/moi", "/auth/export"]
        for page in pages:
            r = c.get(page, headers=bob)
            assert r.status_code == 200, f"{page} -> {r.status_code}"
            assert SECRET not in r.text, f"{page} expose des données d'Alice"
        assert c.get("/alertes/compteur", headers=bob).json() == {"non_lues": 0, "total": 0}

        # 3. Les données d'Alice sont intactes et visibles par Alice
        assert c.get(f"/parcelles/{p}", headers=alice).json()["nom"] == f"Parcelle {SECRET}"
        assert [x["code"] for x in c.get("/equipements", headers=alice).json()] == [f"CAP-{SECRET}"]
        assert SECRET in json.dumps(c.get("/humidite/apercu", headers=alice).json())
        assert any(SECRET in x["message"] for x in c.get("/alertes", headers=alice).json())
        assert c.get(f"/fertilisation/dose/{p}", headers=alice).status_code == 200


def test_sans_jeton_aucune_donnee():
    with TestClient(app) as c:
        for page in ["/parcelles", "/equipements", "/humidite/apercu", "/alertes", "/fertilisation/apports",
                     "/camera/parcelles", "/dashboard/indicateurs", "/auth/export", "/exploitations"]:
            assert c.get(page).status_code == 401, page
