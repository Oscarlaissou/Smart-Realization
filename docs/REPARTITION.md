# Répartition des tâches (équitable : 18 points chacun, 72 au total)

Barème : 1 point = environ une demi-journée de travail. Chaque fonctionnalité comprend le back-end (`backend/app/features/<nom>/`) ET le front (`frontend/src/features/<nom>/`) : la personne responsable fait les deux, sauf mention contraire.

| Membre | Fonctionnalités | Points |
|---|---|---|
| **Oscar** (chef) | F1 Authentification (5) · F3 Équipements (5) · F8 Tableau de bord (8) | 18 |
| **Tofa** | F2 Parcelles (6) · F5 Alertes (6) · F10 Qualité transverse (6) | 18 |
| **Emmanuelle** | F9 Firmware ESP32 (9) · F7 Caméra (9) | 18 |
| **Aurelie** | F4 Humidité et irrigation (9) · F6 Fertilisation (9) | 18 |

Oscar assure en plus la coordination (Git, revues de pull requests, planning) : sa charge technique est donc volontairement plafonnée à 18 comme les autres.

## Détail

### F1 Authentification — Oscar (5)
- Page Connexion (formulaire, erreurs, « rester connecté ») et Inscription (1,5)
- Mot de passe oublié et déconnexion (1)
- Validation des champs et messages d'erreur (0,5)
- Protection des routes côté front et rôles de base (1)
- Tests automatiques d'authentification (1)

### F3 Équipements — Oscar (5)
- CRUD capteurs / électrovannes / caméras côté API (1,5)
- Association d'un équipement à une parcelle (1)
- Page Équipements : liste, ajout, état en ligne/hors ligne (2)
- Tests (0,5)

### F8 Tableau de bord — Oscar (8)
- Endpoint des indicateurs clés (eau, humidité, plants, apports, alertes) (2)
- Graphiques d'évolution avec onglets (recharts) (2)
- Filtres période / parcelle / culture (1,5)
- Export PDF, Excel et CSV (2)
- Tests (0,5)

### F2 Parcelles — Tofa (6)
- CRUD exploitations, parcelles, cultures : finir l'API et les validations (2)
- Page Parcelles : liste, création, modification, suppression (2,5)
- Fiche parcelle avec cultures (1)
- Tests (0,5)

### F5 Alertes — Tofa (6)
- Règles d'alerte (seuils, capteur hors service) dans `alertes/service.py` (1,5)
- Notification dans l'application (cloche, compteur) (1)
- Envoi par e-mail et par SMS (2)
- Page Alertes et préférences par canal (1,5)

### F10 Qualité transverse — Tofa (6)
- Mise en page commune (menu, en-tête, thème vert) et responsive tablette / téléphone (2,5)
- Internationalisation : français + 1 autre langue (1,5)
- Accessibilité : contraste élevé, navigation clavier (1)
- Paramètres : profil, langue, sécurité, sauvegardes (1)

### F9 Firmware ESP32 — Emmanuelle (9)
- Capteur : lecture, étalonnage, envoi MQTT toutes les 30 s (3)
- Électrovanne : réception des commandes et pilotage du relais (3)
- ESP32-CAM : capture et envoi d'images à l'API (2)
- Reconnexion Wi-Fi/MQTT et tests sur banc (1)

### F7 Caméra — Emmanuelle (9)
- Réception et stockage des images (`camera/router.py`) (1,5)
- Comptage des plants avec YOLO (`camera/service.py`) (3,5)
- Page Suivi par caméra : image avec détections, nombre de plants (2)
- Évolution du comptage et comparaison par date (1,5)
- Tests (0,5)

### F4 Humidité et irrigation — Aurelie (9)
- Base de données : modèles, migrations Alembic (1,5)
- Réception des mesures MQTT et historique (1,5)
- Irrigation automatique / manuelle et commande de l'électrovanne (2)
- Programmation des cycles et journal des irrigations (1,5)
- Page Humidité et irrigation (jauge, courbe 24 h, pilotage) (2)
- Tests (0,5)

### F6 Fertilisation — Aurelie (9)
- Saisie et import (CSV) des données agronomiques (2)
- Calcul des doses recommandées par culture (`fertilisation/service.py`) (2,5)
- Ajustement manuel de la dose et enregistrement des apports (1,5)
- Calendrier des apports et rappels (1,5)
- Page Fertilisation (1,5)

## Ordre conseillé
1. Tout le monde : installer l'environnement, créer sa branche.
2. F1, F2 et F3 d'abord (les autres fonctionnalités en dépendent), puis F4 et F9 (les mesures arrivent), puis F5, F6, F7, F8, F10.
3. Une pull request par fonctionnalité, relue par une autre personne.
