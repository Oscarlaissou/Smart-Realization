<<<<<<< HEAD
# Sevia – Optimisation des ressources des plantations

Architecture : **front React (Vue MVC)** ⇄ **API FastAPI (Contrôleurs + Services + Modèles)** ⇄ **PostgreSQL**, avec **ESP32** → **MQTT** → API.

```
backend/app/
  core/            configuration, base de données, sécurité (commun)
  features/<nom>/  UNE FONCTIONNALITÉ = models.py (MODÈLE), schemas.py, router.py (CONTRÔLEUR), service.py (logique)
                   auth · parcelles · equipements · humidite · alertes · fertilisation · camera · dashboard
  mqtt/            réception des mesures des capteurs
frontend/src/
  features/<nom>/  VUE : pages React, components/, api.js de la fonctionnalité
  services/api.js  appels HTTP communs · i18n/ traductions
firmware/          code ESP32
docs/REPARTITION.md  qui fait quoi
```

## Installation (une seule fois)

Pré-requis : Git, Python 3.11+, Node.js LTS, Docker Desktop, VS Code.

```bash
git clone <URL_DU_DEPOT> sevia && cd sevia

# 1. Base de données + broker MQTT
docker compose up -d

# 2. Back-end
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows   |   source .venv/bin/activate  (Mac/Linux)
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000/docs

# 3. Front-end (autre terminal)
cd frontend
npm install
npm run dev                     # http://localhost:5173

# 4. Tests
cd backend && pytest
```

Avant de coder, lire `docs/REPARTITION.md` (tâches de chacun).

## Vérifier que tout marche
1. Ouvrir http://localhost:8000/docs → créer un compte (`POST /auth/register`) puis `Authorize`.
2. Créer une exploitation puis une parcelle.
3. Simuler un capteur : `POST /humidite/mesures` avec `{"parcelle_id":1,"humidite":22}` → une alerte « Sol sec » apparaît dans `GET /alertes`.

## Pour avancer sur une fonctionnalité
Branche → travailler uniquement dans le dossier `features/<nom>` de la fonctionnalité (service, routeur, puis page React) → test → pull request.
Les `TODO` dans le code indiquent où continuer.
=======
# Smart-Realization
Application web d'optimisation des ressources des plantations agricoles pour un développement durable
>>>>>>> fd266c2e9b2664f198f0da1550391c01d3d418e0
