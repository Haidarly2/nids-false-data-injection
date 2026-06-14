# server_gateway.py (Target Operasi / Pintu Utama IoT)
import socket
import threading

HOST = "0.0.0.0"
PORT = 8000


def tangani_klien(conn, addr):
    """Fungsi ini menangani setiap paket yang masuk secara independen"""
    with conn:
        try:
            # LOOP KRUSIAL: Mencegah Pintu Tertutup sepihak (Mencegah Broken Pipe)
            while True:
                data = conn.recv(4096)
                if not data:
                    break  # Klien (Sensor/Attacker) yang menutup koneksinya

                # Terjemahkan data mentah menjadi teks
                # teks_data = data.decode("utf-8", errors="ignore").strip()

                # Kita HANYA mencetak data sensor agar terminal tidak ngelag/penuh saat dibombardir attacker
                # if "SENS-SUHU" in teks_data:
                #     print(f"[v] Data masuk dari {addr}: {teks_data}")

                # Kirim balasan (ACK) agar metrik OUT_BYTES tercatat untuk NIDS
                conn.sendall(b"ACK\r\n")
        except Exception:
            pass


def jalankan_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Mengizinkan port langsung dipakai ulang jika server direstart
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))

        # Mengizinkan antrean hingga 1000 koneksi bersamaan (Siap untuk Flooding)
        s.listen(1000)

        print("=" * 50)
        print(f"🚀 [TARGET AKTIF] Server IoT berjalan di {HOST}:{PORT}")
        print("🛡️  Pintu Utama siap menerima data sensor atau serangan injeksi...")
        print("=" * 50)

        while True:
            conn, addr = s.accept()
            # Menggunakan Threading agar server tidak macet saat dibombardir serangan
            thread = threading.Thread(target=tangani_klien, args=(conn, addr))
            thread.start()


if __name__ == "__main__":
    jalankan_server()
