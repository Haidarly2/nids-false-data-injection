# injector_nyata.py (Berjalan di WSL)
import socket
import json
import csv
import time
import random

# Port NIDS Engine Anda (Sesuaikan jika Anda mengubahnya di backend)
NIDS_IP = '127.0.0.1'
NIDS_PORT = 8080 # Ganti ke 8080 jika NIDS engine Anda mendengarkan di 8080
print("[!] Bersiap menyuntikkan data serangan PCAP asli ke NIDS Engine...")

def baca_dan_suntik():
    try:
        with open('serangan_nyata.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((NIDS_IP, NIDS_PORT))
                
                for row in csv_reader:
                    # Membungkus 4 fitur asli ke dalam template 49 fitur NIDS
                    # Kita menggunakan nilai baseline (normal) untuk fitur yang tidak terekstrak
                    # Namun kita menyuntikkan nilai ASLI Scapy untuk fitur krusial
                    payload_ai = {
                        "IPV4_SRC_ADDR": row['src_ip'],
                        "L4_SRC_PORT": int(row['src_port']),
                        "L4_DST_PORT": int(row['dst_port']),
                        "IN_BYTES": int(row['in_bytes']), # Ini yang akan membuat NIDS teriak!
                        "TCP_FLAGS": 16, # Representasi numerik flag ACK/PSH
                        "PROTOCOL": 6,
                        "L7_PROTO": 0,
                        "IN_PKTS": random.randint(5, 10),
                        "OUT_PKTS": random.randint(1, 5),
                        "OUT_BYTES": random.randint(100, 500),
                        "FLOW_DURATION_MILLISECONDS": random.randint(10, 50),
                        # (Untuk keperluan demo, kita asumsikan generator engine Anda akan melengkapi
                        # sisa fitur lainnya secara otomatis jika menggunakan format dictionary/JSON)
                    }
                    
                    pesan = json.dumps(payload_ai)
                    s.sendall(pesan.encode('utf-8'))
                    print(f"[v] Paket Injeksi (Bytes: {row['in_bytes']}, Port: {row['src_port']}) dikirim ke NIDS!")
                    time.sleep(1) # Jeda 1 detik antar tembakan
                    
    except ConnectionRefusedError:
        print("[X] NIDS Engine belum menyala. Jalankan gateway_engine.py di backend terlebih dahulu!")
    except FileNotFoundError:
        print("[X] File serangan_nyata.csv tidak ditemukan di folder ini!")

if __name__ == "__main__":
    baca_dan_suntik()