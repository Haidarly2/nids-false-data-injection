import pandas as pd
import numpy as np
import socket
import time
import json

# =======================================================
# 1. KONFIGURASI JARINGAN LOKAL (LOCALHOST)
# =======================================================
HOST = "127.0.0.1"  # IP internal laptop
PORT = 9999  # Port Gateway

# =======================================================
# 2. PENGATURAN TEKNIK JITTERING
# =======================================================
# Daftar kolom kategorikal/identitas yang HARAM diubah nilainya
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
    "Label",
]


def terapkan_jitter(row):
    """Menambahkan noise -2% hingga +2% pada kolom numerik"""
    row_dict = row.to_dict()
    for col, val in row_dict.items():
        # Lewati kolom kategorikal atau jika nilainya kosong (NaN)
        if col in KOLOM_KATEGORIKAL or pd.isna(val):
            continue

        # Terapkan Jitter hanya jika nilainya angka (numerik)
        if isinstance(val, (int, float, np.integer, np.floating)):
            # Hasilkan noise acak antara -2% (-0.02) hingga +2% (0.02)
            noise = np.random.uniform(-0.02, 0.02)
            nilai_baru = val * (1 + noise)

            # Jika tipe data asli adalah bilangan bulat (seperti IN_BYTES),
            # bulatkan kembali agar tidak ada data pecahan yang tidak logis
            if isinstance(val, (int, np.integer)):
                row_dict[col] = int(round(nilai_baru))
            else:
                row_dict[col] = nilai_baru

    return row_dict


# =======================================================
# 3. MESIN GENERATOR UTAMA
# =======================================================
def mulai_generator():
    print("⏳ Membaca seluruh dataset final... (Ini butuh sekitar 10-20 detik)")
    # 1. Baca SEMUA data agar kita bisa mencari baris serangan yang tersembunyi
    df_full = pd.read_csv("../datasets/dataset_final_2juta.csv")

    print("🔍 Menyaring skenario serangan...")
    # 2. Ambil paket Serangan dan paket Normal sesuai porsi yang kita inginkan
    # Misalnya kita ingin menyimulasikan 50000 total tembakan
    jumlah_serangan = 50
    jumlah_normal = 4950

    df_serangan = df_full[df_full["Label"] == 1].head(jumlah_serangan)
    df_normal = df_full[df_full["Label"] == 0].head(jumlah_normal)

    # 3. Gabungkan dan Acak (Shuffle) agar serangannya muncul secara acak (tidak beruntun di akhir)
    df = pd.concat([df_normal, df_serangan]).sample(frac=1).reset_index(drop=True)

    print(
        f"✅ Skenario siap! Total {len(df)} paket akan ditembakkan (Termasuk {len(df_serangan)} serangan)."
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"🔄 Mencari Edge Gateway di {HOST}:{PORT}...")

        # Terus mencoba menghubungi Gateway (Receiver/Dashboard)
        while True:
            try:
                s.connect((HOST, PORT))
                print("✅ Berhasil terhubung ke Edge Gateway! Memulai transmisi...\n")
                break
            except ConnectionRefusedError:
                print("   Gateway belum siap. Mencoba lagi dalam 2 detik...")
                time.sleep(2)

        # Proses Transmisi Data
        for index, row in df.iterrows():
            # 1. Terapkan Jitter
            # if row["Label"] == 1:
            #     data_baru = row.to_dict()
            # else:
            #     data_baru = terapkan_jitter(row)
            # ---------------------------------
            data_baru = row.to_dict()

            pesan = json.dumps(data_baru) + "\n"

            try:
                s.sendall(pesan.encode("utf-8"))
            except Exception as e:
                print(f"\n❌ Koneksi terputus: {e}")
                break

            time.sleep(0.001)

            if (index + 1) % 5000 == 0:  # Notif setiap 5000 agar terminal tidak bising
                print(f"🚀 [{index + 1}] paket jaringan berhasil dikirim...")

        print("\n🏁 Transmisi simulasi selesai.")


if __name__ == "__main__":
    mulai_generator()
