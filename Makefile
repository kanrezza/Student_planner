.PHONY: test test-ocr

# Toàn bộ lint + test bằng một lệnh (constitution Nguyên tắc II).
test:
	./scripts/test.sh

test-ocr:
	./scripts/test.sh --ocr
