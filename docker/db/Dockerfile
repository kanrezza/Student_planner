# Postgres kèm sẵn script khởi tạo (tạo DB test) — nướng vào image thay vì bind mount từ thư mục dự án.
FROM postgres:16-alpine
COPY 01-test-db.sql /docker-entrypoint-initdb.d/01-test-db.sql
