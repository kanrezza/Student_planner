import { describe, expect, it } from 'vitest';
import type { CalendarData, ClassSession, Task } from '../src/api/types';
import { toCalendarEvents } from '../src/lib/calendarEvents';
import { colorHex } from '../src/lib/colors';
import { shiftRanges } from '../src/lib/shifts';
import { formatTagParam, parseTagParam, toggleTag } from '../src/lib/tagFilter';

const tag = (id: number, color: string) => ({ id, name: `N${id}`, color, system_key: null });

const session = (over: Partial<ClassSession> = {}): ClassSession => ({
  id: 1,
  subject_id: 7,
  subject_name: 'Giải tích 1',
  date: '2026-11-16',
  start_at: '2026-11-16T06:45:00+07:00',
  end_at: '2026-11-16T09:25:00+07:00',
  room: 'A2-301',
  lecturer: null,
  class_code: null,
  is_cancelled: false,
  time_overridden: false,
  room_overridden: false,
  color: 'c01',
  tags: [],
  own_tag_ids: [],
  display_color: 'c01',
  shift_label: 'Ca 1',
  auto_task_id: null,
  ...over,
});

const task = (over: Partial<Task> = {}): Task => ({
  id: 5,
  title: 'Nộp bài',
  notes: null,
  due_date: '2026-11-17',
  due_time: '17:00',
  due_at: '2026-11-17T17:00:00+07:00',
  priority: 2,
  list_id: 1,
  list_name: 'Học tập',
  completed: false,
  completed_at: null,
  is_overdue: false,
  is_auto: false,
  source_session_id: null,
  user_modified: false,
  tags: [],
  display_color: 'c02',
  reminder_minutes: null,
  reminder_at: null,
  ...over,
});

const data = (sessions: ClassSession[], tasks: Task[]): CalendarData => ({ sessions, tasks });

describe('toCalendarEvents', () => {
  it('buổi học là sự kiện có giờ, màu theo display_color', () => {
    const [e] = toCalendarEvents(data([session()], []));
    expect(e).toMatchObject({
      id: 'session-1',
      title: 'Giải tích 1 · A2-301',
      start: '2026-11-16T06:45:00+07:00',
      end: '2026-11-16T09:25:00+07:00',
      allDay: false,
      backgroundColor: colorHex('c01'),
      classNames: [],
    });
  });

  it('buổi huỷ có class is-cancelled', () => {
    const [e] = toCalendarEvents(data([session({ is_cancelled: true })], []));
    expect(e.classNames).toEqual(['is-cancelled']);
  });

  it('task có giờ là sự kiện có giờ; task chỉ có ngày là sự kiện cả ngày', () => {
    const [timed, dateOnly] = toCalendarEvents(
      data([], [task(), task({ id: 6, due_time: null, due_at: '2026-11-17T23:59:00+07:00' })]),
    );
    expect(timed).toMatchObject({ start: '2026-11-17T17:00:00+07:00', allDay: false });
    expect(dateOnly).toMatchObject({ start: '2026-11-17', allDay: true });
    expect(timed.backgroundColor).toBe(colorHex('c02'));
  });

  it('nhãn thứ 2 trở đi thành chấm màu; task đã xong có class is-done', () => {
    const [e] = toCalendarEvents(
      data([], [task({ completed: true, tags: [tag(1, 'c07'), tag(2, 'c04'), tag(3, 'c09')] })]),
    );
    expect(e.classNames).toEqual(['is-done']);
    expect(e.extendedProps?.extraTagColors).toEqual([colorHex('c04'), colorHex('c09')]);
  });
});

describe('bộ lọc nhãn trong URL', () => {
  it('đọc và ghi tham số tags', () => {
    expect(parseTagParam('1,2,x,-3')).toEqual([1, 2]);
    expect(parseTagParam(null)).toEqual([]);
    expect(formatTagParam([3, 1])).toBe('3,1');
    expect(formatTagParam([])).toBeNull();
  });

  it('bật/tắt một nhãn, giữ thứ tự chọn', () => {
    expect(toggleTag([1], 2)).toEqual([1, 2]);
    expect(toggleTag([1, 2], 1)).toEqual([2]);
  });
});

describe('dãy ca', () => {
  it('liệt kê ca đơn và dãy ca liền nhau', () => {
    const shifts = [
      { id: 2, name: 'Ca 2', start_time: '09:35', end_time: '12:10', position: 2 },
      { id: 1, name: 'Ca 1', start_time: '06:45', end_time: '09:25', position: 1 },
    ];
    expect(shiftRanges(shifts).map((r) => [r.label, r.start_time, r.end_time])).toEqual([
      ['Ca 1', '06:45', '09:25'],
      ['Ca 1–2', '06:45', '12:10'],
      ['Ca 2', '09:35', '12:10'],
    ]);
  });
});
