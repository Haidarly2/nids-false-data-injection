# sensor_suhu.py
import socket
import time
import json
import random

# Mengirim ke localhost karena berjalan di mesin yang sama dengan gateway
TARGET_IP = '127.0.0.1'
TARGET_PORT = 8080

def kirim_data():
    print("[*] Sensor suhu aktif mengirim data...")
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((TARGET_IP, TARGET_PORT))
                payload = {
                    "id_sensor": "SENS-SUHU-01",
                    "suhu": random.randint(40, 45),
                    "status": "NORMAL"
                }
                s.sendall(json.dumps(payload).encode('utf-8'))
            time.sleep(2)
        except ConnectionRefusedError:
            time.sleep(2)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    kirim_data()