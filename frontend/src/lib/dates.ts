/**
 * Định dạng ngày giờ kiểu Việt Nam (FR-026, research R10): "Thứ Hai, 16/11/2026", giờ 24h.
 * Luôn tính theo múi giờ Asia/Ho_Chi_Minh, kể cả khi trình duyệt đặt múi giờ khác.
 */
export const TIME_ZONE = 'Asia/Ho_Chi_Minh';

export const WEEKDAYS_VN = [
  'Thứ Hai',
  'Thứ Ba',
  'Thứ Tư',
  'Thứ Năm',
  'Thứ Sáu',
  'Thứ Bảy',
  'Chủ Nhật',
] as const;

type DateParts = { year: number; month: number; day: number; hour: number; minute: number };

const partsFormatter = new Intl.DateTimeFormat('en-GB', {
  timeZone: TIME_ZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
});

/** Nhận "YYYY-MM-DD" (ngày thuần) hoặc ISO có offset; trả các thành phần theo giờ Việt Nam. */
function toParts(iso: string): DateParts {
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (dateOnly) {
    return { year: +dateOnly[1], month: +dateOnly[2], day: +dateOnly[3], hour: 0, minute: 0 };
  }
  const instant = new Date(iso);
  if (Number.isNaN(instant.getTime())) throw new Error(`Ngày giờ không hợp lệ: ${iso}`);
  const get = (type: string) =>
    Number(partsFormatter.formatToParts(instant).find((p) => p.type === type)?.value);
  return {
    year: get('year'),
    month: get('month'),
    day: get('day'),
    hour: get('hour'),
    minute: get('minute'),
  };
}

const pad = (n: number) => String(n).padStart(2, '0');

/** 0 = Thứ Hai … 6 = Chủ Nhật. */
function weekdayIndex({ year, month, day }: DateParts): number {
  const jsDay = new Date(Date.UTC(year, month - 1, day)).getUTCDay(); // 0 = Chủ Nhật
  return (jsDay + 6) % 7;
}

/** "16/11/2026" */
export function formatDate(iso: string): string {
  const p = toParts(iso);
  return `${pad(p.day)}/${pad(p.month)}/${p.year}`;
}

/** "Thứ Hai, 16/11/2026" */
export function formatDayLong(iso: string): string {
  const p = toParts(iso);
  return `${WEEKDAYS_VN[weekdayIndex(p)]}, ${formatDate(iso)}`;
}

/** "07:30" (24 giờ) */
export function formatTime(iso: string): string {
  const p = toParts(iso);
  return `${pad(p.hour)}:${pad(p.minute)}`;
}

/** Ngày theo giờ Việt Nam của một thời điểm, dạng "YYYY-MM-DD" (dùng khi gọi API). */
export function toIsoDate(d: Date): string {
  const p = toParts(d.toISOString());
  return `${p.year}-${pad(p.month)}-${pad(p.day)}`;
}

/** "2026-11-09" + 3 → "2026-11-12" (ngày thuần, không phụ thuộc múi giờ). */
export function addDays(isoDate: string, days: number): string {
  const [y, m, d] = isoDate.split('-').map(Number);
  const next = new Date(Date.UTC(y, m - 1, d + days));
  return next.toISOString().slice(0, 10);
}

/** Số ngày từ `from` tới `to` (ngày thuần). */
export function daysBetween(from: string, to: string): number {
  const parse = (iso: string) => {
    const [y, m, d] = iso.split('-').map(Number);
    return Date.UTC(y, m - 1, d);
  };
  return Math.round((parse(to) - parse(from)) / 86_400_000);
}

/** 1 = Thứ Hai … 7 = Chủ Nhật của một ngày thuần. */
export function isoWeekday(isoDate: string): number {
  return weekdayIndex(toParts(isoDate)) + 1;
}

/** "Thứ Năm, 12/11" */
export function formatDayShort(isoDate: string): string {
  const p = toParts(isoDate);
  return `${WEEKDAYS_VN[weekdayIndex(p)]}, ${pad(p.day)}/${pad(p.month)}`;
}

/** "12/11" */
export function formatDayMonth(isoDate: string): string {
  const p = toParts(isoDate);
  return `${pad(p.day)}/${pad(p.month)}`;
}

/** Thời điểm 00:00 (giờ Việt Nam) của một ngày thuần. */
export function startOfDayVn(isoDate: string): Date {
  return new Date(`${isoDate}T00:00:00+07:00`);
}

/** "T2 16/11" · "CN 22/11" — thứ viết tắt kèm ngày/tháng (dùng cho dấu "Đã dời (từ …)"). */
export function formatDayAbbr(isoDate: string): string {
  const p = toParts(isoDate);
  const index = weekdayIndex(p);
  return `${index === 6 ? 'CN' : `T${index + 2}`} ${pad(p.day)}/${pad(p.month)}`;
}

/** "30/11/2026" (cũng nhận "-", "." và ngày/tháng 1 chữ số) → "2026-11-30"; sai/không có thật → null. */
export function parseVnDate(text: string): string | null {
  const m = /^\s*(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\s*$/.exec(text);
  if (!m) return null;
  const day = Number(m[1]);
  const month = Number(m[2]);
  const year = Number(m[3]);
  const d = new Date(Date.UTC(year, month - 1, day));
  if (d.getUTCFullYear() !== year || d.getUTCMonth() !== month - 1 || d.getUTCDate() !== day) {
    return null;
  }
  return `${String(year).padStart(4, '0')}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

/** "2026-11-30" → "30/11/2026"; rỗng hoặc không đúng dạng → "". */
export function isoToVnDate(iso: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? '');
  return m ? `${m[3]}/${m[2]}/${m[1]}` : '';
}
