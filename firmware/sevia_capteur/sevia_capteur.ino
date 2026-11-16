// Squelette : lecture du capteur et envoi MQTT (bibliothèque PubSubClient). À compléter.
#include <WiFi.h>
#include <PubSubClient.h>
const char* WIFI_SSID = "A_REMPLIR";
const char* WIFI_PASS = "A_REMPLIR";
const char* MQTT_HOST = "A_REMPLIR";   // IP du serveur
const int   PARCELLE_ID = 1;
const int   PIN_CAPTEUR = 34;
WiFiClient wifi; PubSubClient mqtt(wifi);

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  mqtt.setServer(MQTT_HOST, 1883);
}
void loop() {
  if (!mqtt.connected()) mqtt.connect("esp32-parcelle-1");
  int brut = analogRead(PIN_CAPTEUR);
  float humidite = map(brut, 3200, 1400, 0, 100);   // TODO : étalonner (sol sec / sol saturé)
  char topic[48], msg[48];
  snprintf(topic, sizeof topic, "sevia/parcelle/%d/humidite", PARCELLE_ID);
  snprintf(msg, sizeof msg, "{\"humidite\": %.1f}", humidite);
  mqtt.publish(topic, msg);
  delay(30000);
}
