/** Chuỗi hiển thị của một dòng task (feature 002 FR-011). Hàm thuần. */
import type { Task } from '../../api/types';
import { t } from '../../i18n/vi';
import { addDays, formatDate, formatDayMonth, isoWeekday } from '../../lib/dates';

/** Giờ hạn (hôm nay/ngày mai) hoặc ngày hạn (xa hơn), canh phải trên dòng task. */
export function dueLabel(task: Pick<Task, 'due_date' | 'due_time'>, today: string): string {
  const { due_date: date, due_time: time } = task;
  if (!date) return '';
  const withTime = (text: string) => (time ? `${text} ${time}` : text);
  if (date === today) return time ?? t('groups.today');
  if (date === addDays(today, 1)) return withTime(t('groups.tomorrow'));
  if (date === addDays(today, -1)) return withTime(t('groups.yesterday'));
  const sameYear = date.slice(0, 4) === today.slice(0, 4);
  return withTime(sameYear ? formatDayMonth(date) : formatDate(date));
}

/** "T5 19:00–21:00" */
export function workLabel(task: Pick<Task, 'work_date' | 'work_start' | 'work_end'>): string {
  if (!task.work_date || !task.work_start || !task.work_end) return '';
  const day = t(`weekdaysShort.${isoWeekday(task.work_date)}`);
  return `${day} ${task.work_start}–${task.work_end}`;
}
