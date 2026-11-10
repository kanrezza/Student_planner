# Backend: Flask + gunicorn + EasyOCR (offline).
# Model EasyOCR được tải TRONG LÚC BUILD; lúc chạy dùng download_enabled=False nên không cần internet
# (constitution Nguyên tắc IV, spec FR-025/FR-029).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Ho_Chi_Minh \
    EASYOCR_MODEL_DIR=/opt/easyocr-models

# Thư viện hệ thống cần cho OpenCV (phụ thuộc của EasyOCR).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# pg_dump / pg_restore phải cùng hoặc mới hơn server (PostgreSQL 16) nên lấy từ kho PGDG chính thức
# (kho Debian chỉ có bản cũ hơn). Chỉ cần internet lúc build image (feature 003, research R2).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && install -d /etc/apt/keyrings \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc -o /etc/apt/keyrings/pgdg.asc \
    && . /etc/os-release \
    && echo "deb [signed-by=/etc/apt/keyrings/pgdg.asc] https://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PyTorch bản CPU (có wheel linux/arm64 cho Apple Silicon) — nhỏ hơn bản CUDA nhiều.
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Cài dependencies đọc từ pyproject.toml (runtime + dev để chạy test trong container).
COPY pyproject.toml ./
RUN python - <<'EOF' > /tmp/requirements.txt
import tomllib
project = tomllib.load(open("pyproject.toml", "rb"))["project"]
print("\n".join(project["dependencies"] + project["optional-dependencies"]["dev"]))
EOF
RUN pip install -r /tmp/requirements.txt

# Tải sẵn model EasyOCR (detector CRAFT + recognizer latin cho tiếng Việt) vào image.
RUN python -c "import easyocr; easyocr.Reader(['vi', 'en'], gpu=False, \
model_storage_directory='/opt/easyocr-models', download_enabled=True)"

COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
