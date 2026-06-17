# EcoVision — Backend

FastAPI + SQLAlchemy (async) + Alembic. Git repo & Docker độc lập.

## Yêu cầu trước khi chạy

1. **Network chung** đã tạo (một lần):
   ```bash
   docker network create ecovision-net
   ```
2. **Hạ tầng** đang chạy (Postgres/Redis/MinIO/MediaMTX) — xem repo `deployment/`:
   ```bash
   cd ../deployment && docker compose -f docker-compose.infra.yml up -d
   ```

## Chạy

```bash
cp .env.example .env        # điền MQTT_PASSWORD (broker của bạn)
docker compose up -d --build
```

| Mục | URL |
|---|---|
| Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Health sâu (DB/Redis/MinIO/MQTT) | http://localhost:8000/health/deep |

## Tạo admin đầu tiên

```bash
docker compose exec backend python scripts/seed.py    # admin / admin123
```

## Migrations (Alembic)

Dev nhanh: `CREATE_TABLES_ON_STARTUP=true` tự tạo bảng. Khi cần migration chuẩn:

```bash
docker compose exec backend alembic revision --autogenerate -m "init"
docker compose exec backend alembic upgrade head
```

## Cấu trúc

```
backend/
  apps/        auth (User), devices (Device) ...
  core/        config, database, security, mqtt, redis, storage, topics
  api/         health (và các router sau)
  workers/     tiến trình nền
  alembic/     migrations
  scripts/     seed.py
  main.py
```

## API Core (đã có)

| Nhóm | Endpoint |
|---|---|
| Auth | `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` |
| Users (admin) | `GET/POST /users` · `GET/PATCH /users/{id}` · `POST /users/{id}/reset-password` |
| Devices | `GET/POST /devices` · `GET/PATCH/DELETE /devices/{id}` · `POST /devices/{id}/heartbeat` |
| Alerts | `GET /alerts` · `GET /alerts/unread-count` · `POST /alerts` · `GET /alerts/{id}` · `POST /alerts/{id}/ack` · `/resolve` |
| Notifications | `GET /notifications/routes` · `GET /notifications/logs` · `POST /notifications/test` |
| Event Bus (admin) | `GET /events/recent` |
| Realtime | `WS /ws?token=<access_token>` |

Phân quyền: `admin` toàn quyền; `operator` vận hành (device/alert); `viewer` chỉ xem.
Dùng `Authorization: Bearer <access_token>` cho REST.

## Kết nối

Trong network `ecovision-net`, backend gọi hạ tầng theo tên service: `db`, `redis`,
`minio`, `mediamtx`. MQTT là broker external (cấu hình trong `.env`).

> Lưu ý: chạy `deployment/` (hạ tầng) trước, nếu không backend sẽ retry tới khi DB sẵn sàng.
