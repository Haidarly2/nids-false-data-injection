import socket
import time
import json
import random

# Mengarah ke IP WSL Anda (Tempat dummy_target.py berada)
# Ganti dengan IP WSL Anda (misal: 172.24.x.x)
TARGET_IP = "172.17.0.1" 
TARGET_PORT = 8088

print("[+] Sensor Medis Normal (Docker) Beroperasi...")

while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((TARGET_IP, TARGET_PORT))
            
            # Simulasi suhu tubuh normal (36.0 - 37.5)
            suhu_normal = round(random.uniform(36.0, 37.5), 1)
            payload = json.dumps({"id_sensor": "SENS-SUHU-01", "suhu": suhu_normal, "keterangan": "NORMAL"}) + "\r\n"
            
            s.sendall(payload.encode('utf-8'))
            print(f"[v] Terkirim: {payload.strip()}")
            
        except ConnectionRefusedError:
            print("[!] Gagal terhubung ke Gateway. Mencoba lagi...")
        except Exception as e:
            print(f"[!] Error: {e}")
            
    # Perangkat IoT normal memiliki jeda konstan yang teratur
    time.sleep(3)