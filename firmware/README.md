# Firmware ESP32 (Emmanuelle)

Outils : VS Code + extension **PlatformIO** (ou Arduino IDE).

## À faire
1. `sevia_capteur/` : lire le capteur capacitif (broche analogique), convertir en % d'humidité,
   publier toutes les 30 s sur MQTT : topic `sevia/parcelle/<ID>/humidite`, payload `{"humidite": 27.4}`.
2. `sevia_vanne/` : s'abonner à `sevia/parcelle/<ID>/commande` (`{"ouvrir": true, "duree_min": 30}`) et piloter le relais.
3. `sevia_camera/` : ESP32-CAM, envoyer une photo toutes les X minutes à `POST /camera/<ID>/images`.

Test sans matériel : `mosquitto_pub -h localhost -t sevia/parcelle/1/humidite -m '{"humidite": 22}'`
(il faut `MQTT_ENABLED=true` dans `backend/.env`).
