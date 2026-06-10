# live_extractor.py
from nfstream import NFStreamer
import socket
import json

NIDS_IP = '127.0.0.1'
NIDS_PORT = 9999 # Ganti ke 8080 jika engine Anda menggunakan port tersebut

INTERFACE = "eth0" # Antarmuka WSL

print(f"[*] Menyiapkan Live Flow Extractor di interface {INTERFACE}...")
print("[*] NFStream aktif merekam 49 fitur NIDS...")

def kirim_ke_nids(payload):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((NIDS_IP, NIDS_PORT))
            s.sendall(json.dumps(payload).encode('utf-8'))
            print(f"[v] Flow NIDS terkirim! (Port: {payload['L4_DST_PORT']}, IN_BYTES: {payload['IN_BYTES']}, PKTS: {payload['IN_PKTS']})")
    except ConnectionRefusedError:
        pass

streamer = NFStreamer(source=INTERFACE, active_timeout=1, idle_timeout=1)

for flow in streamer:
    # Abaikan lalu lintas internal WSL (localhost/broadcast)
    if "127.0.0" in flow.src_ip or "255.255" in flow.dst_ip or ":" in flow.src_ip:
        continue

    # FORMAT TEGAS 49 FITUR (Sesuai Referensi Model)
    # Fitur dinamis akan diisi oleh NFStream, sisanya diset ke baseline aman (0).
    payload_nids = {
        "L4_SRC_PORT": flow.src_port,
        "L4_DST_PORT": flow.dst_port,
        "PROTOCOL": flow.protocol,
        "L7_PROTO": 0, 
        "TCP_FLAGS": 16, # Default standar
        "CLIENT_TCP_FLAGS": 0,
        "SERVER_TCP_FLAGS": 0,
        "ICMP_TYPE": 0,
        "ICMP_IPV4_TYPE": 0,
        "DNS_QUERY_ID": 0,
        "DNS_QUERY_TYPE": 0,
        "DNS_TTL_ANSWER": 0,
        "FTP_COMMAND_RET_CODE": 0,
        
        # --- Fitur Inti Deteksi FDI ---
        "IN_BYTES": flow.src2dst_bytes,
        "IN_PKTS": flow.src2dst_packets,
        "OUT_BYTES": flow.dst2src_bytes,
        "OUT_PKTS": flow.dst2src_packets,
        "FLOW_DURATION_MILLISECONDS": flow.bidirectional_duration_ms,
        # ------------------------------
        
        "DURATION_IN": 0,
        "DURATION_OUT": 0,
        "MIN_TTL": 0,
        "MAX_TTL": 0,
        "LONGEST_FLOW_PKT": 0,
        "SHORTEST_FLOW_PKT": 0,
        "MIN_IP_PKT_LEN": 0,
        "MAX_IP_PKT_LEN": 0,
        "SRC_TO_DST_SECOND_BYTES": 0,
        "DST_TO_SRC_SECOND_BYTES": 0,
        "RETRANSMITTED_IN_BYTES": 0,
        "RETRANSMITTED_IN_PKTS": 0,
        "RETRANSMITTED_OUT_BYTES": 0,
        "RETRANSMITTED_OUT_PKTS": 0,
        "SRC_TO_DST_AVG_THROUGHPUT": 0,
        "DST_TO_SRC_AVG_THROUGHPUT": 0,
        "NUM_PKTS_UP_TO_128_BYTES": 0,
        "NUM_PKTS_128_TO_256_BYTES": 0,
        "NUM_PKTS_256_TO_512_BYTES": 0,
        "NUM_PKTS_512_TO_1024_BYTES": 0,
        "NUM_PKTS_1024_TO_1514_BYTES": 0,
        "TCP_WIN_MAX_IN": 0,
        "TCP_WIN_MAX_OUT": 0,
        "SRC_TO_DST_IAT_MIN": 0,
        "SRC_TO_DST_IAT_MAX": 0,
        "SRC_TO_DST_IAT_AVG": 0,
        "SRC_TO_DST_IAT_STDDEV": 0,
        "DST_TO_SRC_IAT_MIN": 0,
        "DST_TO_SRC_IAT_MAX": 0,
        "DST_TO_SRC_IAT_AVG": 0,
        "DST_TO_SRC_IAT_STDDEV": 0
    }

    kirim_ke_nids(payload_nids)