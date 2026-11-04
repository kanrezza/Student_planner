import { describe, expect, it } from 'vitest';
import {
  dropToPatch,
  resizeToPatch,
  roundTo15,
  selectionToNew,
  undoPatch,
} from '../src/features/calendar/dropToPatch';
import { makeTask } from './fixtures';

/** Giờ máy, giống FullCalendar (múi giờ `local`). */
const at = (day: number, h: number, m = 0) => new Date(2026, 10, day, h, m);

const worked = makeTask({
  id: 1,
  due_date: '2026-11-20',
  due_time: '23:59',
  work_date: '2026-11-16',
  work_start: '14:00',
  work_end: '16:00',
});
const timedDue = makeTask({ id: 2, due_date: '2026-11-18', due_time: '10:00' });
const dateOnly = makeTask({ id: 3, due_date: '2026-11-18' });

describe('roundTo15', () => {
  it('làm tròn tới 15 phút gần nhất', () => {
    expect(roundTo15(at(17, 9, 7))).toEqual(at(17, 9, 0));
    expect(roundTo15(at(17, 9, 8))).toEqual(at(17, 9, 15));
    expect(roundTo15(at(17, 9, 53))).toEqual(at(17, 10, 0));
  });
});

describe('dropToPatch — task có khung giờ làm', () => {
  it('sang giờ khác: giữ thời lượng, không đụng hạn chót', () => {
    expect(dropToPatch(worked, at(17, 9, 0), false)).toEqual({
      work_date: '2026-11-17',
      work_start: '09:00',
      work_end: '11:00',
    });
  });

  it('làm tròn 15 phút', () => {
    expect(dropToPatch(worked, at(17, 9, 8), false)).toMatchObject({
      work_start: '09:15',
      work_end: '11:15',
    });
  });

  it('kéo vào hàng Cả ngày: bỏ khung giờ làm, hạn chót là ngày đích', () => {
    expect(dropToPatch(worked, at(18, 0), true)).toEqual({
      work_date: null,
      work_start: null,
      work_end: null,
      due_date: '2026-11-18',
    });
  });

  it('không tràn qua nửa đêm', () => {
    expect(dropToPatch(worked, at(17, 23, 0), false)).toMatchObject({
      work_start: '23:00',
      work_end: '23:59',
    });
  });

  it('thả về chỗ cũ thì không có thay đổi', () => {
    expect(dropToPatch(worked, at(16, 14, 0), false)).toBeNull();
  });
});

describe('dropToPatch — task chỉ có giờ hạn', () => {
  it('giờ khác: đổi ngày và giờ hạn', () => {
    expect(dropToPatch(timedDue, at(19, 17, 0), false)).toEqual({
      due_date: '2026-11-19',
      due_time: '17:00',
    });
  });

  it('hàng Cả ngày: chỉ còn ngày hạn', () => {
    expect(dropToPatch(timedDue, at(19, 0), true)).toEqual({
      due_date: '2026-11-19',
      due_time: null,
    });
  });
});

describe('dropToPatch — task chỉ có ngày hạn', () => {
  it('vào lưới giờ: có khung giờ làm 1 giờ, hạn chót giữ nguyên', () => {
    const patch = dropToPatch(dateOnly, at(19, 10, 0), false);
    expect(patch).toEqual({ work_date: '2026-11-19', work_start: '10:00', work_end: '11:00' });
    expect(patch).not.toHaveProperty('due_date');
  });

  it('sang ô Cả ngày của ngày khác: đổi ngày hạn', () => {
    expect(dropToPatch(dateOnly, at(21, 0), true)).toEqual({ due_date: '2026-11-21' });
  });

  it('thả lại đúng ô Cả ngày cũ thì không đổi', () => {
    expect(dropToPatch(dateOnly, at(18, 0), true)).toBeNull();
  });
});

describe('resizeToPatch — kéo mép dưới', () => {
  it('đổi giờ kết thúc, làm tròn 15 phút', () => {
    expect(resizeToPatch(worked, at(16, 17, 8))).toEqual({ work_end: '17:15' });
  });

  it('tối thiểu 15 phút sau giờ bắt đầu', () => {
    expect(resizeToPatch(worked, at(16, 14, 5))).toEqual({ work_end: '14:15' });
    expect(resizeToPatch(worked, at(16, 13, 0))).toEqual({ work_end: '14:15' });
  });

  it('khối chỉ có giờ hạn hoặc chỉ ngày không kéo dãn được', () => {
    expect(resizeToPatch(timedDue, at(18, 11, 0))).toBeNull();
    expect(resizeToPatch(dateOnly, at(18, 11, 0))).toBeNull();
  });
});

describe('undoPatch', () => {
  it('trả giá trị cũ của đúng các trường đã đổi', () => {
    expect(
      undoPatch(worked, { work_start: '09:00', work_end: '11:00', work_date: '2026-11-17' }),
    ).toEqual({
      work_date: '2026-11-16',
      work_start: '14:00',
      work_end: '16:00',
    });
    expect(
      undoPatch(dateOnly, { work_date: '2026-11-19', work_start: '10:00', work_end: '11:00' }),
    ).toEqual({
      work_date: null,
      work_start: null,
      work_end: null,
    });
    expect(undoPatch(timedDue, { due_date: '2026-11-19', due_time: null })).toEqual({
      due_date: '2026-11-18',
      due_time: '10:00',
    });
  });
});

describe('selectionToNew — kéo vùng trống', () => {
  it('khung giờ làm bằng vùng đã kéo, hạn chót là ngày đó', () => {
    expect(selectionToNew(at(18, 10, 0), at(18, 11, 30), false)).toEqual({
      due: '2026-11-18',
      work_date: '2026-11-18',
      work_start: '10:00',
      work_end: '11:30',
    });
  });

  it('vùng qua nửa đêm bị cắt ở cuối ngày; vùng ngắn tối thiểu 15 phút', () => {
    expect(selectionToNew(at(18, 22, 0), at(19, 1, 0), false)).toMatchObject({ work_end: '23:59' });
    expect(selectionToNew(at(18, 10, 0), at(18, 10, 0), false)).toMatchObject({
      work_start: '10:00',
      work_end: '10:15',
    });
  });

  it('hàng Cả ngày: chỉ có hạn chót', () => {
    expect(selectionToNew(at(18, 0), at(19, 0), true)).toEqual({ due: '2026-11-18' });
  });
});
