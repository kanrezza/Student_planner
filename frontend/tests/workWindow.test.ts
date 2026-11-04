import { describe, expect, it } from 'vitest';
import {
  defaultWorkWindow,
  isWorkAfterDue,
  workWindowError,
} from '../src/features/tasks/workWindow';

describe('khung giờ làm (FR-018)', () => {
  it('bật lần đầu: ngày hạn (chưa qua) lúc 09:00, hoặc hôm nay từ giờ tròn kế tiếp, dài 1 giờ', () => {
    expect(defaultWorkWindow({ due_date: '2026-11-12' }, '2026-11-09', 8 * 60 + 20)).toEqual({
      work_date: '2026-11-12',
      work_start: '09:00',
      work_end: '10:00',
    });
    expect(defaultWorkWindow({ due_date: null }, '2026-11-09', 14 * 60 + 5)).toEqual({
      work_date: '2026-11-09',
      work_start: '15:00',
      work_end: '16:00',
    });
    // Hạn đã qua → hôm nay; muộn quá thì không vượt 22:00–23:00 (trong một ngày).
    expect(defaultWorkWindow({ due_date: '2026-11-01' }, '2026-11-09', 23 * 60 + 30)).toEqual({
      work_date: '2026-11-09',
      work_start: '22:00',
      work_end: '23:00',
    });
  });

  it('báo lỗi giống backend', () => {
    expect(workWindowError({ work_date: '2026-11-09', work_start: '19:00' })).toEqual({
      work_date: 'Cần chọn đủ ngày, giờ bắt đầu và giờ kết thúc',
    });
    expect(
      workWindowError({ work_date: '2026-11-09', work_start: '19:00', work_end: '19:00' }),
    ).toEqual({ work_end: 'Giờ kết thúc phải sau giờ bắt đầu' });
    expect(
      workWindowError({ work_date: '2026-11-09', work_start: '19:00', work_end: '21:00' }),
    ).toBeNull();
  });

  it('cảnh báo khi khung giờ làm sau hạn chót', () => {
    expect(isWorkAfterDue({ work_date: '2026-11-13', due_date: '2026-11-12' })).toBe(true);
    expect(isWorkAfterDue({ work_date: '2026-11-12', due_date: '2026-11-12' })).toBe(false);
    expect(isWorkAfterDue({ work_date: '2026-11-12', due_date: null })).toBe(false);
  });
});
