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

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =======================================================
# 1. BACA PERINTAH DARI API SERVER (TENTUKAN MODEL AKTIF)
# =======================================================
# Pilihan: 'incremental', 'rf', 'dnn'
TIPE_MODEL = sys.argv[1] if len(sys.argv) > 1 else "incremental"
print(f"🔄 Menghidupkan NIDS Engine dengan otak: [{TIPE_MODEL.upper()}]")

MODEL_INC_FILE = "model_nids_terbaru.pkl"
MODEL_RF_FILE = "model_rf_batch.pkl"
MODEL_DNN_FILE = "model_dnn_batch.keras"
SCALER_FILE = "scaler_batch.pkl"

model_inc, rf_model, dnn_model, batch_scaler = None, None, None, None

# HANYA LOAD MODEL YANG DIPILIH (ISOLASI RAM MURNI)
if TIPE_MODEL == "incremental":
    if os.path.exists(MODEL_INC_FILE):
        with open(MODEL_INC_FILE, "rb") as f:
            model_inc = pickle.load(f)
    else:
        base_model = tree.HoeffdingTreeClassifier()
        model_inc = compose.Pipeline(
            preprocessing.MinMaxScaler(),
            ensemble.ADWINBaggingClassifier(model=base_model, n_models=10, seed=42),
        )
elif TIPE_MODEL == "rf":
    rf_model = joblib.load(MODEL_RF_FILE)
    batch_scaler = joblib.load(SCALER_FILE)
elif TIPE_MODEL == "dnn":
    from keras.models import load_model

    dnn_model = load_model(MODEL_DNN_FILE)
    batch_scaler = joblib.load(SCALER_FILE)

# Menyiapkan Metrik (Tetap dihitung manual untuk akurasi streaming)
metric_acc = metrics.Accuracy()
metric_f1 = metrics.F1()
total_diproses = 0

LOG_FILE = "log_hasil_nids.json"

HOST = "0.0.0.0"
PORT = 9999

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"🚀 Gateway [{TIPE_MODEL.upper()}] siap menerima serangan di {HOST}:{PORT}")

    while True:
        try:
            conn, addr = s.accept()
            with conn:
                file_stream = conn.makefile("r", encoding="utf-8")
                for baris in file_stream:
                    baris = baris.strip()
                    if not baris:
                        continue
                    try:
                        waktu_mulai_paket = time.time()
                        total_diproses += 1
                        fitur_jaringan = json.loads(baris)
                        y_true = fitur_jaringan.pop("Label", None)
                        y_pred = None

                        # ===================================================
                        # EKSEKUSI PREDIKSI SESUAI MODEL AKTIF
                        # ===================================================
                        if TIPE_MODEL == "incremental":
                            y_pred = model_inc.predict_one(fitur_jaringan)
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

                        # Kalkulasi Akurasi Live
                        if y_pred is not None and y_true is not None:
                            metric_acc.update(y_true, y_pred)
                            metric_f1.update(y_true, y_pred)

                        # Simpan berkala khusus Incremental
                        if TIPE_MODEL == "incremental" and total_diproses % 50000 == 0:
                            with open(MODEL_INC_FILE, "wb") as f:
                                pickle.dump(model_inc, f)

                        # Kalkulasi Metrik Profiling (INI SEKARANG 100% MURNI!)
                        latensi_ms = (time.time() - waktu_mulai_paket) * 1000
                        ram_terpakai_mb = psutil.Process().memory_info().rss / (
                            1024 * 1024
                        )

                        with open(LOG_FILE, "a") as f:
                            log_entry = {
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S.%f"
                                )[:-3],
                                "paket_ke": total_diproses,
                                "model_aktif": TIPE_MODEL,  # <--- Tandai model apa yang sedang nebak
                                "data_mentah": fitur_jaringan,
                                "ground_truth": y_true,
                                "prediksi_ai": y_pred if y_pred is not None else -1,
                                "metrik": {
                                    "akurasi": (
                                        round(metric_acc.get() * 100, 2)
                                        if total_diproses > 1
                                        else 0
                                    ),
                                    "f1_score": (
                                        round(metric_f1.get() * 100, 2)
                                        if total_diproses > 1
                                        else 0
                                    ),
                                },
                                "resource": {
                                    "latensi_ms": round(latensi_ms, 4),
                                    "ram_mb": round(ram_terpakai_mb, 2),
                                },
                            }
                            f.write(json.dumps(log_entry) + "\n")

                    except json.JSONDecodeError:
                        pass

                # Sesi Putus, simpan state
                if TIPE_MODEL == "incremental":
                    with open(MODEL_INC_FILE, "wb") as f:
                        pickle.dump(model_inc, f)
        except Exception as e:
            time.sleep(0.5)
            continue
