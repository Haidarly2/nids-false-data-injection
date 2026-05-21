import streamlit as st
import socket
import json
import pickle
import threading
import time
import pandas as pd
import warnings
from streamlit.runtime.scriptrunner import add_script_run_ctx

warnings.filterwarnings("ignore")

# =======================================================
# 1. KONFIGURASI HALAMAN & MODEL
# =======================================================
st.set_page_config(page_title="NIDS Edge Gateway", page_icon="🛡️", layout="wide")
st.title("🛡️ NIDS Edge Gateway - Live Monitoring")


# Fungsi untuk memuat model (di-cache agar tidak di-load berulang kali)
@st.cache_resource
def load_model():
    with open("../model_nids_terlatih_ver3.pkl", "rb") as f:
        return pickle.load(f)


model = load_model()

# =======================================================
# 2. INISIALISASI VARIABEL GLOBAL (STATE)
# =======================================================
if "total_trafik" not in st.session_state:
    st.session_state.total_trafik = 0
    st.session_state.trafik_normal = 0
    st.session_state.trafik_anomali = 0
    st.session_state.log_anomali = []
    st.session_state.server_berjalan = False


# =======================================================
# 3. THREADING: FUNGSI PENERIMA JARINGAN (SOCKET)
# =======================================================
def mulai_server_socket():
    HOST = "127.0.0.1"
    PORT = 9999

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()

        st.session_state.server_berjalan = True

        conn, addr = s.accept()
        with conn:
            # BUNGKUS KONEKSI SEBAGAI FILE (Anti Terpotong)
            file_stream = conn.makefile("r", encoding="utf-8")

            for baris in file_stream:
                if not st.session_state.server_berjalan:
                    break

                baris = baris.strip()
                if not baris:
                    continue

                try:
                    fitur_jaringan = json.loads(baris)

                    # Buang kolom 'Label' sebelum ditebak oleh model NIDS
                    # agar tidak membiaskan proses prediksi
                    fitur_jaringan.pop("Label", None)

                    # PREDIKSI REAL-TIME
                    prediksi = model.predict_one(fitur_jaringan)

                    # UPDATE METRIK
                    st.session_state.total_trafik += 1

                    if prediksi == 1:
                        st.session_state.trafik_anomali += 1
                        log_baru = {
                            "Waktu": time.strftime("%H:%M:%S"),
                            "Port Asal": fitur_jaringan.get("L4_SRC_PORT", "N/A"),
                            "Port Tujuan": fitur_jaringan.get("L4_DST_PORT", "N/A"),
                            "Protokol": fitur_jaringan.get("PROTOCOL", "N/A"),
                            "Total Bytes": fitur_jaringan.get("IN_BYTES", 0)
                            + fitur_jaringan.get("OUT_BYTES", 0),
                        }
                        st.session_state.log_anomali.insert(0, log_baru)
                        st.session_state.log_anomali = st.session_state.log_anomali[:10]
                    else:
                        st.session_state.trafik_normal += 1

                except json.JSONDecodeError:
                    pass  # Aman, file_stream meminimalisir error ini hampir 0%


# =======================================================
# 4. TAMPILAN DASHBOARD (UI)
# =======================================================
# Tombol untuk menyalakan/mematikan penangkap data
if not st.session_state.server_berjalan:
    if st.button("▶️ Mulai Buka Gerbang NIDS (Port 9999)"):
        # Jalankan fungsi socket di background thread
        thread_socket = threading.Thread(target=mulai_server_socket, daemon=True)
        add_script_run_ctx(thread_socket)
        thread_socket.start()
        st.rerun()
else:
    st.success(
        "✅ NIDS Gateway aktif dan memantau lalu lintas jaringan pada 127.0.0.1:9999"
    )

# Layout Kartu Metrik
col1, col2, col3 = st.columns(3)
col1.metric("Total Trafik Masuk", f"{st.session_state.total_trafik} Paket")
col2.metric("✅ Trafik Normal", f"{st.session_state.trafik_normal} Paket")
col3.metric("🚨 Anomali (Serangan FDI)", f"{st.session_state.trafik_anomali} Paket")

# Tabel Log Serangan Terakhir
st.markdown("### ⚠️ Log Serangan FDI Terakhir")
if st.session_state.log_anomali:
    df_log = pd.DataFrame(st.session_state.log_anomali)
    st.dataframe(df_log, use_container_width=True)
else:
    st.info("Sistem aman. Belum ada serangan yang terdeteksi.")

# Mekanisme Auto-Refresh (Dashboard akan memperbarui layar setiap 1 detik)
if st.session_state.server_berjalan:
    time.sleep(1)
    st.rerun()
