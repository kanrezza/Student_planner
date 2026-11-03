import { describe, expect, it } from 'vitest';
import {
  blankToNull,
  formatDue,
  priorityLabel,
  sessionTimeRange,
  weekdaysLabel,
} from '../src/lib/format';

describe('định dạng hiển thị', () => {
  it('hạn chót có hoặc không có giờ', () => {
    expect(formatDue({ due_date: '2026-11-10', due_time: '17:00' })).toBe(
      'Thứ Ba, 10/11/2026 17:00',
    );
    expect(formatDue({ due_date: '2026-11-10', due_time: null })).toBe('Thứ Ba, 10/11/2026');
    expect(formatDue({ due_date: null, due_time: null })).toBe('Không có hạn chót');
  });

  it('mức ưu tiên tiếng Việt', () => {
    expect([1, 2, 3].map((p) => priorityLabel(p as 1 | 2 | 3))).toEqual([
      'Cao',
      'Trung bình',
      'Thấp',
    ]);
  });

  it('khung giờ buổi học 24h', () => {
    expect(
      sessionTimeRange({
        start_at: '2026-11-10T13:00:00+07:00',
        end_at: '2026-11-10T15:40:00+07:00',
      }),
    ).toBe('13:00 – 15:40');
  });

  it('thứ viết tắt', () => {
    expect(weekdaysLabel([1, 4, 7])).toBe('T2, T5, CN');
  });

  it('chuỗi trống thành null', () => {
    expect(blankToNull('   ')).toBeNull();
    expect(blankToNull(' A101 ')).toBe('A101');
  });
});
