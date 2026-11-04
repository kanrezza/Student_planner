import { describe, expect, it } from 'vitest';
import {
  calendarTitle,
  scrollTimeFor,
  shiftDate,
  visibleRange,
} from '../src/features/calendar/calendarTitle';
import { monthGrid } from '../src/features/calendar/monthGrid';

describe('calendarTitle', () => {
  it('tuần trong một tháng: "Tháng 11, 2026"', () => {
    expect(calendarTitle('tuan', '2026-11-18')).toBe('Tháng 11, 2026');
  });

  it('tuần vắt hai tháng: "Tháng 11 – Tháng 12, 2026"', () => {
    // Tuần Thứ Hai 30/11 – Chủ Nhật 06/12/2026.
    expect(calendarTitle('tuan', '2026-12-02')).toBe('Tháng 11 – Tháng 12, 2026');
  });

  it('tuần vắt hai năm: "Tháng 12, 2026 – Tháng 1, 2027"', () => {
    // Tuần Thứ Hai 28/12/2026 – Chủ Nhật 03/01/2027.
    expect(calendarTitle('tuan', '2027-01-01')).toBe('Tháng 12, 2026 – Tháng 1, 2027');
  });

  it('chế độ Ngày và Tháng ghi tháng của ngày đang xem', () => {
    expect(calendarTitle('ngay', '2026-12-31')).toBe('Tháng 12, 2026');
    expect(calendarTitle('thang', '2027-02-14')).toBe('Tháng 2, 2027');
  });
});

describe('visibleRange và shiftDate', () => {
  it('tuần bắt đầu Thứ Hai', () => {
    expect(visibleRange('tuan', '2026-11-01')).toEqual({ start: '2026-10-26', end: '2026-11-01' });
    expect(visibleRange('tuan', '2026-11-16')).toEqual({ start: '2026-11-16', end: '2026-11-22' });
    expect(visibleRange('ngay', '2026-11-16')).toEqual({ start: '2026-11-16', end: '2026-11-16' });
    expect(visibleRange('thang', '2026-11-16')).toEqual({ start: '2026-11-01', end: '2026-11-30' });
  });

  it('trước/sau theo chế độ', () => {
    expect(shiftDate('ngay', '2026-11-30', 1)).toBe('2026-12-01');
    expect(shiftDate('tuan', '2026-11-18', -1)).toBe('2026-11-11');
    expect(shiftDate('thang', '2026-01-31', 1)).toBe('2026-02-01');
    expect(shiftDate('thang', '2026-01-15', -1)).toBe('2025-12-01');
  });
});

describe('scrollTimeFor', () => {
  const now = new Date('2026-11-18T14:20:00+07:00'); // Thứ Tư

  it('tuần có hôm nay → giờ hiện tại − 1 giờ', () => {
    expect(scrollTimeFor('tuan', '2026-11-16', now)).toBe('13:00:00');
    expect(scrollTimeFor('ngay', '2026-11-18', now)).toBe('13:00:00');
  });

  it('không âm khi vừa qua nửa đêm', () => {
    expect(scrollTimeFor('tuan', '2026-11-18', new Date('2026-11-18T00:30:00+07:00'))).toBe(
      '00:00:00',
    );
  });

  it('tuần/ngày khác → 06:00', () => {
    expect(scrollTimeFor('tuan', '2026-11-25', now)).toBe('06:00:00');
    expect(scrollTimeFor('ngay', '2026-11-17', now)).toBe('06:00:00');
  });
});

describe('monthGrid', () => {
  it('6 hàng × 7 ngày, bắt đầu Thứ Hai; tháng 11/2026 bắt đầu Chủ Nhật 01/11', () => {
    const grid = monthGrid('2026-11');
    expect(grid).toHaveLength(6);
    expect(grid.every((row) => row.length === 7)).toBe(true);
    expect(grid[0][0]).toEqual({ date: '2026-10-26', day: 26, outside: true });
    expect(grid[0][6]).toEqual({ date: '2026-11-01', day: 1, outside: false });
    expect(grid[5][6]).toEqual({ date: '2026-12-06', day: 6, outside: true });
    const inside = grid.flat().filter((cell) => !cell.outside);
    expect(inside).toHaveLength(30);
  });

  it('tháng 2/2027 (28 ngày, bắt đầu Thứ Hai)', () => {
    const grid = monthGrid('2027-02');
    expect(grid[0][0]).toEqual({ date: '2027-02-01', day: 1, outside: false });
    expect(grid[3][6]).toEqual({ date: '2027-02-28', day: 28, outside: false });
    expect(grid[4][0]).toEqual({ date: '2027-03-01', day: 1, outside: true });
    expect(grid.flat().filter((cell) => !cell.outside)).toHaveLength(28);
  });
});
