# EcoVision — Deployment (hạ tầng dùng chung)

Hạ tầng dùng chung cho mọi project: **PostgreSQL (pgvector) · Redis · MinIO · MediaMTX**.
Nằm trong repo gốc; các project backend/ai_worker/frontend kết nối qua network `ecovision-net`.

## Chạy

```bash
# 1) tạo network chung (một lần duy nhất, dùng cho tất cả project)
docker network create ecovision-net

# 2) cấu hình + bật hạ tầng
cp .env.example .env
docker compose -f docker-compose.infra.yml up -d
```

| Service | Cổng | Ghi chú |
|---|---|---|
| PostgreSQL | 5432 | image pgvector (sẵn cho face embedding) |
| Redis | 6379 | |
| MinIO | 9000 / 9001 | API / Console (minioadmin/minioadmin) |
| MediaMTX | 8554/8889/8888/9997 | RTSP / WebRTC / HLS / API |

## Dừng

```bash
docker compose -f docker-compose.infra.yml down        # giữ dữ liệu
docker compose -f docker-compose.infra.yml down -v      # xóa luôn volume (dữ liệu)
```

## Ghi chú

- MQTT **không** nằm ở đây — bạn dùng broker external (cấu hình trong `backend/.env` & `ai_worker/.env`).
  Cần broker local để test: có sẵn `mosquitto.conf`, tự thêm service nếu muốn.
- Bật hạ tầng **trước** khi chạy backend/ai_worker.
