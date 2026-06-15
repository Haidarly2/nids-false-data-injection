from nfstream import NFStreamer
import socket
import json
import pprint

NIDS_IP = "127.0.0.1"
NIDS_PORT = 9999
INTERFACE = "any"


def kirim_ke_nids(payload):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((NIDS_IP, NIDS_PORT))
            s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
    except ConnectionRefusedError:
        pass


streamer = NFStreamer(
    source=INTERFACE, active_timeout=10, idle_timeout=5, bpf_filter="port 8000"
)

for flow in streamer:
    durasi_detik = (
        flow.bidirectional_duration_ms / 1000.0
        if flow.bidirectional_duration_ms > 0
        else 0.001
    )
    src_throughput = int(flow.src2dst_bytes / durasi_detik)
    dst_throughput = int(flow.dst2src_bytes / durasi_detik)

    in_pkts = flow.src2dst_packets if flow.src2dst_packets > 0 else 1
    out_pkts = flow.dst2src_packets if flow.dst2src_packets > 0 else 1
    avg_in_ps = flow.src2dst_bytes // in_pkts
    avg_out_ps = flow.dst2src_bytes // out_pkts

    # Deteksi murni berdasarkan ukuran payload Parrot OS Anda
    is_fdi_attack = flow.src2dst_bytes >= 1000 and flow.src2dst_packets >= 10

    # KITA SUAPI AI AGAR IA BELAJAR DNA WSL!
    MODE_KALIBRASI = False

    if MODE_KALIBRASI:
        ground_truth = 1 if is_fdi_attack else 0
        print(
            f"[*] KALIBRASI AI... Trafik: {'SERANGAN' if is_fdi_attack else 'NORMAL'} | Bytes: {flow.src2dst_bytes}"
        )
    else:
        ground_truth = None
        print(
            f"[!] MODE UJIAN AKTIF! AI Menebak Mandiri... | Bytes: {flow.src2dst_bytes}"
        )

    payload_nids = {
        "L4_SRC_PORT": flow.src_port,
        "L4_DST_PORT": flow.dst_port,
        "PROTOCOL": flow.protocol,
        "L7_PROTO": getattr(flow, "application_id", 0),
        "TCP_FLAGS": 16,
        "CLIENT_TCP_FLAGS": 0,
        "SERVER_TCP_FLAGS": 0,
        "ICMP_TYPE": 0,
        "ICMP_IPV4_TYPE": 0,
        "DNS_QUERY_ID": 0,
        "DNS_QUERY_TYPE": 0,
        "DNS_TTL_ANSWER": 0,
        "FTP_COMMAND_RET_CODE": 0,
        "IN_BYTES": flow.src2dst_bytes,
        "IN_PKTS": flow.src2dst_packets,
        "OUT_BYTES": flow.dst2src_bytes,
        "OUT_PKTS": flow.dst2src_packets,
        "FLOW_DURATION_MILLISECONDS": flow.bidirectional_duration_ms,
        "DURATION_IN": getattr(flow, "src2dst_duration_ms", 0),
        "DURATION_OUT": getattr(flow, "dst2src_duration_ms", 0),
        "MIN_TTL": getattr(flow, "src2dst_min_ttl", 0),
        "MAX_TTL": getattr(flow, "src2dst_max_ttl", 0),
        "LONGEST_FLOW_PKT": max(
            getattr(flow, "src2dst_max_ps", avg_in_ps),
            getattr(flow, "dst2src_max_ps", avg_out_ps),
        ),
        "SHORTEST_FLOW_PKT": min(
            getattr(flow, "src2dst_min_ps", avg_in_ps),
            getattr(flow, "dst2src_min_ps", avg_out_ps),
        ),
        "MIN_IP_PKT_LEN": getattr(flow, "src2dst_min_ps", avg_in_ps),
        "MAX_IP_PKT_LEN": getattr(flow, "src2dst_max_ps", avg_in_ps),
        "SRC_TO_DST_SECOND_BYTES": 0,
        "DST_TO_SRC_SECOND_BYTES": 0,
        "RETRANSMITTED_IN_BYTES": 0,
        "RETRANSMITTED_IN_PKTS": 0,
        "RETRANSMITTED_OUT_BYTES": 0,
        "RETRANSMITTED_OUT_PKTS": 0,
        "SRC_TO_DST_AVG_THROUGHPUT": src_throughput,
        "DST_TO_SRC_AVG_THROUGHPUT": dst_throughput,
        "NUM_PKTS_UP_TO_128_BYTES": 0,
        "NUM_PKTS_128_TO_256_BYTES": 0,
        "NUM_PKTS_256_TO_512_BYTES": 0,
        "NUM_PKTS_512_TO_1024_BYTES": 0,
        "NUM_PKTS_1024_TO_1514_BYTES": 0,
        "TCP_WIN_MAX_IN": 0,
        "TCP_WIN_MAX_OUT": 0,
        "SRC_TO_DST_IAT_MIN": getattr(flow, "src2dst_min_piat_ms", 0),
        "SRC_TO_DST_IAT_MAX": getattr(flow, "src2dst_max_piat_ms", 0),
        "SRC_TO_DST_IAT_AVG": getattr(flow, "src2dst_mean_piat_ms", 0),
        "SRC_TO_DST_IAT_STDDEV": getattr(flow, "src2dst_stddev_piat_ms", 0),
        "DST_TO_SRC_IAT_MIN": getattr(flow, "dst2src_min_piat_ms", 0),
        "DST_TO_SRC_IAT_MAX": getattr(flow, "dst2src_max_piat_ms", 0),
        "DST_TO_SRC_IAT_AVG": getattr(flow, "dst2src_mean_piat_ms", 0),
        "DST_TO_SRC_IAT_STDDEV": getattr(flow, "dst2src_stddev_piat_ms", 0),
        # INJEKSI LABEL UNTUK TRAINING
        "Label": ground_truth,
    }

    MODE_INSPEKSI_TERMINAL = True  # Ubah ke False jika terminal terlalu penuh
    MODE_SIMPAN_KE_FILE = True  # Ubah ke True untuk menyimpan ke file txt

    if MODE_INSPEKSI_TERMINAL:
        print(f"\n[+] Aliran Data Terdeteksi! (Protokol: {payload_nids['PROTOCOL']})")
        pprint.pprint(payload_nids)  # Mencetak isi payload secara vertikal dan rapi

    if MODE_SIMPAN_KE_FILE:
        with open("debug_raw_nfstream.json", "a") as f:
            f.write(json.dumps(payload_nids) + "\n")

    kirim_ke_nids(payload_nids)
