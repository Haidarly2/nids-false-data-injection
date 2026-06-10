import socket
import json
import time
import psutil
import pickle
import os
from datetime import datetime
from river import compose, preprocessing, tree, ensemble, metrics

MODEL_FILE = "model_nids_terbaru.pkl"

if os.path.exists(MODEL_FILE):
    # Kasus Nyata: Gateway nyala ulang setelah mati lampu, load ingatan lama
    print(f"Memuat memori model AI dari {MODEL_FILE}...")
    with open(MODEL_FILE, "rb") as f:
        model = pickle.load(f)
else:
    # Kasus Nyata: Pemasangan pertama kali di Rumah Sakit (Cold Start)
    print("Membangun model AI dari nol (Cold Start)...")
    base_model = tree.HoeffdingTreeClassifier()
    model = compose.Pipeline(
        preprocessing.MinMaxScaler(),
        ensemble.ADWINBaggingClassifier(model=base_model, n_models=10, seed=42),
    )

# 2. MENYIAPKAN 5 METRIK EVALUASI
metric_acc = metrics.Accuracy()
metric_prec = metrics.Precision()
metric_rec = metrics.Recall()
metric_f1 = metrics.F1()
metric_kappa = metrics.CohenKappa()

total_diproses = 0
LOG_FILE = "log_hasil_nids.json"

# Pastikan file log bersih setiap kali server dinyalakan ulang
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

# 3. PERSIAPAN SERVER SOCKET (Menerima Tembakan dari Parrot OS)
# Menggunakan 0.0.0.0 agar mesin ini bisa menerima data dari jaringan apa pun (termasuk VirtualBox)
HOST = "0.0.0.0"
PORT = 9999

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Gateway Listener aktif di {HOST}:{PORT}")

    conn, addr = s.accept()
    with conn:
        print(f"Menerima aliran data dari {addr}")
        file_stream = conn.makefile("r", encoding="utf-8")

        for baris in file_stream:
            baris = baris.strip()
            if not baris:
                continue

            try:
                waktu_mulai_paket = time.time()
                total_diproses += 1

                # Terjemahkan string mentah menjadi objek JSON (Dictionary Python)
                fitur_jaringan = json.loads(baris)

                # 4. FASE PEMROSESAN INTI
                # a. Cabut Label (Ground Truth) agar model tidak menyontek
                y_true = fitur_jaringan.pop("Label", None)

                # b. Testing (Prediksi awal sebelum belajar)
                y_pred = model.predict_one(fitur_jaringan)

                # c. Evaluasi (LENGKAP 5 METRIK SESUAI BAB 3)
                if y_pred is not None and y_true is not None:
                    metric_acc.update(y_true, y_pred)
                    metric_prec.update(y_true, y_pred)
                    metric_rec.update(y_true, y_pred)
                    metric_f1.update(y_true, y_pred)
                    metric_kappa.update(y_true, y_pred)

                # d. Training (Belajar seketika dari paket tersebut)
                if y_true is not None:
                    model.learn_one(fitur_jaringan, y_true)

                # Simpan ingatan model ke harddisk setiap kelipatan 5.000 paket
                # if total_diproses % 5000 == 0:
                #     with open(MODEL_FILE, "wb") as f:
                #         pickle.dump(model, f)
                if total_diproses == 50000:
                    with open(MODEL_FILE, "wb") as f:
                        pickle.dump(model, f)
                    print(f"✅ Model AI berhasil disimpan secara permanen pada paket {total_diproses}!")

                # Waktu selesai proses (Kalkulasi Latensi dalam milidetik)
                latensi_ms = (time.time() - waktu_mulai_paket) * 1000
                total_diproses += 1

                # 5. PROFILING SUMBER DAYA (Memori RAM yang dipakai Python saat ini)
                ram_terpakai_mb = psutil.Process().memory_info().rss / (1024 * 1024)

                # 6. RAW DATA LOGGING (Memenuhi Syarat Dospem & Database)
                # Semua data disimpan ke JSON sebagai bukti audit
                with open(LOG_FILE, "a") as f:
                    log_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                            :-3
                        ],
                        "paket_ke": total_diproses,
                        "data_mentah": fitur_jaringan,  # Data tanpa label
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

                # --- Indikator Visual di Terminal (Opsional, agar terlihat sistem bekerja) ---
                if total_diproses % 500 == 0:
                    print(
                        f"[Paket {total_diproses:,}] Acc: {metric_acc.get()*100:.2f}% | Latensi: {latensi_ms:.2f} ms | RAM: {ram_terpakai_mb:.1f} MB"
                    )

            except json.JSONDecodeError:
                print("[ERROR] Paket data rusak / bukan JSON valid.")
                pass
            
        print(f"\nTransmisi selesai! Menerima total {total_diproses} paket.")
        try:
            with open(MODEL_FILE, "wb") as f:
                pickle.dump(model, f)
            print("✅ Model AI berhasil disimpan secara permanen di akhir sesi!")
        except Exception as e:
            print(f"❌ GAGAL MENYIMPAN MODEL: {e}")
