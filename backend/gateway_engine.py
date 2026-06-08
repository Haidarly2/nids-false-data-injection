import socket
import json
import time
import psutil
import os
from datetime import datetime
from river import compose, preprocessing, tree, ensemble, metrics

print("=" * 60)
print("🚀 MENGINISIALISASI GATEWAY NIDS (COLD START) 🚀")
print("=" * 60)

# 1. MEMBANGUN ARSITEKTUR AI (Dari Kode .ipynb Anda)
# Kita bangun dari keadaan KOSONG (Cold Start) untuk membuktikan kemampuan adaptasi real-time.
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

    print(f"\n[INFO] Gateway NIDS Berjalan di Background.")
    print(f"[INFO] Menunggu serangan dari VM di Port {PORT}...\n")

    conn, addr = s.accept()
    with conn:
        print(f"🔥 [ALERT] Koneksi masuk dari Mesin Penyerang: {addr} 🔥")
        print("Memulai pemrosesan Prequential Evaluation...\n")

        # Membaca aliran data bagaikan air yang mengalir dari selang
        file_stream = conn.makefile("r", encoding="utf-8")

        for baris in file_stream:
            baris = baris.strip()
            if not baris:
                continue

            try:
                # Waktu mulai proses 1 paket (Untuk hitung latensi)
                waktu_mulai_paket = time.time()

                # Terjemahkan string mentah menjadi objek JSON (Dictionary Python)
                fitur_jaringan = json.loads(baris)

                # 4. FASE PEMROSESAN INTI (Tanpa Data Frame Pandas)
                # a. Cabut Label (Ground Truth) agar model tidak menyontek
                y_true = fitur_jaringan.pop("Label", None)

                # b. Testing (Tebak buta berdasarkan fitur teknis)
                y_pred = model.predict_one(fitur_jaringan)

                # c. Evaluasi (Cocokkan tebakan dengan kunci jawaban)
                if y_pred is not None and y_true is not None:
                    metric_acc.update(y_true, y_pred)
                    metric_prec.update(y_true, y_pred)
                    metric_rec.update(y_true, y_pred)
                    metric_f1.update(y_true, y_pred)
                    metric_kappa.update(y_true, y_pred)

                # d. Training (Belajar seketika dari paket tersebut)
                if y_true is not None:
                    model.learn_one(fitur_jaringan, y_true)

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
