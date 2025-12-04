#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "Adafruit_SGP30.h"

// ============================================================
// CONFIGURACIÓN DE PINES (ESP32-S3)
// ============================================================

// SGP30 → I2C
#define SDA_PIN 21
#define SCL_PIN 20

// MQ-7B → ANALÓGICO (ADC1_CH1)
#define MQ7B_PIN 1      
#define MQ_VCC 5.0

// Parámetros MQ-7B
#define RL 10.0  
#define R0 10.0  
#define A -0.77  
#define B 1.9    

// ============================================================
// CONFIGURACIÓN WIFI / MQTT
// ============================================================

const char* ssid     = "LunarLink";
const char* password = "11223344";

const char* mqtt_server = "192.168.0.88";  // <-- CAMBIAR por tu servidor MQTT
const int mqtt_port = 1883;

const char* TOPIC_TIME = "TimeNow";
const char* TOPIC_SENSORS = "Enviromental Sensors Network";

WiFiClient espClient;
PubSubClient client(espClient);

Adafruit_SGP30 sgp;

String lastUTC = "";

// ============================================================
// MQ-7B: Conversión VOLTAJE → PPM
// ============================================================

float voltageToPPM(float voltage) {
  if (voltage <= 0.01) return 0.0;
  if (voltage >= MQ_VCC) voltage = MQ_VCC - 0.01;

  float RS = RL * (MQ_VCC - voltage) / voltage;
  float ratio = RS / R0;

  if (ratio <= 0) return 0;

  return pow(10, (A * log10(ratio) + B));
}

// ============================================================
// WIFI
// ============================================================

void connectWiFi() {
  Serial.print("Conectando a WiFi ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n[OK] WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// ============================================================
// CALLBACK MQTT
// ============================================================

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Mensaje recibido en topic: ");
  Serial.println(topic);

  String msg;
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  Serial.print("Payload: ");
  Serial.println(msg);

  if (String(topic) == TOPIC_TIME) {   // TOPIC_TIME = "TimeNow"
    StaticJsonDocument<128> doc;
    DeserializationError error = deserializeJson(doc, msg);

    if (error) {
      Serial.print("Error parseando JSON de TimeNow: ");
      Serial.println(error.c_str());
      return;
    }

    if (doc.containsKey("TimeNow")) {
      // Guardamos exactamente lo que viene, por ejemplo "2025-337-16:11:39"
      lastUTC = doc["TimeNow"].as<String>();
      Serial.print("Hora actualizada desde TimeNow: ");
      Serial.println(lastUTC);
    } else {
      Serial.println("El JSON recibido NO tiene la clave 'TimeNow'");
    }
  }
}


// ============================================================
// RECONEXIÓN MQTT
// ============================================================

void reconnectMQTT() {
  while (!client.connected()) {
    if (client.connect("ESP32S3_B8")) {
      client.subscribe(TOPIC_TIME);
      Serial.println("Suscrito a TimeNow");
    } else {
      delay(3000);
    }
  }
}

// ============================================================
// SETUP
// ============================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("🚀 Iniciando ESP32-S3 + SGP30 + MQ-7B");

  connectWiFi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  // Inicializar I2C
  Wire.begin(SDA_PIN, SCL_PIN);

  if (!sgp.begin()) {
    Serial.println("ERROR SGP30 no detectado");
    while (1);
  }

  Serial.println("SGP30 OK");
}

// ============================================================
// LOOP PRINCIPAL
// ============================================================

void loop() {
  if (!client.connected()) reconnectMQTT();
  client.loop();

  // Leer SGP30
  sgp.IAQmeasure();
  int co2 = sgp.eCO2;
  int tvoc = sgp.TVOC;

  // Leer MQ-7B
  float voltage = analogReadMilliVolts(MQ7B_PIN) / 1000.0;
  float ppmCO = voltageToPPM(voltage);

  if (lastUTC.length() == 0) return;

  // Crear JSON
  StaticJsonDocument<256> doc;
  doc["ID"] = "B8";
  doc["Tiempo_UTC"] = lastUTC;
  doc["CO2_ppm"] = co2;
  doc["TVOC_ppb"] = tvoc;
  doc["CO_ppm"] = ppmCO;

  char out[256];
  serializeJson(doc, out);

  client.publish(TOPIC_SENSORS, out);

  Serial.println(out);
  Serial.println("--------------------------");

  delay(10000);
}
