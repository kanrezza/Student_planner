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

export type ColorScheme = 'light' | 'dark';

/** Nền cửa sổ của từng chế độ (khớp `--color-bg` trong index.css). */
export const SCHEME_BACKGROUND: Record<ColorScheme, string> = {
  light: '#ffffff',
  dark: '#1d1e21',
};

function hexToRgb(hex: string): [number, number, number] {
  const value = hex.replace('#', '');
  return [0, 2, 4].map((i) => parseInt(value.slice(i, i + 2), 16)) as [number, number, number];
}

function rgbToHex([r, g, b]: [number, number, number]): string {
  return `#${[r, g, b].map((c) => Math.round(c).toString(16).padStart(2, '0')).join('')}`;
}

/** Trộn hai màu: `amount` = tỉ lệ của màu `b` (0 → a, 1 → b). */
export function mixHex(a: string, b: string, amount: number): string {
  const ca = hexToRgb(a);
  const cb = hexToRgb(b);
  return rgbToHex(
    [0, 1, 2].map((i) => ca[i] + (cb[i] - ca[i]) * amount) as [number, number, number],
  );
}

/** Nền nhạt của khối trên lịch, chip nhãn (feature 002 FR-023). */
export function colorSoft(code: string | null | undefined, scheme: ColorScheme): string {
  const base = colorHex(code);
  return scheme === 'light'
    ? mixHex(base, '#ffffff', 0.86)
    : mixHex(base, SCHEME_BACKGROUND.dark, 0.7);
}

/** Màu chữ/viền đậm đi kèm `colorSoft`, đủ tương phản 4.5:1 trên nền nhạt (FR-032). */
export function colorStrong(code: string | null | undefined, scheme: ColorScheme): string {
  const base = colorHex(code);
  return scheme === 'light' ? mixHex(base, '#000000', 0.2) : mixHex(base, '#ffffff', 0.6);
}

/** Chế độ màu hiện tại của macOS/trình duyệt. */
export function currentScheme(): ColorScheme {
  return typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light';
}
