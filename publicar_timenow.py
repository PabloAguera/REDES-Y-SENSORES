import time
import json
from datetime import datetime
import paho.mqtt.client as mqtt

# ⚠ Si el broker está en tu propio PC, deja 'localhost'
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_TIMENOW = "TimeNow"

def get_utc_timestring():
    # Formato: YYYY-DOY-HH:MM:SS (DOY = día del año)
    now = datetime.utcnow()
    return now.strftime("%Y-%j-%H:%M:%S")

def main():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    print(f"Conectado a MQTT en {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Publicando en el topic '{TOPIC_TIMENOW}' cada 10 segundos...\n")

    while True:
        timestr = get_utc_timestring()
        payload = {"TimeNow": timestr}
        client.publish(TOPIC_TIMENOW, json.dumps(payload))
        print("Publicado:", payload)
        time.sleep(10)  # ⏱ cada 10 segundos

if __name__ == "__main__":
    main()
