import socket
import time
import sys
import math
import csv
from datetime import datetime

# ============================================================
# KONFIGURASI
# Sesuaikan IP di bawah ini sebelum menjalankan
# ============================================================
PROXY_IP      = '192.168.110.180 '.strip()   # Ganti dengan IP laptop Proxy
PROXY_PORT    = 8080

WEBSERVER_IP  = '192.168.110.239'.strip()    # Ganti dengan IP laptop Web Server
WEBSERVER_UDP_PORT = 9000

TOTAL_PACKETS = 10                 # Jumlah paket UDP (minimal 10 sesuai ketentuan)
UDP_TIMEOUT   = 1.0               # Timeout per paket: 1 detik (sesuai ketentuan)

# ============================================================
# MODE TCP — HTTP via Proxy
# ============================================================
def mode_tcp(path="/index.html"):
    print(f"{'='*50}")
    print(f"  MODE TCP — HTTP Request via Proxy")
    print(f"  Target: {PROXY_IP}:{PROXY_PORT} | Path: {path}")
    print(f"{'='*50}")
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((PROXY_IP, PROXY_PORT))

        # Format HTTP GET request sesuai standar HTTP/1.1
        request = f"GET {path} HTTP/1.1\r\nHost: {PROXY_IP}\r\nConnection: close\r\n\r\n"
        client.sendall(request.encode('utf-8'))

        # Terima seluruh response
        response = b""
        while True:
            part = client.recv(4096)
            if not part:
                break
            response += part

        client.close()

        print("\n--- RESPONSE DARI PROXY ---")
        print(response.decode('utf-8', errors='replace'))

    except ConnectionRefusedError:
        print(f"[ERROR] Koneksi ditolak. Pastikan Proxy berjalan di {PROXY_IP}:{PROXY_PORT}")
    except socket.timeout:
        print(f"[ERROR] Koneksi timeout ke Proxy {PROXY_IP}:{PROXY_PORT}")
    except Exception as e:
        print(f"[ERROR] Mode TCP gagal: {e}")

# ============================================================
# MODE UDP — QoS Ping ke Web Server
# ============================================================
def mode_udp():
    print(f"{'='*50}")
    print(f"  MODE UDP — QoS Measurement")
    print(f"  Target: {WEBSERVER_IP}:{WEBSERVER_UDP_PORT}")
    print(f"  Paket: {TOTAL_PACKETS} | Timeout: {UDP_TIMEOUT}s/paket")
    print(f"{'='*50}")

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(UDP_TIMEOUT)

    rtts               = []
    lost_packets       = 0
    total_bytes_recv   = 0
    start_test_time    = time.time()

    for i in range(1, TOTAL_PACKETS + 1):
        # Format payload wajib: "Ping <seq> <timestamp>"
        t_send  = time.time()
        payload = f"Ping {i} {t_send}"
        payload_bytes = payload.encode('utf-8')

        try:
            client.sendto(payload_bytes, (WEBSERVER_IP, WEBSERVER_UDP_PORT))
            data, server_addr = client.recvfrom(1024)

            t_recv = time.time()
            rtt    = (t_recv - t_send) * 1000   # konversi ke milidetik
            rtts.append(rtt)
            total_bytes_recv += len(data)

            print(f"  Paket {i:02d}: seq={i} | rtt={rtt:.2f} ms | dari {server_addr[0]}")

        except socket.timeout:
            lost_packets += 1
            print(f"  Paket {i:02d}: Request timed out")

    test_duration = time.time() - start_test_time
    client.close()

    # -------------------------------------------------------
    # PERHITUNGAN STATISTIK QoS
    # -------------------------------------------------------
    print(f"\n{'='*50}")
    print("  HASIL ANALISIS QoS")
    print(f"{'='*50}")

    # Packet Loss (%)
    loss_percent = (lost_packets / TOTAL_PACKETS) * 100
    print(f"  Packet Loss  : {loss_percent:.1f}% ({lost_packets}/{TOTAL_PACKETS} paket hilang)")

    # Throughput (kbps) = (Total byte diterima × 8) / durasi (detik) / 1000
    throughput_kbps = (total_bytes_recv * 8) / test_duration / 1000 if test_duration > 0 else 0
    print(f"  Throughput   : {throughput_kbps:.2f} kbps")

    if rtts:
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = sum(rtts) / len(rtts)
        print(f"  RTT          : Min={min_rtt:.2f} ms | Avg={avg_rtt:.2f} ms | Max={max_rtt:.2f} ms")

        # Jitter: deviasi standar selisih RTT berturut-turut σ(RTTi - RTTi-1)
        # Sesuai rumus ketentuan PDF hal. 13
        if len(rtts) > 1:
            deltas      = [rtts[j] - rtts[j-1] for j in range(1, len(rtts))]
            mean_delta  = sum(deltas) / len(deltas)
            variance    = sum((d - mean_delta) ** 2 for d in deltas) / len(deltas)
            jitter      = math.sqrt(variance)
            print(f"  Jitter       : {jitter:.2f} ms")
        else:
            jitter = 0.0
            print(f"  Jitter       : 0.00 ms (data tidak cukup)")
    else:
        min_rtt = max_rtt = avg_rtt = jitter = 0.0
        print("  RTT & Jitter : Tidak dapat dihitung (100% packet loss)")

    print(f"{'='*50}")

    # -------------------------------------------------------
    # SIMPAN HASIL KE CSV
    # -------------------------------------------------------
    filename = f"qos_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        # Data per paket
        writer.writerow(['seq', 'rtt_ms', 'status'])
        rtt_idx = 0
        for i in range(1, TOTAL_PACKETS + 1):
            # Tentukan apakah paket ini received atau lost
            # (urutan: paket yang received duluan mengisi rtts secara berurutan)
            if rtt_idx < len(rtts) and (i - 1 - lost_packets + rtt_idx) < len(rtts):
                pass
        # Tulis ulang dengan pendekatan sederhana: received dulu, lost setelahnya
        for idx, rtt in enumerate(rtts, 1):
            writer.writerow([idx, f"{rtt:.2f}", 'received'])
        for idx in range(len(rtts) + 1, TOTAL_PACKETS + 1):
            writer.writerow([idx, '', 'lost'])
        # Ringkasan statistik
        writer.writerow([])
        writer.writerow(['=== STATISTIK QoS ==='])
        writer.writerow(['packet_loss_%', 'throughput_kbps', 'min_rtt_ms', 'avg_rtt_ms', 'max_rtt_ms', 'jitter_ms'])
        writer.writerow([
            f"{loss_percent:.1f}",
            f"{throughput_kbps:.2f}",
            f"{min_rtt:.2f}",
            f"{avg_rtt:.2f}",
            f"{max_rtt:.2f}",
            f"{jitter:.2f}"
        ])

    print(f"\n  Hasil disimpan ke: {filename}")

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    # Validasi argumen: python client.py -mode tcp/udp [path]
    if len(sys.argv) < 3 or sys.argv[1] != "-mode":
        print("Cara penggunaan:")
        print("  python client.py -mode tcp [path] → HTTP request via Proxy (contoh: /osi.html)")
        print("  python client.py -mode udp        → QoS UDP ping ke Web Server")
        sys.exit(1)

    mode = sys.argv[2].lower()
    if mode == "tcp":
        # Ambil path jika diinput oleh user, jika tidak gunakan default /index.html
        path = sys.argv[3] if len(sys.argv) >= 4 else "/index.html"
        mode_tcp(path)
    elif mode == "udp":
        mode_udp()
    else:
        print(f"[ERROR] Mode '{mode}' tidak dikenal. Pilih 'tcp' atau 'udp'.")
        sys.exit(1)
