import type { EventInput } from '@fullcalendar/core';
import type {
  CalendarData,
  CalendarExam,
  ClassSession,
  ProjectedTask,
  Task,
} from '../../api/types';
import { colorHex, colorSoft, colorStrong, type ColorScheme } from '../../lib/colors';

export type CalendarItemKind = 'session' | 'task' | 'exam' | 'projected';

/** Dữ liệu `CalendarBlock` cần để vẽ khối (FR-023). */
export type CalendarEventProps = {
  kind: CalendarItemKind;
  id: number;
  important: boolean;
  /** Khối 30 phút tại giờ hạn của task không có khung giờ làm (FR-022). */
  deadline: boolean;
  done: boolean;
  cancelled: boolean;
  moved: boolean;
  /** Ngày gốc của buổi đã dời ("YYYY-MM-DD"), để ghi "Đã dời (từ T2 16/11)". */
  originalDate: string | null;
  room: string | null;
  priority: number;
  /** Màu của các nhãn thứ 2 trở đi, hiện thành chấm nhỏ. */
  extraTagColors: string[];
};

const DEADLINE_MINUTES = 30;

/**
 * Ánh xạ dữ liệu API sang sự kiện FullCalendar theo bảng "Khối trên lịch" của data-model
 * (FR-022, FR-023): vị trí, cờ kéo/kéo dãn, màu nền nhạt + chữ đậm theo chế độ sáng/tối.
 */
export function toCalendarEvents(data: CalendarData, scheme: ColorScheme = 'light'): EventInput[] {
  return [
    ...data.sessions.map((s) => sessionEvent(s, scheme)),
    ...data.tasks.flatMap((t) => taskEvent(t, scheme) ?? []),
    ...(data.exams ?? []).map(examEvent),
    ...(data.projected_tasks ?? []).map((p) => projectedEvent(p, scheme)),
  ];
}

function softColors(code: string, scheme: ColorScheme) {
  return {
    backgroundColor: colorSoft(code, scheme),
    borderColor: colorHex(code),
    textColor: colorStrong(code, scheme),
  };
}

const extraColors = (tags: { color: string }[]) => tags.slice(1).map((tag) => colorHex(tag.color));

function baseProps(kind: CalendarItemKind, id: number): CalendarEventProps {
  return {
    kind,
    id,
    important: false,
    deadline: false,
    done: false,
    cancelled: false,
    moved: false,
    originalDate: null,
    room: null,
    priority: 2,
    extraTagColors: [],
  };
}

function sessionEvent(s: ClassSession, scheme: ColorScheme): EventInput {
  return {
    id: `session-${s.id}`,
    title: s.subject_name,
    start: s.start_at,
    end: s.end_at,
    allDay: false,
    startEditable: !s.is_cancelled,
    durationEditable: false,
    ...softColors(s.display_color, scheme),
    classNames: classes({ 'is-cancelled': s.is_cancelled, 'is-important': s.is_important }),
    extendedProps: {
      ...baseProps('session', s.id),
      important: s.is_important,
      cancelled: s.is_cancelled,
      moved: Boolean(s.is_moved),
      originalDate: s.original_date ?? null,
      room: s.room,
      extraTagColors: extraColors(s.tags),
    } satisfies CalendarEventProps,
  };
}

function taskEvent(task: Task, scheme: ColorScheme): EventInput | null {
  const open = !task.completed;
  const props: CalendarEventProps = {
    ...baseProps('task', task.id),
    important: task.is_important,
    done: task.completed,
    priority: task.priority,
    extraTagColors: extraColors(task.tags),
  };
  const common = {
    id: `task-${task.id}`,
    title: task.title,
    ...softColors(task.display_color, scheme),
    classNames: classes({ 'is-done': task.completed, 'is-important': task.is_important }),
  };

  if (task.work_date && task.work_start && task.work_end) {
    return {
      ...common,
      start: `${task.work_date}T${task.work_start}:00+07:00`,
      end: `${task.work_date}T${task.work_end}:00+07:00`,
      allDay: false,
      startEditable: open,
      durationEditable: open,
      extendedProps: props,
    };
  }
  if (task.due_date && task.due_time && task.due_at) {
    const end = new Date(new Date(task.due_at).getTime() + DEADLINE_MINUTES * 60_000);
    return {
      ...common,
      start: task.due_at,
      end: end.toISOString(),
      allDay: false,
      startEditable: open,
      durationEditable: false,
      classNames: [...common.classNames, 'is-deadline'],
      extendedProps: { ...props, deadline: true },
    };
  }
  if (task.due_date) {
    return {
      ...common,
      start: task.due_date,
      allDay: true,
      startEditable: open,
      durationEditable: false,
      extendedProps: props,
    };
  }
  return null;
}

/**
 * Lần dự kiến của task lặp (FR-022): khối mờ, viền nét đứt (CSS `is-projected`), không kéo được;
 * bấm mở lần hiện tại nên `id` là id của lần hiện tại.
 */
function projectedEvent(p: ProjectedTask, scheme: ColorScheme): EventInput {
  const common = {
    id: `projected-${p.series_id}-${p.date}`,
    title: p.title,
    ...softColors(p.color, scheme),
    startEditable: false,
    durationEditable: false,
    classNames: ['is-projected'],
  };
  const props = { ...baseProps('projected', p.current_task_id), deadline: p.time !== null };
  if (!p.time) return { ...common, start: p.date, allDay: true, extendedProps: props };
  const start = `${p.date}T${p.time}:00+07:00`;
  const end = new Date(new Date(start).getTime() + DEADLINE_MINUTES * 60_000).toISOString();
  return { ...common, start, end, allDay: false, extendedProps: props };
}

/** Buổi thi nổi bật hẳn: nền màu đậm, chữ trắng, viền rõ (FR-023); không kéo được. */
function examEvent(exam: CalendarExam): EventInput {
  return {
    id: `exam-${exam.id}`,
    title: exam.course_name,
    start: exam.start_at,
    end: exam.end_at,
    allDay: false,
    startEditable: false,
    durationEditable: false,
    backgroundColor: colorHex(exam.display_color),
    borderColor: colorStrong(exam.display_color, 'light'),
    textColor: '#ffffff',
    classNames: classes({ 'is-exam': true, 'is-important': exam.is_important }),
    extendedProps: {
      ...baseProps('exam', exam.id),
      important: exam.is_important,
      room: exam.room,
      extraTagColors: extraColors(exam.tags),
    } satisfies CalendarEventProps,
  };
}

function classes(flags: Record<string, boolean>): string[] {
  return Object.entries(flags)
    .filter(([, on]) => on)
    .map(([name]) => name);
}
