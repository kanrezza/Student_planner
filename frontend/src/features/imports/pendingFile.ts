/**
 * Ảnh hoặc PDF vừa dán/thả ở trang Môn học / Lịch thi, chờ màn hình Nhập lịch nhận.
 * Chỉ nằm trong bộ nhớ của trang (không localStorage, không gửi đi đâu) — FR-035.
 */
let pending: File | null = null;

export function setPendingFile(file: File): void {
  pending = file;
}

/** Lấy file đang chờ và xoá khỏi bộ nhớ (chỉ lấy được một lần). */
export function takePendingFile(): File | null {
  const file = pending;
  pending = null;
  return file;
}
