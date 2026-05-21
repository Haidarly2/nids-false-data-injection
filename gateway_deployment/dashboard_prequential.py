import streamlit as st
import socket
import json
import time
import pickle
import pandas as pd
from river import metrics

st.set_page_config(page_title="NIDS Prequential Gateway", layout="wide")


# =======================================================
# 1. INISIALISASI STATE & PREQUENTIAL ENGINE
# =======================================================
def inisialisasi_state():
    if "server_berjalan" not in st.session_state:
        st.session_state.server_berjalan = False

    if "model" not in st.session_state:
        # Kita menggunakan ver3.pkl sebagai fondasi kecerdasan awal,
        # namun nanti ia akan terus diperbarui secara live!
        with open("../model_nids_terlatih_ver3.pkl", "rb") as f:
            st.session_state.model = pickle.load(f)

    if "metric_acc" not in st.session_state:
        # Metrik River untuk evaluasi instan
        st.session_state.metric_acc = metrics.Accuracy()
        st.session_state.metric_f1 = metrics.F1()

    if "history_acc" not in st.session_state:
        st.session_state.history_acc = []

    if "total_paket" not in st.session_state:
        st.session_state.total_paket = 0
        st.session_state.trafik_normal = 0
        st.session_state.trafik_anomali = 0
        st.session_state.log_anomali = []


inisialisasi_state()

# =======================================================
# 2. ANTARMUKA STREAMLIT
# =======================================================
st.title("🛡️ NIDS Gateway - True Online Learning")
st.markdown(
    "**Skenario:** Prequential Evaluation (Test-Then-Train) dengan Data Sintetis Dinamis"
)

col_btn1, col_btn2 = st.columns([1, 8])
with col_btn1:
    if st.button("▶️ Buka Gateway"):
        st.session_state.server_berjalan = True
with col_btn2:
    if st.button("⏹️ Tutup Gateway"):
        st.session_state.server_berjalan = False

# Wadah (Placeholder) untuk metrik dan grafik agar bisa di-update real-time
placeholder_metrik = st.empty()
placeholder_grafik = st.empty()
placeholder_tabel = st.empty()


def update_ui():
    """Fungsi untuk merender ulang UI dengan data terbaru"""
    # 1. Update Kartu Metrik
    with placeholder_metrik.container():
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Paket", f"{st.session_state.total_paket:,}")
        c2.metric("Trafik Normal", f"{st.session_state.trafik_normal:,}")
        c3.metric("🚨 Anomali (FDI)", f"{st.session_state.trafik_anomali:,}")
        c4.metric("Akurasi (Live)", f"{st.session_state.metric_acc.get()*100:.2f}%")
        c5.metric("F1-Score (Live)", f"{st.session_state.metric_f1.get()*100:.2f}%")

    # 2. Update Grafik Garis (Line Chart)
    with placeholder_grafik.container():
        if len(st.session_state.history_acc) > 0:
            df_chart = pd.DataFrame({"Akurasi": st.session_state.history_acc})
            st.line_chart(df_chart, height=250)

    # 3. Update Tabel Log
    with placeholder_tabel.container():
        if st.session_state.log_anomali:
            st.error("⚠️ Log Deteksi Serangan Terakhir:")
            st.dataframe(
                pd.DataFrame(st.session_state.log_anomali), use_container_width=True
            )


# =======================================================
# 3. MESIN JARINGAN & SIKLUS TEST-THEN-TRAIN
# =======================================================
def mulai_server():
    HOST = "127.0.0.1"
    PORT = 9999

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()

        update_ui()
        st.info("Menunggu tembakan data dari Generator Sintetis...")

        conn, addr = s.accept()
        with conn:
            st.success(
                f"Generator terhubung dari {addr}! Memulai siklus Prequential..."
            )
            file_stream = conn.makefile("r", encoding="utf-8")

            for baris in file_stream:
                if not st.session_state.server_berjalan:
                    break

                baris = baris.strip()
                if not baris:
                    continue

                try:
                    fitur_jaringan = json.loads(baris)

                    # 1. EKSTRAKSI GROUND TRUTH (Pisahkan kunci jawaban)
                    y_true = fitur_jaringan.pop("Label", None)

                    # 2. FASE TESTING (Prediksi Mandiri ke data unseen)
                    y_pred = st.session_state.model.predict_one(fitur_jaringan)

                    # 3. FASE EVALUASI (Bandingkan tebakan dengan kunci jawaban)
                    if y_pred is not None and y_true is not None:
                        st.session_state.metric_acc.update(y_true, y_pred)
                        st.session_state.metric_f1.update(y_true, y_pred)

                    # 4. FASE TRAINING KILAT (Update pemahaman model di tempat)
                    if y_true is not None:
                        st.session_state.model.learn_one(fitur_jaringan, y_true)

                    # --- PENCATATAN STATISTIK ---
                    st.session_state.total_paket += 1

                    if y_pred == 1:
                        st.session_state.trafik_anomali += 1
                        st.session_state.log_anomali.insert(
                            0,
                            {
                                "Waktu": time.strftime("%H:%M:%S"),
                                "Prediksi": "Serangan",
                                "Asli (Ground Truth)": (
                                    "Serangan"
                                    if y_true == 1
                                    else "Normal (False Positive)"
                                ),
                                "L4_SRC_PORT": fitur_jaringan.get("L4_SRC_PORT", "N/A"),
                                "IN_BYTES": fitur_jaringan.get("IN_BYTES", 0),
                            },
                        )
                        st.session_state.log_anomali = st.session_state.log_anomali[
                            :5
                        ]  # Batasi 5 log
                    else:
                        st.session_state.trafik_normal += 1

                    # Simpan history akurasi setiap 50 paket untuk digambar di grafik
                    if st.session_state.total_paket % 50 == 0:
                        st.session_state.history_acc.append(
                            st.session_state.metric_acc.get() * 100
                        )
                        # Render ulang layar setiap 50 paket agar browser tidak lag
                        update_ui()

                except json.JSONDecodeError:
                    pass


if st.session_state.server_berjalan:
    mulai_server()
else:
    update_ui()
