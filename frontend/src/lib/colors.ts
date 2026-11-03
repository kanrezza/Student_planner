/**
 * Bảng 12 màu cố định, dùng chung cho môn học, danh sách và nhãn (backend lưu mã c01…c12).
 * Các màu đủ đậm để chữ trắng đọc rõ (tương phản ≥ 4.5:1).
 */
export const PALETTE: Record<string, string> = {
  c01: '#1d4ed8', // xanh dương
  c02: '#047857', // xanh lục
  c03: '#b45309', // cam đất
  c04: '#7c3aed', // tím
  c05: '#0e7490', // xanh mòng két
  c06: '#be185d', // hồng đậm
  c07: '#b91c1c', // đỏ
  c08: '#4d7c0f', // xanh lá mạ
  c09: '#6d28d9', // tím than
  c10: '#a16207', // vàng nâu
  c11: '#334155', // xám xanh
  c12: '#9f1239', // đỏ mận
};

export const PALETTE_CODES = Object.keys(PALETTE);

const FALLBACK = PALETTE.c11;

export function colorHex(code: string | null | undefined): string {
  return (code && PALETTE[code]) || FALLBACK;
}
