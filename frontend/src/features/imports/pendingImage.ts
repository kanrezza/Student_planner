/**
 * Ảnh vừa dán ở trang Môn học / Lịch thi, chờ màn hình Nhập từ ảnh nhận.
 * Chỉ nằm trong bộ nhớ của trang (không localStorage, không gửi đi đâu) — FR-035.
 */
let pending: File | null = null;

export function setPendingImage(file: File): void {
  pending = file;
}

/** Lấy ảnh đang chờ và xoá khỏi bộ nhớ (chỉ lấy được một lần). */
export function takePendingImage(): File | null {
  const file = pending;
  pending = null;
  return file;
}
