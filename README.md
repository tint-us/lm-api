# 🟡 lm-api

**lm-api** adalah service API sederhana berbasis [FastAPI](https://fastapi.tiangolo.com/) untuk mengambil **harga emas ANTAM** harian (1 gram).  
API ini sudah dilengkapi dengan **Bearer Token authentication**, caching sederhana, dan bisa dijalankan via **Docker**.

---

## ✨ Features

- Ambil **harga emas harian** dari sumber resmi (emasantam.id).
- Return data dalam format JSON.
- **Auth dengan Bearer Token** (`APP_TOKEN`).
- **Caching** untuk mengurangi hit ke website sumber.
- **Docker ready** (jalan di port `8088`).
- Endpoint **health check** untuk monitoring.

---

## 📦 Setup

### 1. Clone repository
```bash
git clone https://github.com/tint-us/lm-api.git
cd lm-api
```

### 2. Buat file `.env`
Salin contoh file:
```bash
cp .env.example .env
```

Edit `.env` sesuai kebutuhan:
```dotenv
APP_TOKEN=isi_token_rahasia_kamu
SOURCE_URL=https://emasantam.id/harga-emas-antam-harian/
CACHE_TTL_SEC=300
HTTP_TIMEOUT=12
HTTP_RETRIES=3
```

### 3. Build & jalankan Docker
```bash
docker compose up -d --build
```

Cek apakah container sudah jalan:
```bash
docker ps
```

---

## 🚀 Usage

### 1. Health check (tanpa auth)
```bash
curl -s http://localhost:8088/health | jq
```

Contoh response:
```json
{
  "ok": true,
  "service": "lm-api",
  "source_url": "https://emasantam.id/harga-emas-antam-harian/"
}
```

### 2. Ambil harga emas (dengan auth)
```bash
curl -s -H "Authorization: Bearer abcde" http://localhost:8088/harga | jq
```

Contoh response:
```json
{
  "harga_tanggal_text": "18 September 2025",
  "harga_idr": 2115000,
  "source_url": "https://emasantam.id/harga-emas-antam-harian/",
  "fetched_at_utc": "2025-09-18T02:40:00.000000+00:00",
  "note": "harga via selector | tanggal via selector"
}
```

---

## 📖 API Endpoints

### `GET /health`
- **Auth**: ❌ Tidak perlu
- **Description**: Untuk memastikan service hidup (liveness check).
- **Response**:
```json
{
  "ok": true,
  "service": "lm-api",
  "source_url": "https://emasantam.id/harga-emas-antam-harian/"
}
```

### `GET /harga`
- **Auth**: ✅ Wajib Bearer Token (`Authorization: Bearer <APP_TOKEN>`)
- **Description**: Mengambil harga emas 1 gram untuk tanggal berjalan.
- **Response**:
```json
{
  "harga_tanggal_text": "18 September 2025",
  "harga_idr": 2115000,
  "source_url": "https://emasantam.id/harga-emas-antam-harian/",
  "fetched_at_utc": "2025-09-18T02:40:00.000000+00:00",
  "note": "harga via selector | tanggal via selector"
}
```

---

## 🛠️ Development (opsional, tanpa Docker)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8088
```

---

## 🤝 Contributing 
Pull request dipersilakan! Untuk fitur baru / bugfix, buat branch lalu PR ke `main`.

---

## 🤝 Collaboration 
Just drop your email to tintus.ardi@gmail.com.

---


## 📜 License
MIT License. Lihat [LICENSE](LICENSE) file untuk detail.
