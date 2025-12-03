import json
import time
import paho.mqtt.client as mqtt

BROKER = "10.42.0.1"
PORT = 1883

TOPIC_SENSORS = "Enviromental Sensors Network"
TOPIC_TIME = "TimeNow"

OWN_ID = "B8"

# Últimas lecturas guardadas
sensors = {}
current_time_utc = None   # Se actualiza desde TimeNow


def print_sensor(id_, entry):
    """Imprime todos los datos enviados por un sensor."""
    t = entry.get("time", "unknown")
    data = entry["data"]

    print(f"[{t}] ID={id_}")
    for k, v in data.items():
        if k not in ("ID", "Tiempo_UTC"):
            print(f"   {k}: {v}")


def on_connect(client, userdata, flags, rc):
    print("Conectado al broker, código:", rc)

    client.subscribe(TOPIC_TIME)
    print(f"Suscrito a: {TOPIC_TIME}")

    client.subscribe(TOPIC_SENSORS)
    print(f"Suscrito a: {TOPIC_SENSORS}")


def on_message(client, userdata, msg):
    global current_time_utc

    payload = msg.payload.decode(errors="ignore")

    # --------------------------------------------------------------------
    # 1) Mensajes de TimeNow → actualizar tiempo global
    # --------------------------------------------------------------------
    if msg.topic == TOPIC_TIME:
        try:
            data = json.loads(payload)
            current_time_utc = data.get("TimeNow", None)
            print(f"[TimeNow] Hora UTC actualizada → {current_time_utc}")
        except Exception:
            print("TimeNow recibió JSON inválido:", payload)
        return

    # --------------------------------------------------------------------
    # 2) Mensajes de sensores → integrar hora UTC y mostrar datos
    # --------------------------------------------------------------------
    if msg.topic == TOPIC_SENSORS:
        try:
            data = json.loads(payload)
        except Exception:
            print("Mensaje no JSON recibido:", payload)
            return

        sensor_id = data.get("ID")
        if not sensor_id:
            print("JSON sin campo ID:", data)
            return

        # Si aún no recibimos TimeNow, usar timestamp del sistema
        timestamp = current_time_utc or time.strftime("%Y-%j-%H:%M:%S", time.gmtime())

        # Inyectamos el tiempo en el JSON que envió el sensor
        data["Tiempo_UTC"] = timestamp

        # Guardamos la lectura
        sensors[sensor_id] = {"time": timestamp, "data": data}

        # Mostrar datos del sensor
        if sensor_id == OWN_ID:
            print(">>> Lectura propia (OWN_ID):")
        else:
            print("Lectura de otro sensor recibida:")

        print_sensor(sensor_id, sensors[sensor_id])

        # ----------------------------------------------------------------
        # Resumen dinámico de *todos* los sensores
        # ----------------------------------------------------------------
        print("-- Resumen actual de sensores --")
        for sid, entry in sensors.items():
            campos = []
            for k, v in entry["data"].items():
                if k not in ("ID", "Tiempo_UTC"):
                    campos.append(f"{k}={v}")
            campos_txt = ", ".join(campos)
            print(f"  {sid}: {campos_txt}")
        print("--------------------------------\n")

        return


def main():
    client = mqtt.Client(client_id=f"py-subscriber-{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, 60)
    except Exception as e:
        print("Error conectando al broker:", e)
        return

    client.loop_forever()


if __name__ == "__main__":
    main()
