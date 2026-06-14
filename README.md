# Client–Proxy–Server with TCP/UDP Socket Programming

Implementasi sistem **Client–Proxy–Server berbasis Python Socket Programming** untuk memenuhi Tugas Besar Mata Kuliah Jaringan Komputer.

Sistem terdiri dari tiga komponen utama:

* **Client**
* **Proxy Server**
* **Web Server**

yang berkomunikasi melalui jaringan LAN menggunakan protokol **TCP** dan **UDP**.

Selain implementasi komunikasi jaringan, proyek ini juga mengevaluasi:

* Mekanisme caching pada Proxy Server
* Quality of Service (QoS)
* Multithreading (Thread-per-Connection)
* Performa Cache HIT vs Cache MISS
* Performa Single Client vs Multi Client

---

# 📌 Fitur Utama

## Web Server

* HTTP Server berbasis TCP
* UDP Echo Server
* Parsing HTTP Request secara manual
* Multi-client menggunakan multithreading
* Logging aktivitas client
* Status code:

  * 200 OK
  * 400 Bad Request
  * 404 Not Found
  * 500 Internal Server Error

## Proxy Server

* Forward HTTP Request ke Web Server
* Cache lokal berbasis file
* Cache HIT dan Cache MISS detection
* Atomic cache write
* Thread-safe cache access menggunakan `threading.Lock()`
* Error handling:

  * 400 Bad Request
  * 502 Bad Gateway
  * 504 Gateway Timeout

## Client

### TCP Mode

Mengirim HTTP GET Request melalui Proxy Server.

### UDP Mode

Melakukan pengukuran QoS:

* RTT (Round Trip Time)
* Jitter
* Packet Loss
* Throughput

Hasil pengujian otomatis disimpan ke file CSV.

---

# 🏗️ Arsitektur Sistem

```text
+---------+
| Client  |
+---------+
     |
     | TCP :8080
     v
+-------------+
| ProxyServer |
+-------------+
     |
     | TCP :8000
     v
+------------+
| Web Server |
+------------+

UDP QoS Measurement
Client <-------> Web Server (:9000)
```

## Alur Komunikasi

1. Client mengirim HTTP Request ke Proxy Server.
2. Proxy melakukan pengecekan cache.

### Cache HIT

```text
Client
   |
   v
Proxy Cache
   |
   +--> Response langsung
```

### Cache MISS

```text
Client
   |
   v
Proxy
   |
   v
Web Server
   |
   v
Proxy (Store Cache)
   |
   v
Client
```

---

# 📂 Struktur Project

```text
.
├── client.py
├── proxy.py
├── webserver.py
├── cache_dir/
│   └── ...
├── index.html
├── qos_result_*.csv
└── README.md
```

---

# ⚙️ Requirements

* Python 3.13+
* Python Socket Library
* Threading
* CSV
* OS

Semua library yang digunakan merupakan library bawaan Python.

---

# 🚀 Cara Menjalankan

## 1. Menjalankan Web Server

```bash
python webserver.py
```

Server akan membuka:

```text
TCP  : 8000
UDP  : 9000
```

---

## 2. Menjalankan Proxy Server

```bash
python proxy.py
```

Proxy berjalan pada:

```text
TCP : 8080
```

---

## 3. Menjalankan Client TCP

```bash
python client.py -mode tcp -file index.html
```

Contoh:

```bash
python client.py -mode tcp -file about.html
```

---

## 4. Menjalankan Client UDP (QoS)

```bash
python client.py -mode udp
```

Output:

```text
RTT Min
RTT Avg
RTT Max
Packet Loss
Jitter
Throughput
```

Hasil otomatis tersimpan pada:

```text
qos_result_<timestamp>.csv
```

---

# 📊 Hasil Pengujian QoS

| Parameter   | Rata-rata |
| ----------- | --------- |
| Packet Loss | 2%        |
| RTT Min     | 20.84 ms  |
| RTT Avg     | 146.07 ms |
| RTT Max     | 429.73 ms |
| Jitter      | 186.12 ms |
| Throughput  | 2.46 kbps |

---

# ⚡ Analisis Cache

## Single Client

| Request | Cache | Latency    |
| ------- | ----- | ---------- |
| 1       | MISS  | 1094.70 ms |
| 2       | HIT   | 1.39 ms    |
| 3       | HIT   | 1.06 ms    |
| 4       | HIT   | 0.72 ms    |
| 5       | HIT   | 0.90 ms    |

### Hasil

Reduksi latensi mencapai sekitar:

```text
99.9%
```

setelah konten tersimpan pada cache Proxy.

---

# 🧵 Multithreading

Sistem menggunakan model:

```text
Thread-per-Connection
```

Setiap koneksi client akan mendapatkan thread tersendiri.

Contoh hasil pengujian:

| Client | Thread Aktif |
| ------ | ------------ |
| 1      | 2            |
| 2      | 3            |
| 3      | 4            |
| 5      | 6            |

Semua request berhasil diproses tanpa kegagalan.

---

# 🛡️ Error Handling

## Web Server

| Kondisi              | Status                    |
| -------------------- | ------------------------- |
| File ditemukan       | 200 OK                    |
| File tidak ditemukan | 404 Not Found             |
| Request tidak valid  | 400 Bad Request           |
| Internal error       | 500 Internal Server Error |

## Proxy Server

| Kondisi            | Status              |
| ------------------ | ------------------- |
| Invalid request    | 400 Bad Request     |
| Timeout            | 504 Gateway Timeout |
| Connection refused | 504 Gateway Timeout |
| Bad gateway        | 502 Bad Gateway     |

---

# 🔒 Keamanan dan Reliability

Fitur yang diterapkan:

* `SO_REUSEADDR`
* `threading.Lock()`
* Cache atomic write
* Path traversal sanitization
* Socket timeout
* Graceful error handling
* Daemon thread

---

# 📈 Pengembangan Selanjutnya

Beberapa peningkatan yang dapat dilakukan:

* Implementasi Thread Pool
* AsyncIO Architecture
* Cache TTL (Time To Live)
* TLS/SSL Encryption
* Fine-grained Cache Locking
* Pengujian QoS pada jaringan kabel
* Dukungan jumlah client yang lebih besar

---

# 📚 Referensi

* Python Socket Documentation
* Python Threading Documentation
* RFC 768 (UDP)
* RFC 793 (TCP)
* RFC 2616 (HTTP/1.1)
* RFC 9110 (HTTP Semantics)

---

## 📄 Lisensi

Project ini dibuat untuk keperluan akademik dalam Mata Kuliah **Jaringan Komputer**.

---

## our honest reaction

<img width="478" height="241" alt="image" src="https://github.com/user-attachments/assets/f9b7271d-0e52-4ce2-9fe0-0ef8b9635b2e" />

---

