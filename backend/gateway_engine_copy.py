import socket
import json
import time
import psutil
import pickle
import os
import sys
import numpy as np
from datetime import datetime
from river import compose, preprocessing, tree, ensemble, metrics

# Mematikan peringatan TensorFlow jika ada
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Konstanta Warna Terminal untuk Demo Sidang
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_RESET = "\033[0m"

# =======================================================
# 1. INISIALISASI ENGINE & MODEL
# =======================================================
TIPE_MODEL = sys.argv[1] if len(sys.argv) > 1 else "incremental"
print(f"{C_CYAN}===================================================={C_RESET}")
print(
    f"{C_CYAN}🛡️  Menghidupkan NIDS Gateway Engine [{TIPE_MODEL.upper()}] 🛡️{C_RESET}"
)
print(f"{C_CYAN}===================================================={C_RESET}")

MODEL_INC_FILE = "model_nids_terbaru.pkl"
LOG_FILE = "log_hasil_nids.json"

model_inc = None

if TIPE_MODEL == "incremental":
    if os.path.exists(MODEL_INC_FILE):
        print(f"[*] Memuat memori AI dari: {MODEL_INC_FILE}")
        with open(MODEL_INC_FILE, "rb") as f:
            model_inc = pickle.load(f)
    else:
        print(f"[*] File .pkl tidak ditemukan. Memulai KANVAS KOSONG (Zero-Shot)!")
        base_model = tree.HoeffdingTreeClassifier()
        model_inc = compose.Pipeline(
            preprocessing.MinMaxScaler(),
            ensemble.ADWINBaggingClassifier(model=base_model, n_models=10, seed=42),
        )

# Menyiapkan Metrik Streaming
metric_acc = metrics.Accuracy()
metric_f1 = metrics.F1()
total_diproses = 0


# =======================================================
# 2. FUNGSI LOGGING & METRIK
# =======================================================
def simpan_log(fitur, y_true, y_pred, waktu_mulai):
    latensi_ms = (time.time() - waktu_mulai) * 1000
    ram_mb = psutil.Process().memory_info().rss / (1024 * 1024)

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "paket_ke": total_diproses,
        "model_aktif": TIPE_MODEL,
        "data_mentah": fitur,
        "ground_truth": y_true,
        "prediksi_ai": int(y_pred) if y_pred is not None else -1,
        "metrik": {
            "akurasi": round(metric_acc.get() * 100, 2) if total_diproses > 1 else 0.0,
            "f1_score": round(metric_f1.get() * 100, 2) if total_diproses > 1 else 0.0,
        },
        "resource": {
            "latensi_ms": round(latensi_ms, 4),
            "ram_mb": round(ram_mb, 2),
        },
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


# =======================================================
# 3. MAIN LOOP SERVER SOCKET
# =======================================================
HOST, PORT = "0.0.0.0", 9999

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(
        f"{C_GREEN}🚀 Gateway siap mengintai aliran data di {HOST}:{PORT}...{C_RESET}\n"
    )

    while True:
        try:
            conn, addr = s.accept()
            with conn:
                file_stream = conn.makefile("r", encoding="utf-8")
                for baris in file_stream:
                    baris = baris.strip()
                    if not baris:
                        continue

                    waktu_mulai = time.time()

                    try:
                        fitur_jaringan = json.loads(baris)
                        y_true = fitur_jaringan.pop(
                            "Label", None
                        )  # Ambil dan Hapus Label
                        y_pred = None

                        total_diproses += 1

                        # --- FASE INFERENSI (TEBAKAN AI) ---
                        if TIPE_MODEL == "incremental":
                            y_pred = model_inc.predict_one(fitur_jaringan)

                            # Tampilkan di Terminal dengan Visual yang Rapi
                            if y_pred == 1:
                                status = f"{C_RED}[TERDETEKSI SERANGAN (1)]{C_RESET}"
                            elif y_pred == 0:
                                status = f"{C_GREEN}[Lalu Lintas Normal (0)]{C_RESET}"
                            else:
                                status = f"{C_YELLOW}[Memproses Pola... (-1)]{C_RESET}"

                            print(
                                f"Paket {total_diproses} | Pkts: {fitur_jaringan.get('IN_PKTS', 0):02d} | Bytes: {fitur_jaringan.get('IN_BYTES', 0):04d} --> Prediksi: {status}"
                            )

                            # --- FASE ADAPTASI (BELAJAR) ---
                            if y_true is not None:
                                model_inc.learn_one(fitur_jaringan, y_true)
                                # Update metrik hanya jika ada kunci jawaban
                                if y_pred is not None:
                                    metric_acc.update(y_true, y_pred)
                                    metric_f1.update(y_true, y_pred)

                        # Simpan ke file log JSON
                        simpan_log(fitur_jaringan, y_true, y_pred, waktu_mulai)

                    except json.JSONDecodeError:
                        print(
                            f"{C_RED}[!] Error: Format data JSON dari Extractor rusak.{C_RESET}"
                        )
                        continue

                # Simpan ingatan model setelah koneksi dari ekstraktor ditutup
                if TIPE_MODEL == "incremental" and model_inc is not None:
                    with open(MODEL_INC_FILE, "wb") as f:
                        pickle.dump(model_inc, f)
                    print(
                        f"\n{C_YELLOW}[*] Ingatan AI berhasil disimpan ke .pkl{C_RESET}\n"
                    )

        except Exception as e:
            print(f"{C_RED}[!] Gateway terputus atau Error: {e}{C_RESET}")
            time.sleep(1)
            continue
