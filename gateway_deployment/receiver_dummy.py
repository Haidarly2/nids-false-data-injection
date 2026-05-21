import socket

# Konfigurasi harus sama persis dengan generator.py
HOST = "127.0.0.1"
PORT = 9999


def mulai_receiver():
    # Membuka gerbang jaringan (Socket TCP)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Mengikat program ke IP dan Port tersebut
        s.bind((HOST, PORT))
        # Mulai mendengarkan (listening)
        s.listen()
        print(f"🛡️ Gateway Dummy bersiap di {HOST}:{PORT}")
        print("⏳ Menunggu aliran data dari Data Generator...")

        # Menerima koneksi jika generator.py mengetuk pintu
        conn, addr = s.accept()
        with conn:
            print(f"✅ Terhubung dengan Sensor IoT/Attacker di {addr}\n")

            # Terus-menerus menangkap data
            while True:
                data = conn.recv(2048)  # Menangkap maksimal 2048 bytes per ketukan
                if not data:
                    break  # Berhenti jika tidak ada data lagi

                # Decode data dari byte ke teks dan bersihkan spasi/newline berlebih
                teks_data = data.decode("utf-8").strip()

                # Cetak ke layar (dibatasi 120 karakter agar terminal tidak terlalu penuh)
                print(f"📥 Ditangkap: {teks_data[:120]}... [dipotong]")


if __name__ == "__main__":
    mulai_receiver()
