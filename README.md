# lm-api

API sederhana untuk mengambil harga emas ANTAM (tanggal & harga rupiah).

## Jalankan dengan Docker

```bash
docker compose up -d --build
```

## Auth

Semua endpoint data dilindungi **Bearer Token**. Set `APP_TOKEN` di environment/container.

## Endpoint

- `GET /health` → tanpa auth
- `GET /harga` → dengan `Authorization: Bearer <APP_TOKEN>`
