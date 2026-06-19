import socket
import threading
import os
from datetime import datetime

# KONFIGURASI
TCP_HOST = '0.0.0.0'
TCP_PORT = 8000
UDP_HOST = '0.0.0.0'
UDP_PORT = 9000

# TCP SERVER (HTTP)
def handle_tcp_request(client_socket, client_addr):
    client_ip = client_addr[0]
    try:
        request_data = client_socket.recv(4096).decode('utf-8', errors='replace')
        if not request_data:
            return

        first_line = request_data.split('\r\n')[0]

        # Validasi request HTTP (anti malformed request)
        parts = first_line.split(' ')
        if len(parts) < 2:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[TCP] {timestamp} | IP: {client_ip} | Status: 400 Bad Request (malformed)")
            client_socket.sendall(
                b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"
            )
            return

        url_path = parts[1]
        if url_path == '/':
            url_path = '/index.html'

        filepath = '.' + url_path
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if os.path.exists(filepath) and os.path.isfile(filepath):
            # 200 OK
            with open(filepath, 'rb') as f:
                content = f.read()
            status_code = "200 OK"
            header = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(content)}\r\n"
                f"\r\n"
            ).encode('utf-8')
            client_socket.sendall(header + content)
        else:
            # 404 Not Found
            status_code = "404 Not Found"
            error_body = b"<html><body><h1>404 Not Found</h1></body></html>"
            header = (
                f"HTTP/1.1 404 Not Found\r\n"
                f"Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(error_body)}\r\n"
                f"\r\n"
            ).encode('utf-8')
            client_socket.sendall(header + error_body)

        # Log Wajib: IP client, jalur berkas, timestamp, status code
        print(f"[TCP] {timestamp} | IP: {client_ip} | Path: {url_path} | Status: {status_code}")

    except Exception as e:
        # 500 Internal Server Error
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[TCP] {timestamp} | IP: {client_ip} | Status: 500 Internal Server Error | Exception: {e}")
        try:
            error_body = b"<html><body><h1>500 Internal Server Error</h1></body></html>"
            header = (
                f"HTTP/1.1 500 Internal Server Error\r\n"
                f"Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(error_body)}\r\n"
                f"\r\n"
            ).encode('utf-8')
            client_socket.sendall(header + error_body)
        except:
            pass
    finally:
        client_socket.close()

def start_tcp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((TCP_HOST, TCP_PORT))
    server.listen(10)
    print(f"[TCP] Web Server (HTTP) berjalan di port {TCP_PORT}...")
    while True:
        try:
            client_sock, addr = server.accept()
            t = threading.Thread(
                target=handle_tcp_request,
                args=(client_sock, addr),
                daemon=True
            )
            t.start()
            print(f"[TCP] Thread baru untuk {addr[0]} | Thread aktif: {threading.active_count()}")
        except Exception as e:
            print(f"[TCP] Accept error: {e}")

# UDP SERVER (QoS ECHO)
def start_udp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((UDP_HOST, UDP_PORT))
    print(f"[UDP] Echo Server berjalan di port {UDP_PORT}...")
    while True:
        try:
            data, addr = server.recvfrom(1024)
            # Pantulkan payload PERSIS seperti diterima (tanpa modifikasi)
            server.sendto(data, addr)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[UDP] {timestamp} | Echo ke {addr[0]}:{addr[1]} | Payload: {data.decode('utf-8', errors='replace')}")
        except Exception as e:
            print(f"[UDP] Error: {e}")

# MAIN
if __name__ == "__main__":
    print("=" * 50)
    print("  Web Server running on port 8000 (TCP) / 9000 (UDP)")
    print("  Model: thread-per-connection | Thread pool: siap")
    print("=" * 50)
    tcp_thread = threading.Thread(target=start_tcp_server, daemon=True)
    udp_thread = threading.Thread(target=start_udp_server, daemon=True)
    tcp_thread.start()
    udp_thread.start()
    # Gunakan join agar main thread tidak langsung exit
    tcp_thread.join()
    udp_thread.join()
