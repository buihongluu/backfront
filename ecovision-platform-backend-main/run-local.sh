#!/usr/bin/env bash
# Chạy backend TRỰC TIẾP trên máy bằng môi trường conda base (không build Docker, không venv).
# Yêu cầu: đã `conda activate base` (Python >= 3.11) + hạ tầng đang chạy:
#   cd deployment && docker compose -f docker-compose.infra.yml up -d
set -e
cd "$(dirname "$0")"

python -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3,11) else 1)' \
  || { echo "❌ Cần Python >= 3.11. Hãy 'conda activate base' rồi chạy lại."; exit 1; }
echo "→ Dùng $(python --version) tại $(which python)"

pip install -q -r requirements.txt

# Kết nối hạ tầng qua localhost (ghi đè host 'db/redis/minio' của Docker)
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
export MINIO_ENDPOINT=localhost:9000
export MEDIAMTX_API=http://localhost:9997

python scripts/seed.py || true

echo "→ Backend: http://localhost:8000/docs"
exec python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
