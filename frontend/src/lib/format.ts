import type { ClassSession, Priority, Task } from '../api/types';
import { t } from '../i18n/vi';
import { formatDayLong, formatTime } from './dates';

export const PRIORITIES: Priority[] = [1, 2, 3];

export function priorityLabel(p: Priority): string {
  return t(`priority.${p}`);
}

/** "Thứ Hai, 16/11/2026 17:00" hoặc "Thứ Hai, 16/11/2026" (task chỉ có ngày). */
export function formatDue(task: Pick<Task, 'due_date' | 'due_time'>): string {
  if (!task.due_date) return t('tasks.noDueDate');
  const day = formatDayLong(task.due_date);
  return task.due_time ? `${day} ${task.due_time}` : day;
}

/** "07:30 – 09:25" */
export function sessionTimeRange(session: Pick<ClassSession, 'start_at' | 'end_at'>): string {
  return `${formatTime(session.start_at)} – ${formatTime(session.end_at)}`;
}

/** [1, 4] → "T2, T5" */
export function weekdaysLabel(weekdays: number[]): string {
  return weekdays.map((d) => t(`weekdaysShort.${d}`)).join(', ');
}

/** Chuỗi rỗng → null (gửi API cho trường tuỳ chọn). */
export function blankToNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === '' ? null : trimmed;
}

/** Dung lượng dễ đọc, dấu phẩy thập phân kiểu Việt Nam: 2516582 → "2,4 MB". */
export function formatSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  const text = unit === 0 ? String(Math.round(value)) : value.toFixed(1).replace('.', ',');
  return `${text} ${units[unit]}`;
}

/** "21:00 Thứ Năm, 05/11/2026" */
export function formatMoment(iso: string): string {
  return `${formatTime(iso)} ${formatDayLong(iso)}`;
}
