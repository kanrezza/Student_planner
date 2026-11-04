/** Khung giờ làm (feature 002 FR-018): giá trị mặc định khi bật và kiểm tra phía giao diện. */
import type { Task } from '../../api/types';
import { t } from '../../i18n/vi';

export type WorkWindow = { work_date: string; work_start: string; work_end: string };

const toMinutes = (hhmm: string) => Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5));
const toHhmm = (minutes: number) =>
  `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`;

/** Bật khung giờ làm: ngày hạn (nếu chưa qua) hoặc hôm nay; giờ tròn kế tiếp, dài 1 giờ. */
export function defaultWorkWindow(
  task: Pick<Task, 'due_date'>,
  today: string,
  nowMinutes: number,
): WorkWindow {
  const date = task.due_date && task.due_date >= today ? task.due_date : today;
  const start = date === today ? Math.min(Math.ceil((nowMinutes + 1) / 60) * 60, 22 * 60) : 9 * 60;
  return { work_date: date, work_start: toHhmm(start), work_end: toHhmm(start + 60) };
}

/** Lỗi theo trường giống backend, để báo ngay dưới ô mà không cần gọi API. */
export function workWindowError(value: Partial<WorkWindow>): Record<string, string> | null {
  const { work_date, work_start, work_end } = value;
  if (!work_date || !work_start || !work_end) {
    return { work_date: 'Cần chọn đủ ngày, giờ bắt đầu và giờ kết thúc' };
  }
  if (toMinutes(work_end) <= toMinutes(work_start)) {
    return { work_end: 'Giờ kết thúc phải sau giờ bắt đầu' };
  }
  return null;
}

export function isWorkAfterDue(task: Pick<Task, 'work_date' | 'due_date'>): boolean {
  return Boolean(task.work_date && task.due_date && task.work_date > task.due_date);
}

export const workAfterDueMessage = () => t('detail.workAfterDue');
