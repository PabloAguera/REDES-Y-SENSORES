import json
import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from collections import deque
import threading
import time

# ----------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------
BROKER = "192.168.0.88"
TOPIC = "Enviromental Sensors Network"
TARGET_ID = "B8"

MAX_POINTS = 200

time_buf = deque(maxlen=MAX_POINTS)
co2_buf = deque(maxlen=MAX_POINTS)
tvoc_buf = deque(maxlen=MAX_POINTS)
co_buf = deque(maxlen=MAX_POINTS)

# ----------------------------------------------------------
# MQTT CALLBACKS
# ----------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    print("Conectado al broker:", rc)
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    payload_raw = msg.payload.decode("utf-8").strip()
    print("Mensaje recibido:", payload_raw)

    # Intentamos cargar JSON (si no es JSON, se ignora)
    try:
        data = json.loads(payload_raw)
    except:
        return

    # Filtrar ID
    if data.get("ID") != TARGET_ID:
        return

    # Extraer datos exactos del topic
    co2 = float(data.get("CO2_ppm", 0))
    tvoc = float(data.get("TVOC_ppb", 0))
    co = float(data.get("CO_ppm", 0))
    t = data.get("Tiempo_UTC", time.time())

    time_buf.append(t)
    co2_buf.append(co2)
    tvoc_buf.append(tvoc)
    co_buf.append(co)


# ----------------------------------------------------------
# HILO MQTT
# ----------------------------------------------------------
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)
    client.loop_forever()


# Lanzamos MQTT en un hilo separado
thread = threading.Thread(target=start_mqtt, daemon=True)
thread.start()

# ----------------------------------------------------------
# GRAFICADO EN TIEMPO REAL
# ----------------------------------------------------------
plt.ion()
fig, ax = plt.subplots()

line_co2, = ax.plot([], [], label="CO2 (ppm)")
line_tvoc, = ax.plot([], [], label="TVOC (ppb)")
line_co, = ax.plot([], [], label="CO (ppm)")

ax.set_xlabel("Tiempo UTC")
ax.set_title("Lecturas ID B8 – MQTT")
ax.legend()

# Bucle principal de refresco
while True:
    if len(time_buf) > 0:
        line_co2.set_data(range(len(co2_buf)), co2_buf)
        line_tvoc.set_data(range(len(tvoc_buf)), tvoc_buf)
        line_co.set_data(range(len(co_buf)), co_buf)

        ax.relim()
        ax.autoscale_view()

        plt.pause(0.5)

    time.sleep(0.1)
