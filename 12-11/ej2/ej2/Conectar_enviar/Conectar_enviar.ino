// Requiere: PubSubClient, WiFi (ESP8266/ESP32)
// Instalar desde Library Manager: "PubSubClient"

const char* ssid     = "LunarComms4";
const char* password = "11223344";
const char* mqtt_broker = "10.42.0.1";
const uint16_t mqtt_port = 1883;
const char* clientId = "ArduinoPublisher";
const char* topic = "text_test";
const char* message = "Hola desde Arduino";

#include <WiFi.h>          // Para ESP32; en ESP8266 usar <ESP8266WiFi.h>
#include <PubSubClient.h>

WiFiClient espClient;
PubSubClient mqtt(espClient);

void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi conectado. IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Conectando al broker MQTT...");
    if (mqtt.connect(clientId)) {
      Serial.println("conectado");
    } else {
      Serial.print("falló, rc=");
      Serial.print(mqtt.state());
      Serial.println(" - reintentando en 2s");
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  connectWiFi();
  mqtt.setServer(mqtt_broker, mqtt_port);
  connectMQTT();

  // Publica un mensaje (QoS 0 con PubSubClient)
  bool ok = mqtt.publish(topic, message);
  Serial.print("Publicación en ");
  Serial.print(topic);
  Serial.print(ok ? " OK" : " FALLÓ");
  Serial.println();
}

void loop() {
  if (!mqtt.connected()) {
    connectMQTT();
  }
  mqtt.loop();
  // opcional: publicar periódicamente
  // delay(10000);
  // mqtt.publish(topic, "Otro mensaje");
}
