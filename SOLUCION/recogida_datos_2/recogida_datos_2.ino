#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "Adafruit_SGP30.h"

#define SDA_PIN 21
#define SCL_PIN 20

#define MQ7B_PIN 1
#define MQ_VCC 5.0

#define RL 10.0  
#define R0 10.0  
#define A -0.77  
#define B 1.9    

// ==========================
// WIFI / MQTT
// ==========================

const char* ssid     = "iPhone";
const char* password = "aguera38";

const char* mqtt_server = "localhost";
const int mqtt_port = 1883;

const char* TOPIC_TIME = "TimeNow";
const char* TOPIC_SENSORS = "EnviromentalSensorsNetwork";

WiFiClient espClient;
PubSubClient client(espClient);

Adafruit_SGP30 sgp;

String lastUTC = "";

// ==========================
// FUNCIONES LED
// ==========================

void ledPurpleBlink() { rgbLedWrite(RGB_BUILTIN, 255, 0, 255); delay(200); rgbLedWrite(RGB_BUILTIN, 0, 0, 0); delay(200); }
void ledYellowBlink() { rgbLedWrite(RGB_BUILTIN, 255, 255, 0); delay(200); rgbLedWrite(RGB_BUILTIN, 0, 0, 0); delay(200); }

void ledGreen() { rgbLedWrite(RGB_BUILTIN, 0, 255, 0); }
void ledOrangeBlink() { rgbLedWrite(RGB_BUILTIN, 255, 128, 0); delay(300); rgbLedWrite(RGB_BUILTIN, 0, 0, 0); delay(300); }
void ledRedBlink() { rgbLedWrite(RGB_BUILTIN, 255, 0, 0); delay(200); rgbLedWrite(RGB_BUILTIN, 0, 0, 0); delay(200); }

// ==========================
// MQ-7B
// ==========================

float voltageToPPM(float voltage) {
  if (voltage <= 0.01) return 0.0;
  if (voltage >= MQ_VCC) voltage = MQ_VCC - 0.01;

  float RS = RL * (MQ_VCC - voltage) / voltage;
  float ratio = RS / R0;

  if (ratio <= 0) return 0;

  return pow(10, (A * log10(ratio) + B));
}

// ==========================
// WIFI
// ==========================

void connectWiFi() {
  Serial.print("Conectando a WiFi ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    ledPurpleBlink();   // ← MORADO mientras conecta WiFi
    Serial.print(".");
  }

  Serial.println("\n[OK] WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

// ==========================
// CALLBACK MQTT
// ==========================

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;

  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  if (String(topic) == TOPIC_TIME) {
    StaticJsonDocument<128> doc;
    if (!deserializeJson(doc, msg)) {
      if (doc.containsKey("TimeNow")) {
        lastUTC = doc["TimeNow"].as<String>();
        Serial.print("Hora actualizada: ");
        Serial.println(lastUTC);
      }
    }
  }
}

// ==========================
// RECONEXIÓN MQTT
// ==========================

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.println("Conectando a MQTT...");
    ledYellowBlink();  // ← AMARILLO mientras conecta MQTT

    if (client.connect("ESP32S3_B8")) {
      client.subscribe(TOPIC_TIME);
      Serial.println("Suscrito a TimeNow");
    } else {
      delay(1500);
    }
  }

  ledGreen();   // MQTT + WIFI OK → VERDE FIJO
}

// ==========================
// SETUP
// ==========================

void setup() {
  Serial.begin(115200);
  delay(500);

  connectWiFi();

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  Wire.begin(SDA_PIN, SCL_PIN);

  if (!sgp.begin()) {
    Serial.println("ERROR SGP30 no detectado");
    while (1);
  }

  Serial.println("SGP30 OK");
  ledGreen();
}

// ==========================
// LOOP PRINCIPAL
// ==========================

void loop() {
  if (!client.connected()) reconnectMQTT();
  client.loop();

  sgp.IAQmeasure();
  int co2 = sgp.eCO2;
  int tvoc = sgp.TVOC;

  float voltage = analogReadMilliVolts(MQ7B_PIN) / 1000.0;
  float ppmCO = voltageToPPM(voltage);

  // ===============================
  // CONTROL DE LED SEGÚN SENSORES
  // ===============================

  bool peligroModerado =
      ppmCO > 35 || co2 > 1000 || tvoc > 400;

  bool peligroCritico =
      ppmCO > 100 || co2 > 2500 || tvoc > 2000;

  if (peligroCritico) {
    ledRedBlink();
  } else if (peligroModerado) {
    ledOrangeBlink();
  } else {
    ledGreen();  // sistema estable
  }

  if (lastUTC.length() == 0) return;

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

  delay(5000);
}
