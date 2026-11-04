/**
 * Hàm thuần cho đầu trang Lịch (FR-020, FR-021): khoảng đang xem, tiêu đề tháng/năm, trước/sau,
 * giờ cuộn tới. Ngày là chuỗi "YYYY-MM-DD"; tuần bắt đầu Thứ Hai.
 */
import { addDays, formatTime, isoWeekday, toIsoDate } from '../../lib/dates';

export type CalendarMode = 'ngay' | 'tuan' | 'thang';

export const CALENDAR_MODES: CalendarMode[] = ['ngay', 'tuan', 'thang'];

export function isCalendarMode(value: unknown): value is CalendarMode {
  return CALENDAR_MODES.includes(value as CalendarMode);
}

/** Tên chế độ của FullCalendar. */
export const FC_VIEW: Record<CalendarMode, string> = {
  ngay: 'timeGridDay',
  tuan: 'timeGridWeek',
  thang: 'dayGridMonth',
};

const split = (date: string) => date.split('-').map(Number) as [number, number, number];
const pad = (n: number) => String(n).padStart(2, '0');

export function startOfWeek(date: string): string {
  return addDays(date, 1 - isoWeekday(date));
}

function lastDayOfMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

/** Khoảng ngày đang xem [start, end] (gồm cả hai đầu). */
export function visibleRange(mode: CalendarMode, date: string): { start: string; end: string } {
  if (mode === 'ngay') return { start: date, end: date };
  if (mode === 'tuan') {
    const start = startOfWeek(date);
    return { start, end: addDays(start, 6) };
  }
  const [y, m] = split(date);
  return { start: `${y}-${pad(m)}-01`, end: `${y}-${pad(m)}-${pad(lastDayOfMonth(y, m))}` };
}

/** "Tháng 11, 2026"; "Tháng 11 – Tháng 12, 2026"; "Tháng 12, 2026 – Tháng 1, 2027". */
export function calendarTitle(mode: CalendarMode, date: string): string {
  const { start, end } = mode === 'thang' ? { start: date, end: date } : visibleRange(mode, date);
  const [y1, m1] = split(start);
  const [y2, m2] = split(end);
  if (y1 !== y2) return `Tháng ${m1}, ${y1} – Tháng ${m2}, ${y2}`;
  if (m1 !== m2) return `Tháng ${m1} – Tháng ${m2}, ${y1}`;
  return `Tháng ${m1}, ${y1}`;
}

/** Khoảng trước (`-1`) / sau (`1`). Chế độ Tháng về ngày 1 của tháng đích. */
export function shiftDate(mode: CalendarMode, date: string, dir: 1 | -1): string {
  if (mode === 'ngay') return addDays(date, dir);
  if (mode === 'tuan') return addDays(date, 7 * dir);
  const [y, m] = split(date);
  const index = y * 12 + (m - 1) + dir;
  return `${Math.floor(index / 12)}-${pad((index % 12) + 1)}-01`;
}

/** Tuần (hoặc ngày) có hôm nay → cuộn tới giờ hiện tại − 1 giờ; ngược lại 06:00. */
export function scrollTimeFor(mode: CalendarMode, date: string, now: Date): string {
  const today = toIsoDate(now);
  const { start, end } = visibleRange(mode, date);
  if (mode === 'thang' || today < start || today > end) return '06:00:00';
  const hour = Number(formatTime(now.toISOString()).slice(0, 2));
  return `${pad(Math.max(hour - 1, 0))}:00:00`;
}
