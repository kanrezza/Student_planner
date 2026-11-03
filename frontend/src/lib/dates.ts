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
