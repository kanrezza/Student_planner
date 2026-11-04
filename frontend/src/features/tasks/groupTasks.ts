/**
 * Nhóm task trong khu vực chính (feature 002 FR-010; data-model "Nhóm task trong khu vực chính").
 * Hàm thuần: chỉ phụ thuộc danh sách task và thời điểm `now`, nên tự đổi nhóm khi sang ngày mới.
 */
import type { Task } from '../../api/types';
import { t } from '../../i18n/vi';
import { addDays, daysBetween, formatDayShort, toIsoDate } from '../../lib/dates';

export type TaskGroup = {
  key: string;
  title: string;
  tasks: Task[];
  tone?: 'danger';
};

export function isOverdue(task: Task, now: Date): boolean {
  return !task.completed && task.due_at !== null && new Date(task.due_at).getTime() < now.getTime();
}

/** Ngày sớm nhất (từ hôm nay trở đi) trong hạn chót và khung giờ làm; null nếu không có. */
export function referenceDate(task: Task, today: string): string | null {
  const dates = [task.due_date, task.work_date].filter((d): d is string => d !== null).sort();
  if (dates.length === 0) return null;
  return dates.find((d) => d >= today) ?? dates[0];
}

/** Giờ dùng để sắp xếp trong ngày `day`: giờ bắt đầu khung giờ làm hoặc giờ hạn. */
function timeOn(task: Task, day: string | null): string | null {
  if (task.work_date !== null && task.work_date === day) return task.work_start;
  if (task.due_date === day) return task.due_time;
  return null;
}

function byTimeThenPriority(day: (task: Task) => string | null) {
  return (a: Task, b: Task) => {
    const da = day(a) ?? '';
    const db = day(b) ?? '';
    if (da !== db) return da < db ? -1 : 1;
    const ta = timeOn(a, day(a));
    const tb = timeOn(b, day(b));
    if (ta !== tb) {
      if (ta === null) return 1; // không có giờ ở cuối
      if (tb === null) return -1;
      return ta < tb ? -1 : 1;
    }
    return a.priority - b.priority || a.id - b.id;
  };
}

export function groupTasks(tasks: Task[], now: Date): TaskGroup[] {
  const today = toIsoDate(now);
  const overdue: Task[] = [];
  const byKey = new Map<string, Task[]>();
  const push = (key: string, task: Task) => byKey.set(key, [...(byKey.get(key) ?? []), task]);

  for (const task of tasks) {
    if (isOverdue(task, now)) {
      overdue.push(task);
      continue;
    }
    const ref = referenceDate(task, today);
    if (ref === null) {
      push('none', task);
      continue;
    }
    const offset = daysBetween(today, ref);
    if (offset <= 0) push('today', task);
    else if (offset === 1) push('tomorrow', task);
    else if (offset <= 6) push(`day:${ref}`, task);
    else push('later', task);
  }

  const refOf = (task: Task) => referenceDate(task, today);
  const groups: TaskGroup[] = [];
  if (overdue.length) {
    overdue.sort((a, b) => (a.due_at ?? '').localeCompare(b.due_at ?? '') || a.id - b.id);
    groups.push({ key: 'overdue', title: t('groups.overdue'), tasks: overdue, tone: 'danger' });
  }
  const ordered: [string, string][] = [
    ['today', t('groups.today')],
    ['tomorrow', t('groups.tomorrow')],
    ...[2, 3, 4, 5, 6].map((n): [string, string] => {
      const day = addDays(today, n);
      return [`day:${day}`, formatDayShort(day)];
    }),
    ['later', t('groups.later')],
  ];
  for (const [key, title] of ordered) {
    const items = byKey.get(key);
    if (items) groups.push({ key, title, tasks: items.sort(byTimeThenPriority(refOf)) });
  }
  const none = byKey.get('none');
  if (none) {
    none.sort((a, b) => a.priority - b.priority || a.id - b.id);
    groups.push({ key: 'none', title: t('groups.none'), tasks: none });
  }
  return groups;
}

/** Đã hoàn thành: nhóm theo ngày hoàn thành, mới nhất trước (FR-014). */
export function groupCompleted(tasks: Task[], now: Date): TaskGroup[] {
  const today = toIsoDate(now);
  const sorted = [...tasks].sort((a, b) =>
    (b.completed_at ?? '').localeCompare(a.completed_at ?? ''),
  );
  const groups: TaskGroup[] = [];
  for (const task of sorted) {
    const day = task.completed_at ? toIsoDate(new Date(task.completed_at)) : today;
    const key = `done:${day}`;
    let group = groups.find((g) => g.key === key);
    if (!group) {
      const offset = daysBetween(day, today);
      const title =
        offset === 0
          ? t('groups.today')
          : offset === 1
            ? t('groups.yesterday')
            : formatDayShort(day);
      group = { key, title, tasks: [] };
      groups.push(group);
    }
    group.tasks.push(task);
  }
  return groups;
}
