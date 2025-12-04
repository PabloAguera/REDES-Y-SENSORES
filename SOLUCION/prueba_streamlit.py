import streamlit as st
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

st.subheader("📨 Log de mensajes (JSON)")

if st.button("🗑️ Limpiar mensajes RAW"):
    open(FILE_RAW, "w").close()
    st.experimental_rerun()

# Leer mensajes JSONL
messages = []
if os.path.exists(FILE_RAW):
    with open(FILE_RAW, "r", encoding="utf-8") as f:
        for line in f:
            try:
                messages.append(json.loads(line))
            except:
                pass

messages = messages[::-1]  # recientes primero

# Ventana scroll simple sin estilos
scroll_html = """
<div style="
    height:350px;
    overflow-y:auto;
    padding:10px;
    background-color:#222;
    border:1px solid #555;
    border-radius:8px;
    color:white;
    font-family:monospace;
">
"""

for msg in messages[:100]:
    pretty = json.dumps(msg, indent=2, ensure_ascii=False).replace("\n", "<br>")
    scroll_html += f"{pretty}<hr style='border-color:#444;'>"

scroll_html += "</div>"

st.markdown(scroll_html, unsafe_allow_html=True)


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
