import socket
import json
import time
import psutil
import pickle
import os
import sys
import joblib
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
# 1. INISIALISASI ENGINE & ISOLASI ENVIRONMENT
# =======================================================
# Pilihan Argumen: 'incremental_demo', 'incremental_train', 'rf', 'dnn'
TIPE_MODEL = sys.argv[1] if len(sys.argv) > 1 else "incremental_demo"
print(f"{C_CYAN}===================================================={C_RESET}")
print(
    f"{C_CYAN}🛡️  Menghidupkan NIDS Gateway Engine [{TIPE_MODEL.upper()}] 🛡️{C_RESET}"
)
print(f"{C_CYAN}===================================================={C_RESET}")

# ISOLASI MEMORI (AGAR DEMO TIDAK RUSAK KARENA TRAINING)
if TIPE_MODEL == "incremental_demo":
    MODEL_INC_FILE = "model_nids_terbaru.pkl"  # KHUSUS DEMO SIDANG
else:
    MODEL_INC_FILE = "model_nids_eksperimen.pkl"  # KHUSUS MENCARI DATA BAB 6

MODEL_RF_FILE = "model_rf_batch.pkl"
MODEL_DNN_FILE = "model_dnn_batch.keras"
SCALER_FILE = "scaler_batch.pkl"
LOG_FILE = "log_hasil_nids.json"

model_inc, rf_model, dnn_model, batch_scaler = None, None, None, None

# MUAT MODEL SESUAI PILIHAN
if "incremental" in TIPE_MODEL:
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
elif TIPE_MODEL == "rf":
    rf_model = joblib.load(MODEL_RF_FILE)
    batch_scaler = joblib.load(SCALER_FILE)
    print("[*] Model Random Forest (Batch) berhasil dimuat.")
elif TIPE_MODEL == "dnn":
    from keras.models import load_model

    dnn_model = load_model(MODEL_DNN_FILE)
    batch_scaler = joblib.load(SCALER_FILE)
    print("[*] Model Deep Learning (Batch) berhasil dimuat.")

# Menyiapkan Metrik Streaming & Kumulatif Rata-rata
metric_acc = metrics.Accuracy()
metric_f1 = metrics.F1()
metric_prec = metrics.Precision()
metric_rec = metrics.Recall()
metric_kappa = metrics.CohenKappa()
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
            "recall": round(metric_rec.get() * 100, 2) if total_diproses > 1 else 0.0,
            "precision": round(metric_prec.get() * 100, 2) if total_diproses > 1 else 0.0,
            "kappa_statistic": (
                round(metric_kappa.get() * 100, 2) if total_diproses > 1 else 0.0
            ),
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
                        y_true = fitur_jaringan.pop("Label", None)
                        y_pred = None
                        total_diproses += 1

                        # --- FASE INFERENSI (TEBAKAN AI) ---
                        if "incremental" in TIPE_MODEL:
                            y_pred = model_inc.predict_one(fitur_jaringan)
                            # --- FASE ADAPTASI (BELAJAR) KHUSUS INCREMENTAL ---
                            if y_true is not None:
                                model_inc.learn_one(fitur_jaringan, y_true)

                        elif TIPE_MODEL in ["rf", "dnn"]:
                            nilai_fitur = np.array(
                                list(fitur_jaringan.values())
                            ).reshape(1, -1)
                            fitur_scaled = batch_scaler.transform(nilai_fitur)

                            if TIPE_MODEL == "rf":
                                y_pred = int(rf_model.predict(fitur_scaled)[0])
                            elif TIPE_MODEL == "dnn":
                                prob = dnn_model.predict(fitur_scaled, verbose=0)[0][0]
                                y_pred = 1 if prob > 0.5 else 0

                        # --- KALKULASI METRIK BERJALAN ---
                        if y_pred is not None and y_true is not None:
                            metric_acc.update(y_true, y_pred)
                            metric_f1.update(y_true, y_pred)
                            metric_prec.update(y_true, y_pred)
                            metric_rec.update(y_true, y_pred)
                            metric_kappa.update(y_true, y_pred)

                        # Tampilkan di Terminal
                        if y_pred == 1:
                            status = f"{C_RED}[TERDETEKSI SERANGAN (1)]{C_RESET}"
                        elif y_pred == 0:
                            status = f"{C_GREEN}[Lalu Lintas Normal (0)]{C_RESET}"
                        else:
                            status = f"{C_YELLOW}[Memproses Pola... (-1)]{C_RESET}"

                        print(
                            f"Paket {total_diproses} | Model: {TIPE_MODEL} | Prediksi: {status}"
                        )

                        # Simpan log
                        simpan_log(fitur_jaringan, y_true, y_pred, waktu_mulai)

                    except json.JSONDecodeError:
                        continue

                # Simpan ingatan model SETELAH aliran selesai (Khusus Incremental)
                if "incremental" in TIPE_MODEL and model_inc is not None:
                    with open(MODEL_INC_FILE, "wb") as f:
                        pickle.dump(model_inc, f)
                    print(
                        f"\n{C_YELLOW}[*] Ingatan AI berhasil disimpan ke {MODEL_INC_FILE}{C_RESET}\n"
                    )

        except Exception as e:
            print(f"{C_RED}[!] Gateway terputus atau Error: {e}{C_RESET}")
            time.sleep(1)
            continue
