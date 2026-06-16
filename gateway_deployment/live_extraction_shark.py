import pyshark
import json
import socket
import statistics
import time
from collections import defaultdict

# Konfigurasi Target
GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 9999
TARGET_PORT = 8088
# TARGET_IP = '192.168.20.100'  # IP WSL/Windows tempat Gateway berada


# Struktur awal untuk 49 Fitur NIDS
def create_new_flow():
    return {
        "L4_SRC_PORT": 0,
        "L4_DST_PORT": 0,
        "PROTOCOL": 0,
        "L7_PROTO": 0,
        "IN_BYTES": 0,
        "IN_PKTS": 0,
        "OUT_BYTES": 0,
        "OUT_PKTS": 0,
        "TCP_FLAGS": 0,
        "CLIENT_TCP_FLAGS": 0,
        "SERVER_TCP_FLAGS": 0,
        "FLOW_DURATION_MILLISECONDS": 0,
        "DURATION_IN": 0,
        "DURATION_OUT": 0,
        "MIN_TTL": 999,
        "MAX_TTL": 0,
        "LONGEST_FLOW_PKT": 0,
        "SHORTEST_FLOW_PKT": 9999,
        "MIN_IP_PKT_LEN": 9999,
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
        "ICMP_TYPE": 0,
        "ICMP_IPV4_TYPE": 0,
        "DNS_QUERY_ID": 0,
        "DNS_QUERY_TYPE": 0,
        "DNS_TTL_ANSWER": 0,
        "FTP_COMMAND_RET_CODE": 0,
        "SRC_TO_DST_IAT_MIN": 0,
        "SRC_TO_DST_IAT_MAX": 0,
        "SRC_TO_DST_IAT_AVG": 0,
        "SRC_TO_DST_IAT_STDDEV": 0,
        "DST_TO_SRC_IAT_MIN": 0,
        "DST_TO_SRC_IAT_MAX": 0,
        "DST_TO_SRC_IAT_AVG": 0,
        "DST_TO_SRC_IAT_STDDEV": 0,
        # Variabel Internal (Tidak akan dikirim)
        "_start_time": 0,
        "_start_time_in": 0,
        "_start_time_out": 0,
        "_last_time_in": 0,
        "_last_time_out": 0,
        "_iat_in_list": [],
        "_iat_out_list": [],
    }


active_flows = defaultdict(create_new_flow)


def get_flow_key(packet):
    try:
        src_ip = packet.ip.src
        dst_ip = packet.ip.dst
        if hasattr(packet, "tcp"):
            src_port = packet.tcp.srcport
            dst_port = packet.tcp.dstport
            proto = "TCP"
        else:
            return None

        if src_ip < dst_ip:
            return f"{src_ip}:{src_port}-{dst_ip}:{dst_port}-{proto}"
        else:
            return f"{dst_ip}:{dst_port}-{src_ip}:{src_port}-{proto}"
    except AttributeError:
        return None


def calc_stats(iat_list):
    if not iat_list:
        return 0, 0, 0, 0
    return (
        min(iat_list),
        max(iat_list),
        int(statistics.mean(iat_list)),
        int(statistics.stdev(iat_list)) if len(iat_list) > 1 else 0,
    )


def extract_features_live(interface_name):
    print(f"[*] PyShark NIDS Sensor Aktif. Memantau {interface_name}...")

    capture = pyshark.LiveCapture(
        interface=interface_name, bpf_filter=f"tcp port {TARGET_PORT}"
    )

    for packet in capture.sniff_continuously():
        flow_key = get_flow_key(packet)
        if not flow_key:
            continue

        flow = active_flows[flow_key]
        current_time = float(packet.sniff_timestamp)
        pkt_len = int(packet.length)

        try:
            # Penentuan arah lalu lintas (Inbound: Masuk ke Target IP, Outbound: Keluar dari Target IP)
            is_inbound = True if int(packet.tcp.dstport) == TARGET_PORT else False

            # --- 1. INISIALISASI FLOW ---
            if flow["IN_PKTS"] == 0 and flow["OUT_PKTS"] == 0:
                flow["_start_time"] = current_time
                flow["PROTOCOL"] = 6
                flow["L4_SRC_PORT"] = int(packet.tcp.srcport)
                flow["L4_DST_PORT"] = int(packet.tcp.dstport)

            # --- 2. UPDATE METRIK ---
            if hasattr(packet.ip, "ttl"):
                ttl = int(packet.ip.ttl)
                flow["MIN_TTL"] = min(flow["MIN_TTL"], ttl)
                flow["MAX_TTL"] = max(flow["MAX_TTL"], ttl)

            flow["LONGEST_FLOW_PKT"] = max(flow["LONGEST_FLOW_PKT"], pkt_len)
            flow["SHORTEST_FLOW_PKT"] = min(flow["SHORTEST_FLOW_PKT"], pkt_len)
            flow["MIN_IP_PKT_LEN"] = min(flow["MIN_IP_PKT_LEN"], pkt_len)
            flow["MAX_IP_PKT_LEN"] = max(flow["MAX_IP_PKT_LEN"], pkt_len)

            # Histogram Ukuran
            if pkt_len <= 128:
                flow["NUM_PKTS_UP_TO_128_BYTES"] += 1
            elif pkt_len <= 256:
                flow["NUM_PKTS_128_TO_256_BYTES"] += 1
            elif pkt_len <= 512:
                flow["NUM_PKTS_256_TO_512_BYTES"] += 1
            elif pkt_len <= 1024:
                flow["NUM_PKTS_512_TO_1024_BYTES"] += 1
            elif pkt_len <= 1514:
                flow["NUM_PKTS_1024_TO_1514_BYTES"] += 1

            if is_inbound:
                if flow["_start_time_in"] == 0:
                    flow["_start_time_in"] = current_time
                flow["IN_BYTES"] += pkt_len
                flow["IN_PKTS"] += 1
                if flow["_last_time_in"] > 0:
                    flow["_iat_in_list"].append(
                        (current_time - flow["_last_time_in"]) * 1000
                    )
                flow["_last_time_in"] = current_time
            else:
                if flow["_start_time_out"] == 0:
                    flow["_start_time_out"] = current_time
                flow["OUT_BYTES"] += pkt_len
                flow["OUT_PKTS"] += 1
                if flow["_last_time_out"] > 0:
                    flow["_iat_out_list"].append(
                        (current_time - flow["_last_time_out"]) * 1000
                    )
                flow["_last_time_out"] = current_time

            flags = int(packet.tcp.flags, 16)
            flow["TCP_FLAGS"] |= flags
            win_size = int(packet.tcp.window_size_value)
            # --- 3. EKSTRAKSI TCP & L7 ---
            if is_inbound:
                flow["CLIENT_TCP_FLAGS"] |= flags
                flow["TCP_WIN_MAX_IN"] = max(flow["TCP_WIN_MAX_IN"], win_size)
            else:
                flow["SERVER_TCP_FLAGS"] |= flags
                flow["TCP_WIN_MAX_OUT"] = max(flow["TCP_WIN_MAX_OUT"], win_size)

            # if hasattr(packet, "dns"):
            #     flow["DNS_QUERY_ID"] = (
            #         int(packet.dns.id, 16) if hasattr(packet.dns, "id") else 0
            #     )
            #     flow["DNS_QUERY_TYPE"] = (
            #         int(packet.dns.qry_type) if hasattr(packet.dns, "qry_type") else 0
            #     )
            # if hasattr(packet, "icmp"):
            #     flow["ICMP_TYPE"] = int(packet.icmp.type)

            # --- 4. TERMINASI FLOW (TCP FIN/RST atau Timeout UDP) ---
            # flow_closed = False
            # if hasattr(packet, "tcp") and (
            #     int(packet.tcp.flags, 16) & 0x05
            # ):  # FIN atau RST
            #     flow_closed = True
            # elif (
            #     flow["PROTOCOL"] == 17 and flow["IN_PKTS"] > 0 and flow["OUT_PKTS"] > 0
            # ):  # Simulasi tutup sesi UDP
            #     flow_closed = True

            if flags & 0x05:
                flow["FLOW_DURATION_MILLISECONDS"] = int(
                    (current_time - flow["_start_time"]) * 1000
                )
                flow["DURATION_IN"] = (
                    int((flow["_last_time_in"] - flow["_start_time_in"]) * 1000)
                    if flow["_start_time_in"]
                    else 0
                )
                flow["DURATION_OUT"] = (
                    int((flow["_last_time_out"] - flow["_start_time_out"]) * 1000)
                    if flow["_start_time_out"]
                    else 0
                )

                (
                    flow["SRC_TO_DST_IAT_MIN"],
                    flow["SRC_TO_DST_IAT_MAX"],
                    flow["SRC_TO_DST_IAT_AVG"],
                    flow["SRC_TO_DST_IAT_STDDEV"],
                ) = calc_stats(flow["_iat_in_list"])
                (
                    flow["DST_TO_SRC_IAT_MIN"],
                    flow["DST_TO_SRC_IAT_MAX"],
                    flow["DST_TO_SRC_IAT_AVG"],
                    flow["DST_TO_SRC_IAT_STDDEV"],
                ) = calc_stats(flow["_iat_out_list"])

                dur_in_sec = (
                    flow["DURATION_IN"] / 1000.0 if flow["DURATION_IN"] > 0 else 1.0
                )
                dur_out_sec = (
                    flow["DURATION_OUT"] / 1000.0 if flow["DURATION_OUT"] > 0 else 1.0
                )
                flow["SRC_TO_DST_SECOND_BYTES"] = int(flow["IN_BYTES"] / dur_in_sec)
                flow["DST_TO_SRC_SECOND_BYTES"] = int(flow["OUT_BYTES"] / dur_out_sec)
                flow["SRC_TO_DST_AVG_THROUGHPUT"] = flow["SRC_TO_DST_SECOND_BYTES"] * 8
                flow["DST_TO_SRC_AVG_THROUGHPUT"] = flow["DST_TO_SRC_SECOND_BYTES"] * 8

                final_payload = {k: v for k, v in flow.items() if not k.startswith("_")}

                print(
                    f"[+] Sesi Selesai! Mengirim {len(final_payload)} Fitur ke NIDS Backend..."
                )
                send_to_gateway(final_payload)
                del active_flows[flow_key]

        except Exception as e:
            pass


def send_to_gateway(payload):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((GATEWAY_HOST, GATEWAY_PORT))
            s.sendall(json.dumps(payload).encode("utf-8"))
            print("[=>] Payload berhasil dikirim ke NIDS Gateway.")
    except ConnectionRefusedError:
        print("[!] Gagal mengirim: Gateway di port 9999 belum aktif.")


if __name__ == "__main__":
    # Pastikan ini eth0 sesuai dengan interface WSL Anda
    extract_features_live("any")
