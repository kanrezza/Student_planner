import type { EventInput } from '@fullcalendar/core';
import type { CalendarData } from '../api/types';
import { colorHex } from './colors';

export type CalendarEventProps = {
  kind: 'session' | 'task';
  id: number;
  /** Màu của các nhãn thứ 2 trở đi, hiện thành chấm nhỏ (FR-044). */
  extraTagColors: string[];
};

/**
 * Ánh xạ dữ liệu API sang sự kiện của FullCalendar (FR-017):
 * - Buổi học: có giờ; buổi đã huỷ có class `is-cancelled`.
 * - Task có giờ: sự kiện có giờ; task chỉ có ngày: sự kiện cả ngày; task đã xong có class `is-done`.
 * - Màu = `display_color` (màu nhãn đầu tiên, hoặc màu môn/danh sách).
 */
export function toCalendarEvents(data: CalendarData): EventInput[] {
  const sessions: EventInput[] = data.sessions.map((s) => ({
    id: `session-${s.id}`,
    title: s.room ? `${s.subject_name} · ${s.room}` : s.subject_name,
    start: s.start_at,
    end: s.end_at,
    allDay: false,
    backgroundColor: colorHex(s.display_color),
    borderColor: colorHex(s.display_color),
    textColor: '#ffffff',
    classNames: s.is_cancelled ? ['is-cancelled'] : [],
    extendedProps: {
      kind: 'session',
      id: s.id,
      extraTagColors: s.tags.slice(1).map((tag) => colorHex(tag.color)),
    } satisfies CalendarEventProps,
  }));
  const tasks: EventInput[] = data.tasks.map((task) => ({
    id: `task-${task.id}`,
    title: task.title,
    start: task.due_time ? (task.due_at ?? undefined) : (task.due_date ?? undefined),
    allDay: !task.due_time,
    backgroundColor: colorHex(task.display_color),
    borderColor: colorHex(task.display_color),
    textColor: '#ffffff',
    classNames: task.completed ? ['is-done'] : [],
    extendedProps: {
      kind: 'task',
      id: task.id,
      extraTagColors: task.tags.slice(1).map((tag) => colorHex(tag.color)),
    } satisfies CalendarEventProps,
  }));
  return [...sessions, ...tasks];
}
