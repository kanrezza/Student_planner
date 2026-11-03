import { describe, expect, it } from 'vitest';
import { WEEKDAYS_VN, formatDate, formatDayLong, formatTime, toIsoDate } from '../src/lib/dates';

describe('định dạng ngày giờ Việt Nam', () => {
  it('ngày dài có Thứ', () => {
    expect(formatDayLong('2026-11-16')).toBe('Thứ Hai, 16/11/2026');
    expect(formatDayLong('2026-11-22')).toBe('Chủ Nhật, 22/11/2026');
  });

  it('ngày ngắn dd/mm/yyyy', () => {
    expect(formatDate('2027-01-03')).toBe('03/01/2027');
  });

  it('giờ 24h theo giờ Việt Nam, kể cả khi đầu vào là UTC', () => {
    expect(formatTime('2026-11-16T07:30:00+07:00')).toBe('07:30');
    expect(formatTime('2026-11-16T13:05:00Z')).toBe('20:05');
  });

  it('thời điểm gần nửa đêm UTC rơi vào ngày hôm sau ở Việt Nam', () => {
    expect(formatDayLong('2026-11-15T18:30:00Z')).toBe('Thứ Hai, 16/11/2026');
    expect(toIsoDate(new Date('2026-11-15T18:30:00Z'))).toBe('2026-11-16');
  });

  it('danh sách thứ bắt đầu từ Thứ Hai', () => {
    expect(WEEKDAYS_VN[0]).toBe('Thứ Hai');
    expect(WEEKDAYS_VN[6]).toBe('Chủ Nhật');
  });

  it('báo lỗi rõ ràng với chuỗi không hợp lệ', () => {
    expect(() => formatTime('không phải ngày')).toThrow('Ngày giờ không hợp lệ');
  });
});
