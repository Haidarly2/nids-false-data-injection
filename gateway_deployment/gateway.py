import socket
import json
import pickle
import warnings

# Mengabaikan warning versi library jika ada perbedaan minor
warnings.filterwarnings("ignore")

# =======================================================
# 1. KONFIGURASI JARINGAN LOKAL
# =======================================================
HOST = "127.0.0.1"
PORT = 9999


def mulai_gateway():
    print("🧠 Memuat otak NIDS (Memori Incremental Learning)...")

    # Memuat model dari folder luar (skripsi_fdi)
    try:
        with open("../model_nids_terlatih_ver2.pkl", "rb") as f:
            model = pickle.load(f)
        print("✅ Model NIDS berhasil diaktifkan dan siap bertugas!\n")
    except FileNotFoundError:
        print("❌ ERROR: File model.pkl tidak ditemukan. Pastikan namanya benar.")
        return

    # Membuka Socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"🛡️ NIDS Edge Gateway bersiaga penuh di {HOST}:{PORT}")
        print("⏳ Menunggu lalu lintas jaringan dari Sensor...\n")

        conn, addr = s.accept()
        with conn:
            print(f"📡 Terhubung dengan sumber data di {addr}")

            while True:
                data = conn.recv(4096)
                if not data:
                    break

                # Jaringan TCP sering menggabungkan beberapa paket jadi satu string
                # Kita pisahkan berdasarkan garis baru (\n) yang dikirim generator
                teks_data = data.decode("utf-8")
                daftar_pesan = teks_data.strip().split("\n")

                for pesan in daftar_pesan:
                    if not pesan:
                        continue

                    try:
                        # 1. Ekstrak data dari format JSON ke Dictionary
                        fitur_jaringan = json.loads(pesan)

                        # 2. PROSES DETEKSI REAL-TIME
                        # Model langsung memprediksi berdasarkan 50 fitur yang masuk
                        prediksi = model.predict_one(fitur_jaringan)

                        # 3. Tampilkan hasil (Asumsi Label 1 = Serangan, 0 = Normal)
                        # Anda bisa menyesuaikan angka 1/0 ini dengan format dataset Anda
                        if prediksi == 1:
                            port_asal = fitur_jaringan.get("L4_SRC_PORT", "N/A")
                            print(
                                f"🚨 [ANOMALI] Serangan FDI terdeteksi dari Port {port_asal}!"
                            )
                        else:
                            print(f"✅ [NORMAL] Trafik aman.")

                    except json.JSONDecodeError:
                        continue  # Abaikan paket yang terpotong di tengah jalan
                    except Exception as e:
                        print(f"⚠️ Kesalahan deteksi: {e}")


if __name__ == "__main__":
    mulai_gateway()
