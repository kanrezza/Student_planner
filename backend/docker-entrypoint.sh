#!/bin/sh
# Có tham số (ví dụ `docker compose run --rm backend pytest`): chạy đúng lệnh đó.
# Không có tham số: chờ PostgreSQL, chạy migration, rồi khởi động gunicorn.
set -e

export FLASK_APP="app:create_app"

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

attempt=1
until flask db upgrade; do
    if [ "$attempt" -ge 30 ]; then
        echo "Không chạy được migration sau 30 lần thử, dừng lại." >&2
        exit 1
    fi
    echo "Database chưa sẵn sàng (lần $attempt/30), thử lại sau 1 giây..."
    attempt=$((attempt + 1))
    sleep 1
done

# 1 worker × 4 thread: model EasyOCR chỉ nạp một lần; timeout 120 giây cho endpoint nhận diện ảnh.
exec gunicorn -w 1 --threads 4 --timeout 120 -b 0.0.0.0:8000 "app:create_app()"
