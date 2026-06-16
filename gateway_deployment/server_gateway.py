import socket
import threading

HOST = "0.0.0.0"
PORT = 8088

def tangani_klien(conn, addr):
    with conn:
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break

                teks_data = data.decode("utf-8", errors="ignore").strip()

                # TAMPILKAN SEMUA DATA MENTAH YANG MASUK (TANPA FILTER)
                print(f"[!] RAW PAYLOAD DARI {addr[0]} -> {teks_data}")

                conn.sendall(b"ACK\r\n")
        except Exception:
            pass
# def tangani_klien(conn, addr):
#     with conn:
#         try:
#             while True:
#                 data = conn.recv(4096)
#                 if not data:
#                     break

#                 teks_data = data.decode("utf-8", errors="ignore").strip()

#                 # Indikator Visual yang bersih dan tidak bikin lag
#                 if "NORMAL" in teks_data:
#                     print(f"[+] Data Normal dari Sensor: {addr[0]}")
#                 elif "INJECTED_FDI" in teks_data:
#                     print(f"[!] SERANGAN FDI dari Attacker: {addr[0]}")
#                 else:
#                     # TAMPILKAN RAW DATA JIKA TIDAK COCOK KEDUANYA
#                     print(f"[?] PAYLOAD MISTERIUS DARI {addr[0]} -> {teks_data}")

#                 # Kirim balasan (ACK) untuk memancing metrik OUT_BYTES PyShark
#                 conn.sendall(b"ACK\r\n")
#         except Exception:
#             pass

def jalankan_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1000)

        print("=" * 50)
        print(f"🚀 [TARGET AKTIF] Server IoT berjalan di port {PORT}")
        print("🛡️  Siap menerima data sensor (Docker) dan serangan (Parrot)...")
        print("=" * 50)

        while True:
            conn, addr = s.accept()
            print(f"[>] KONEKSI BERHASIL DIBENTUK DARI: {addr[0]}")
            thread = threading.Thread(target=tangani_klien, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    jalankan_server()