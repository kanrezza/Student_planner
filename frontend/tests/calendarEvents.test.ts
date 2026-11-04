import { describe, expect, it } from 'vitest';
import type { CalendarData, CalendarExam, ClassSession, Task } from '../src/api/types';
import {
  toCalendarEvents,
  type CalendarEventProps,
} from '../src/features/calendar/toCalendarEvents';
import { colorHex, colorSoft, colorStrong } from '../src/lib/colors';
import { shiftRanges } from '../src/lib/shifts';
import { formatTagParam, parseTagParam, toggleTag } from '../src/lib/tagFilter';
import { makeTask } from './fixtures';

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
  is_important: false,
  important_override: null,
  subject_is_important: false,
  ...over,
});

const task = (over: Partial<Task> = {}): Task =>
  makeTask({
    id: 5,
    title: 'Nộp bài',
    due_date: '2026-11-17',
    due_time: '17:00',
    due_at: '2026-11-17T17:00:00+07:00',
    display_color: 'c02',
    ...over,
  });

/** Buổi thi giả (dạng API trả về). */
const exam = (over: Partial<CalendarExam> = {}): CalendarExam => ({
  id: 3,
  course_code: null,
  course_name: 'Cơ sở dữ liệu',
  attempt: 1,
  date: '2026-11-18',
  start_at: '2026-11-18T07:30:00+07:00',
  end_at: '2026-11-18T08:30:00+07:00',
  exam_format: null,
  room: 'A5-310',
  candidate_number: null,
  is_past: false,
  display_color: 'c07',
  is_important: true,
  reminder_offsets: null,
  conflicts: [],
  tags: [],
  ...over,
});

const data = (sessions: ClassSession[], tasks: Task[], exams?: CalendarExam[]): CalendarData => ({
  sessions,
  tasks,
  ...(exams ? { exams } : {}),
});

const props = (e: { extendedProps?: unknown }) => e.extendedProps as CalendarEventProps;

describe('toCalendarEvents — khối trên lịch (data-model)', () => {
  it('task có khung giờ làm → khối khung giờ làm, kéo và kéo dãn được', () => {
    const [e] = toCalendarEvents(
      data(
        [],
        [
          task({
            work_date: '2026-11-19',
            work_start: '14:00',
            work_end: '16:00',
            due_date: '2026-11-20',
            due_time: '23:59',
            due_at: '2026-11-20T23:59:00+07:00',
          }),
        ],
      ),
    );
    expect(e).toMatchObject({
      id: 'task-5',
      title: 'Nộp bài',
      start: '2026-11-19T14:00:00+07:00',
      end: '2026-11-19T16:00:00+07:00',
      allDay: false,
      startEditable: true,
      durationEditable: true,
    });
    expect(props(e).deadline).toBe(false);
  });

  it('chỉ có giờ hạn → khối 30 phút từ due_at, cờ deadline, không kéo dãn', () => {
    const [e] = toCalendarEvents(data([], [task()]));
    expect(e.allDay).toBe(false);
    expect(new Date(e.start as string).getTime()).toBe(
      new Date('2026-11-17T17:00:00+07:00').getTime(),
    );
    expect(new Date(e.end as string).getTime()).toBe(
      new Date('2026-11-17T17:30:00+07:00').getTime(),
    );
    expect(props(e).deadline).toBe(true);
    expect(e).toMatchObject({ startEditable: true, durationEditable: false });
  });

  it('chỉ có ngày hạn → hàng Cả ngày', () => {
    const [e] = toCalendarEvents(
      data([], [task({ due_time: null, due_at: '2026-11-17T23:59:00+07:00' })]),
    );
    expect(e).toMatchObject({ start: '2026-11-17', allDay: true, durationEditable: false });
    expect(props(e).deadline).toBe(false);
  });

  it('task không có hạn và khung giờ làm thì không hiện', () => {
    expect(
      toCalendarEvents(data([], [task({ due_date: null, due_time: null, due_at: null })])),
    ).toEqual([]);
  });

  it('task đã xong: class mờ, không kéo được', () => {
    const [e] = toCalendarEvents(data([], [task({ completed: true })]));
    expect(e.classNames).toContain('is-done');
    expect(e).toMatchObject({ startEditable: false, durationEditable: false });
    expect(props(e).done).toBe(true);
  });

  it('buổi học: có phòng, kéo được (chưa huỷ), không kéo dãn', () => {
    const [e] = toCalendarEvents(data([session()], []));
    expect(e).toMatchObject({
      id: 'session-1',
      title: 'Giải tích 1',
      start: '2026-11-16T06:45:00+07:00',
      end: '2026-11-16T09:25:00+07:00',
      allDay: false,
      startEditable: true,
      durationEditable: false,
    });
    expect(props(e)).toMatchObject({ kind: 'session', id: 1, room: 'A2-301', cancelled: false });
  });

  it('buổi huỷ: class mờ, không kéo được; buổi đã dời có cờ moved', () => {
    const [cancelled, moved] = toCalendarEvents(
      data(
        [
          session({ is_cancelled: true }),
          session({ id: 2, is_moved: true, original_date: '2026-11-13' }),
        ],
        [],
      ),
    );
    expect(cancelled.classNames).toContain('is-cancelled');
    expect(cancelled.startEditable).toBe(false);
    expect(props(moved).moved).toBe(true);
    expect(props(moved).originalDate).toBe('2026-11-13');
  });

  it('buổi thi: class nổi bật, nền đậm, không kéo, không kéo dãn', () => {
    const [e] = toCalendarEvents(data([], [], [exam()]));
    expect(e.classNames).toContain('is-exam');
    expect(e).toMatchObject({
      id: 'exam-3',
      title: 'Cơ sở dữ liệu',
      startEditable: false,
      durationEditable: false,
      backgroundColor: colorHex('c07'),
      textColor: '#ffffff',
    });
    expect(props(e)).toMatchObject({ kind: 'exam', room: 'A5-310', important: true });
  });

  it('màu nền colorSoft, chữ colorStrong theo chế độ sáng/tối', () => {
    const [light] = toCalendarEvents(data([session()], []), 'light');
    expect(light.backgroundColor).toBe(colorSoft('c01', 'light'));
    expect(light.textColor).toBe(colorStrong('c01', 'light'));
    expect(light.borderColor).toBe(colorHex('c01'));
    const [dark] = toCalendarEvents(data([session()], []), 'dark');
    expect(dark.backgroundColor).toBe(colorSoft('c01', 'dark'));
    expect(dark.textColor).toBe(colorStrong('c01', 'dark'));
  });

  it('mục quan trọng có cờ important và class is-important; nhãn thứ 2 trở đi thành chấm màu', () => {
    const [e] = toCalendarEvents(
      data([], [task({ is_important: true, tags: [tag(1, 'c07'), tag(2, 'c04'), tag(3, 'c09')] })]),
    );
    expect(e.title).toBe('Nộp bài');
    expect(e.classNames).toContain('is-important');
    expect(props(e).important).toBe(true);
    expect(props(e).extraTagColors).toEqual([colorHex('c04'), colorHex('c09')]);
  });
});

describe('bộ lọc nhãn trong URL', () => {
  it('đọc và ghi tham số', () => {
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
