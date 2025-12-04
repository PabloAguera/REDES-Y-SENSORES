import json
import paho.mqtt.client as mqtt
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_RAW = os.path.join(BASE_DIR, "messages_raw.jsonl")
FILE_GRAPH = os.path.join(BASE_DIR, "mqtt_data.csv")

BROKER = "localhost"
TOPIC = "EnviromentalSensorsNetwork"

# Crear archivos si no existen
if not os.path.exists(FILE_RAW):
    open(FILE_RAW, "w").close()

if not os.path.exists(FILE_GRAPH):
    pd.DataFrame(columns=["ID", "Tiempo_UTC", "CO2_ppm", "TVOC_ppb", "CO_ppm"]).to_csv(FILE_GRAPH, index=False)

def on_connect(client, userdata, flags, rc):
    print("Conectado:", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    payload = msg.payload.decode().strip()
    print("📩:", payload)

    try:
        data = json.loads(payload)
    except:
        return

    # Guardar JSONL REAL
    with open(FILE_RAW, "a", encoding="utf-8") as f:
        json.dump(data, f)
        f.write("\n")

    # Guardar en CSV solo si es B8
    if data.get("ID") == "B8":
        row = {
            "ID": data.get("ID"),
            "Tiempo_UTC": data.get("Tiempo_UTC"),
            "CO2_ppm": data.get("CO2_ppm"),
            "TVOC_ppb": data.get("TVOC_ppb"),
            "CO_ppm": data.get("CO_ppm"),
        }
        pd.DataFrame([row]).to_csv(FILE_GRAPH, mode="a", header=False, index=False)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)
client.loop_forever()
