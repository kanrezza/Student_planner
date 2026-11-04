/** Lưới lịch tháng nhỏ ở cột bên trang Lịch (FR-021): 6 hàng × 7 ngày, bắt đầu Thứ Hai. */
import { addDays } from '../../lib/dates';
import { startOfWeek } from './calendarTitle';

export type MonthCell = { date: string; day: number; outside: boolean };

/** `month` dạng "YYYY-MM". Ngày của tháng trước/sau có `outside: true`. */
export function monthGrid(month: string): MonthCell[][] {
  const first = `${month}-01`;
  const start = startOfWeek(first);
  return Array.from({ length: 6 }, (_, row) =>
    Array.from({ length: 7 }, (_, col) => {
      const date = addDays(start, row * 7 + col);
      return { date, day: Number(date.slice(8, 10)), outside: date.slice(0, 7) !== month };
    }),
  );
}

/** "YYYY-MM" của tháng trước/sau. */
export function shiftMonth(month: string, dir: 1 | -1): string {
  const [y, m] = month.split('-').map(Number);
  const index = y * 12 + (m - 1) + dir;
  return `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, '0')}`;
}
