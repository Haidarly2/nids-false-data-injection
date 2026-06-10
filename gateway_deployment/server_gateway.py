# server_gateway.py
import socket

# Bind ke 0.0.0.0 agar bisa menerima koneksi dari luar (termasuk VirtualBox)
HOST = '0.0.0.0'
PORT = 8080

def jalankan_gateway():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"[*] IoT Edge Gateway aktif mendengarkan di port {PORT}...")
        
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        teks = data.decode('utf-8', errors='ignore')
                        if "OVERHEAT" in teks or "PALSU" in teks:
                            print(f"[!] ANOMALI TERDETEKSI dari {addr[0]}: {teks}")
                        else:
                            print(f"[+] Data normal dari {addr[0]}: {teks}")
            except KeyboardInterrupt:
                print("\n[*] Gateway dimatikan.")
                break
            except Exception as e:
                pass

if __name__ == "__main__":
    jalankan_gateway()