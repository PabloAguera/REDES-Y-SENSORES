#Ejecutar después de recogida_datos.py
# streamlit run .\SOLUCION\prueba_streamlit.py

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import time
import os
import hashlib

# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_RAW = os.path.join(BASE_DIR, "messages_raw.jsonl")
FILE_GRAPH = os.path.join(BASE_DIR, "mqtt_data.csv")

st.set_page_config(page_title="IoT Dashboard", layout="wide")
st.title("📡 Dashboard IoT – Sensor Network")

# ============================================================
# CHAT DE MENSAJES
# ============================================================

st.subheader("💬 Mensajes (chat)")

if st.button("🗑️ Limpiar mensajes RAW"):
    open(FILE_RAW, "w").close()
    st.experimental_rerun()

# Leer JSONL
messages = []
if os.path.exists(FILE_RAW):
    with open(FILE_RAW, "r", encoding="utf-8") as f:
        for line in f:
            try:
                messages.append(json.loads(line))
            except:
                pass

messages = messages[::-1]

def color_from_id(sensor_id):
    h = int(hashlib.md5(sensor_id.encode()).hexdigest(), 16)
    r = (h >> 16) & 255
    g = (h >> 8) & 255
    b = h & 255
    return f"rgba({r%200},{g%200},{b%200},0.85)"

# Construir HTML completo
html_chat = """
<div style="
    height:350px;
    overflow-y:auto;
    padding:10px;
    background:#111;
    border-radius:10px;
    border:1px solid #444;
    color:white;
    font-family:monospace;
">
"""

for msg in messages[:80]:
    sensor = msg.get("ID", "UNKNOWN")
    color = color_from_id(sensor)
    pretty = json.dumps(msg, indent=2, ensure_ascii=False).replace("\n", "<br>").replace(" ", "&nbsp;")

    html_chat += f"""
    <div style="
        background:{color};
        padding:12px;
        margin-bottom:12px;
        border-radius:12px;
        box-shadow:0 0 6px rgba(0,0,0,0.4);
        color:black;
    ">
        <strong>{sensor}</strong><br>
        <div style="margin-top:5px;">{pretty}</div>
    </div>
    """

html_chat += "</div>"

# MOSTRAR HTML SIN ESCAPAR
components.html(html_chat, height=400, scrolling=True)


# ============================================================
# GRÁFICAS SENSOR B8
# ============================================================

st.subheader("📊 Gráficas del sensor B8")

if os.path.exists(FILE_GRAPH):
    df = pd.read_csv(FILE_GRAPH)
    df_b8 = df[df["ID"] == "B8"]

    if not df_b8.empty:
        col1, col2, col3 = st.columns(3)

        col1.subheader("CO₂ (ppm)")
        col1.line_chart(df_b8["CO2_ppm"])

        col2.subheader("TVOC (ppb)")
        col2.line_chart(df_b8["TVOC_ppb"])

        col3.subheader("CO (ppm)")
        col3.line_chart(df_b8["CO_ppm"])
    else:
        st.info("Aún no hay datos del sensor B8.")

# ============================================================
# ACTUALIZACIÓN AUTOMÁTICA
# ============================================================

time.sleep(2)
st.experimental_rerun()
