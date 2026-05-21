import pandas as pd
import numpy as np
import socket
import time
import json

# =======================================================
# 1. KONFIGURASI JARINGAN LOKAL (LOCALHOST)
# =======================================================
HOST = "127.0.0.1"
PORT = 9999

# Daftar kolom yang berupa kategori/identitas (tidak bisa dihitung mean/std-nya)
KOLOM_KATEGORIKAL = [
    "L4_SRC_PORT",
    "L4_DST_PORT",
    "PROTOCOL",
    "L7_PROTO",
    "TCP_FLAGS",
    "CLIENT_TCP_FLAGS",
    "SERVER_TCP_FLAGS",
    "ICMP_TYPE",
    "ICMP_IPV4_TYPE",
    "DNS_QUERY_ID",
    "DNS_QUERY_TYPE",
    "DNS_TTL_ANSWER",
    "FTP_COMMAND_RET_CODE",
]


# =======================================================
# 2. MESIN EKSTRAKSI STATISTIK (MENGHASILKAN BLUEPRINT)
# =======================================================
def buat_blueprint_statistik(df):
    print("📊 Mengekstrak parameter statistik (Mean & Std Dev) dari dataset...")
    blueprint = {0: {}, 1: {}}

    for label in [0, 1]:
        df_label = df[df["Label"] == label]
        blueprint[label]["kategorikal"] = {}
        blueprint[label]["numerik"] = {}

        for col in df.columns:
            if col == "Label":
                continue

            if col in KOLOM_KATEGORIKAL:
                # Simpan daftar nilai unik untuk diacak (sampling) nanti
                blueprint[label]["kategorikal"][col] = (
                    df_label[col].dropna().unique().tolist()
                )
            else:
                # Hitung Rata-rata dan Standar Deviasi untuk kolom fitur numerik
                blueprint[label]["numerik"][col] = {
                    "mean": df_label[col].mean(),
                    "std": df_label[col].std(),
                    "is_int": pd.api.types.is_integer_dtype(df_label[col]),
                }
    return blueprint


# =======================================================
# 3. FUNGSI PENCIPTAAN DATA SINTETIS (UNSEEN DATA)
# =======================================================
def generate_synthetic_data(blueprint, label):
    data_baru = {}

    # a. Hasilkan nilai kategorikal secara acak dari blueprint
    for col, nilai_unik in blueprint[label]["kategorikal"].items():
        data_baru[col] = np.random.choice(nilai_unik) if len(nilai_unik) > 0 else 0

    # b. Hasilkan nilai numerik menggunakan Distribusi Normal (Gaussian)
    for col, stats in blueprint[label]["numerik"].items():
        mean = stats["mean"]
        std = stats["std"]
        is_int = stats["is_int"]

        # KUNCI PROPOSAL: Penciptaan instans data baru secara dinamis
        nilai_sintetis = np.random.normal(loc=mean, scale=std)

        # Logika dasar jaringan: Total Bytes atau Latensi tidak mungkin bernilai minus
        nilai_sintetis = max(0, nilai_sintetis)

        # Kembalikan ke tipe data aslinya (Int atau Float)
        if is_int:
            data_baru[col] = int(round(nilai_sintetis))
        else:
            data_baru[col] = float(nilai_sintetis)

    # Sisipkan Label asli (Ground Truth) sebagai kunci jawaban untuk Gateway nanti
    data_baru["Label"] = label
    return data_baru


# =======================================================
# 4. ALUR UTAMA PROGRAM
# =======================================================
def mulai_generator():
    print("⏳ Membaca dataset asli untuk membuat blueprint...")
    # Baca dataset utuh SATU KALI saja
    df_full = pd.read_csv("../datasets/dataset_final_2juta.csv")

    blueprint = buat_blueprint_statistik(df_full)
    print("✅ Blueprint statistik berhasil diamankan di RAM!")

    # Kita tidak perlu menyimpan dataframe yang berat lagi
    del df_full

    jumlah_serangan = 50
    jumlah_normal = 4950
    total_paket = jumlah_serangan + jumlah_normal

    print(f"🧬 Memproduksi {total_paket} data sintetis unik secara real-time...")

    # Buat kerangka urutan tembakan (misal: 0, 0, 1, 0, 1, 0...) dan acak urutannya
    urutan_label = [0] * jumlah_normal + [1] * jumlah_serangan
    np.random.shuffle(urutan_label)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"🔄 Mencari Edge Gateway NIDS di {HOST}:{PORT}...")
        while True:
            try:
                s.connect((HOST, PORT))
                print(
                    "✅ Berhasil terhubung ke Gateway! Memulai transmisi dinamis...\n"
                )
                break
            except ConnectionRefusedError:
                print("   Gateway belum siap. Mencoba lagi dalam 2 detik...")
                time.sleep(2)

        # Proses Transmisi (Fase 2 Proposal)
        for i, label in enumerate(urutan_label):
            # Ciptakan data BARU tepat sepersekian milidetik sebelum dikirim
            data_sintetis = generate_synthetic_data(blueprint, label)

            pesan = json.dumps(data_sintetis) + "\n"

            try:
                s.sendall(pesan.encode("utf-8"))
            except Exception as e:
                print(f"\n❌ Koneksi terputus: {e}")
                break

            time.sleep(0.001)

            if (i + 1) % 1000 == 0:
                print(f"🚀 [{i + 1}] data sintetis berhasil ditembakkan...")

        print("\n🏁 Transmisi simulasi Prequential selesai.")


if __name__ == "__main__":
    mulai_generator()
