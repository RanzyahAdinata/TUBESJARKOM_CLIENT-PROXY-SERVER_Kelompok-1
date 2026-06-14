import socket
import threading
import os
import time
from datetime import datetime

# ============================================================
# KONFIGURASI
# Sesuaikan IP di bawah ini dengan IP laptop Web Server
# ============================================================
WEBSERVER_IP   = '192.168.110.239'.strip()   # Ganti dengan IP laptop Web Server
WEBSERVER_PORT = 8000
PROXY_HOST     = '192.168.110.180'
PROXY_PORT     = 8080
WEBSERVER_TIMEOUT = 5              # detik, timeout koneksi ke web server
CACHE_DIR      = "cache_dir"

# Buat direktori cache jika belum ada
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

cache_lock = threading.Lock()

# ============================================================
# HANDLER PER CLIENT
# ============================================================
def handle_client(client_socket, client_addr):
    # Jeda 3 detik untuk simulasi multithreading agar thread aktif menumpuk di log
    time.sleep(3.0)

    client_ip  = client_addr[0]
    start_time = time.time()
    url_path   = "-"
    status     = "-"

    try:
        request_data = client_socket.recv(4096)
        if not request_data:
            return

        request_text = request_data.decode('utf-8', errors='replace')
        first_line   = request_text.split('\r\n')[0]

        # --- Validasi request HTTP (anti malformed request) ---
        parts = first_line.split(' ')
        if len(parts) < 2:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[Proxy] {timestamp} | IP: {client_ip} | Malformed request, ditolak (400)")
            client_socket.sendall(
                b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"
            )
            return

        url_path = parts[1]

        # Buat nama file cache yang aman dari karakter path
        safe_filename = url_path.replace("/", "_").replace("..", "")
        if safe_filename in ("", "_"):
            safe_filename = "_index.html"
        cache_filepath = os.path.join(CACHE_DIR, safe_filename)

        # -------------------------------------------------------
        # CACHE HIT
        # -------------------------------------------------------
        with cache_lock:
            cache_exists = os.path.exists(cache_filepath)

        if cache_exists:
            with cache_lock:
                with open(cache_filepath, 'rb') as f:
                    response_data = f.read()
            status = "HIT"
            client_socket.sendall(response_data)

        # -------------------------------------------------------
        # CACHE MISS — forward ke Web Server
        # -------------------------------------------------------
        else:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(WEBSERVER_TIMEOUT)

            try:
                server_socket.connect((WEBSERVER_IP, WEBSERVER_PORT))
                server_socket.sendall(request_data)

                # Terima seluruh response dari web server
                response_data = b""
                while True:
                    part = server_socket.recv(4096)
                    if not part:
                        break
                    response_data += part

            except (socket.timeout, TimeoutError):
                # --- 504 Gateway Timeout ---
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[Proxy] {timestamp} | IP: {client_ip} | URL: {url_path} | 504 Gateway Timeout")
                error_body = b"<html><body><h1>504 Gateway Timeout</h1></body></html>"
                header = (
                    f"HTTP/1.1 504 Gateway Timeout\r\n"
                    f"Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(error_body)}\r\n"
                    f"\r\n"
                ).encode('utf-8')
                client_socket.sendall(header + error_body)
                return

            except ConnectionRefusedError:
                # --- 504 Gateway Timeout (server tidak bisa dijangkau) ---
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[Proxy] {timestamp} | IP: {client_ip} | URL: {url_path} | 504 Gateway Timeout (Connection Refused)")
                error_body = b"<html><body><h1>504 Gateway Timeout</h1><p>Web server tidak dapat dijangkau.</p></body></html>"
                header = (
                    f"HTTP/1.1 504 Gateway Timeout\r\n"
                    f"Content-Type: text/html; charset=utf-8\r\n"
                    f"Content-Length: {len(error_body)}\r\n"
                    f"\r\n"
                ).encode('utf-8')
                client_socket.sendall(header + error_body)
                return

            finally:
                server_socket.close()

            # Simpan ke cache dengan lock (mencegah race condition)
            with cache_lock:
                with open(cache_filepath, 'wb') as f:
                    f.write(response_data)
            status = "MISS"
            client_socket.sendall(response_data)

        # --- Log Wajib: IP client, URL, status cache, waktu respons ---
        latency   = (time.time() - start_time) * 1000
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[Proxy] {timestamp} | IP: {client_ip} | URL: {url_path} | Cache: {status} | Latency: {latency:.2f} ms")

    except Exception as e:
        # --- 502 Bad Gateway (web server mengembalikan error / error tak terduga) ---
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[Proxy] {timestamp} | IP: {client_ip} | URL: {url_path} | 502 Bad Gateway | Exception: {e}")
        try:
            error_body = b"<html><body><h1>502 Bad Gateway</h1></body></html>"
            header = (
                f"HTTP/1.1 502 Bad Gateway\r\n"
                f"Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(error_body)}\r\n"
                f"\r\n"
            ).encode('utf-8')
            client_socket.sendall(header + error_body)
        except:
            pass
    finally:
        client_socket.close()

# ============================================================
# MAIN PROXY SERVER
# ============================================================
def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((PROXY_HOST, PROXY_PORT))
    server.listen(10)
    print("=" * 50)
    print(f"  Proxy Server listening on port {PROXY_PORT}")
    print(f"  Forwarding ke Web Server: {WEBSERVER_IP}:{WEBSERVER_PORT}")
    print(f"  Cache dir: {CACHE_DIR}")
    print(f"  Multithreading: aktif (thread-per-connection)")
    print("=" * 50)
    while True:
        try:
            client_sock, addr = server.accept()
            t = threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                daemon=True
            )
            t.start()
            print(f"[Proxy] Thread baru untuk {addr[0]} | Thread aktif: {threading.active_count()}")
        except Exception as e:
            print(f"[Proxy] Accept error: {e}")

if __name__ == "__main__":
    start_proxy()
