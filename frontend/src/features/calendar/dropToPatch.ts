/**
 * Ánh xạ kéo thả trên lịch → PATCH task (feature 002 FR-026, data-model "Quy tắc kéo thả").
 * Hàm thuần: nhận giờ theo múi giờ máy (FullCalendar dùng `local`) và trả các trường cần gửi, hoặc
 * `null` khi không có gì đổi / không cho phép. Mọi thời điểm làm tròn 15 phút.
 */
import type { Task, TaskInput } from '../../api/types';

export type TaskPatch = Partial<
  Pick<TaskInput, 'due_date' | 'due_time' | 'work_date' | 'work_start' | 'work_end'>
>;

type DragTask = Pick<Task, 'due_date' | 'due_time' | 'work_date' | 'work_start' | 'work_end'>;

const STEP = 15;
const MIN_DURATION = 15;
const LAST_MINUTE = 24 * 60 - 1;

const pad = (n: number) => String(n).padStart(2, '0');
const toMinutes = (hhmm: string) => Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5));
const toHhmm = (minutes: number) => `${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`;
const isoDate = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const minutesOfDay = (d: Date) => d.getHours() * 60 + d.getMinutes();

/** "YYYY-MM-DD" theo giờ máy (FullCalendar dùng múi giờ `local`). */
export const localIsoDate = isoDate;
/** "HH:MM" theo giờ máy, đã làm tròn 15 phút. */
export const localHhmm = (d: Date) => toHhmm(minutesOfDay(roundTo15(d)));

/** Làm tròn tới bội số 15 phút gần nhất. */
export function roundTo15(d: Date): Date {
  const out = new Date(d);
  const rounded = Math.round((minutesOfDay(d) + d.getSeconds() / 60) / STEP) * STEP;
  out.setHours(0, rounded, 0, 0);
  return out;
}

const hasWorkWindow = (task: DragTask) =>
  Boolean(task.work_date && task.work_start && task.work_end);

/** Khung giờ làm bắt đầu tại `startMin`, dài `duration` phút, không tràn qua nửa đêm. */
function workWindow(date: string, startMin: number, duration: number): TaskPatch {
  const start = Math.min(startMin, LAST_MINUTE - MIN_DURATION);
  const end = Math.min(start + duration, LAST_MINUTE);
  return { work_date: date, work_start: toHhmm(start), work_end: toHhmm(end) };
}

/** Một thay đổi bằng chính trạng thái hiện tại thì coi như không có gì đổi. */
function nonEmpty(task: DragTask, patch: TaskPatch): TaskPatch | null {
  const changed = (Object.keys(patch) as (keyof TaskPatch)[]).some(
    (key) => (patch[key] ?? null) !== (task[key] ?? null),
  );
  return changed ? patch : null;
}

/** Thả khối task tại `start` (cột giờ hoặc hàng Cả ngày nếu `allDay`). */
export function dropToPatch(task: DragTask, start: Date, allDay: boolean): TaskPatch | null {
  const day = isoDate(start);
  if (hasWorkWindow(task)) {
    if (allDay) {
      return nonEmpty(task, { work_date: null, work_start: null, work_end: null, due_date: day });
    }
    const duration = toMinutes(task.work_end!) - toMinutes(task.work_start!);
    return nonEmpty(task, workWindow(day, minutesOfDay(roundTo15(start)), duration));
  }
  if (task.due_date && task.due_time) {
    if (allDay) return nonEmpty(task, { due_date: day, due_time: null });
    return nonEmpty(task, { due_date: day, due_time: toHhmm(minutesOfDay(roundTo15(start))) });
  }
  if (allDay) return nonEmpty(task, { due_date: day });
  return workWindow(day, minutesOfDay(roundTo15(start)), 60);
}

/**
 * Vùng chọn trên lưới → giá trị cho bảng tạo task mới (FR-027): khung giờ làm bằng vùng đã kéo (tối
 * thiểu 15 phút, không qua nửa đêm), hạn chót là ngày đó (không giờ). Chọn ở hàng Cả ngày thì chỉ
 * có hạn chót.
 */
export function selectionToNew(
  start: Date,
  end: Date,
  allDay: boolean,
): { due: string; work_date?: string; work_start?: string; work_end?: string } {
  const due = isoDate(start);
  if (allDay) return { due };
  const startMin = Math.min(minutesOfDay(roundTo15(start)), LAST_MINUTE - MIN_DURATION);
  const sameDay = isoDate(end) === due;
  const endMin = sameDay ? minutesOfDay(roundTo15(end)) : LAST_MINUTE;
  return {
    due,
    work_date: due,
    work_start: toHhmm(startMin),
    work_end: toHhmm(Math.min(Math.max(endMin, startMin + MIN_DURATION), LAST_MINUTE)),
  };
}

/** Kéo mép dưới khối có khung giờ làm: đổi giờ kết thúc, tối thiểu 15 phút sau giờ bắt đầu. */
export function resizeToPatch(task: DragTask, end: Date): TaskPatch | null {
  if (!hasWorkWindow(task)) return null;
  const startMin = toMinutes(task.work_start!);
  const endMin = Math.min(
    Math.max(minutesOfDay(roundTo15(end)) || LAST_MINUTE, startMin + MIN_DURATION),
    LAST_MINUTE,
  );
  return nonEmpty(task, { work_end: toHhmm(endMin) });
}

/** Hoàn tác: giá trị cũ của đúng các trường trong `patch`. */
export function undoPatch(task: DragTask, patch: TaskPatch): TaskPatch {
  const undo: Record<string, string | null> = {};
  for (const key of Object.keys(patch) as (keyof TaskPatch)[]) undo[key] = task[key] ?? null;
  return undo as TaskPatch;
}
