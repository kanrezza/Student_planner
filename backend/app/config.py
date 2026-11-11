"""Cấu hình đọc từ biến môi trường (docker-compose.yml đặt các biến này)."""

import os

TIMEZONE = "Asia/Ho_Chi_Minh"
APP_VERSION = "0.3.0"
MAX_IMAGE_BYTES = 20 * 1024 * 1024  # FR-028: ảnh tối đa 20 MB
MAX_RESTORE_BYTES = 500 * 1024 * 1024  # file .lhbackup tối đa 500 MB (feature 003)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://lichhoc:lichhoc@localhost:5432/lichhoc"
)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://lichhoc:lichhoc@localhost:5432/lichhoc_test"
)
EASYOCR_MODEL_DIR = os.environ.get("EASYOCR_MODEL_DIR", "/opt/easyocr-models")
# Nơi lưu nội dung file đính kèm (feature 005): Docker named volume `lichhoc_attachments`.
ATTACHMENTS_DIR = os.environ.get("ATTACHMENTS_DIR", "/var/lib/lichhoc/attachments")


def flask_config() -> dict:
    return {
        "SQLALCHEMY_DATABASE_URI": DATABASE_URL,
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        "MAX_CONTENT_LENGTH": MAX_IMAGE_BYTES + 1024 * 1024,  # chừa phần đầu multipart
        "ATTACHMENTS_DIR": ATTACHMENTS_DIR,
    }
