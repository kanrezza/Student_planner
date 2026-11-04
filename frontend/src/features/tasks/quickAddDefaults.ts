/**
 * Giá trị mặc định khi thêm nhanh theo view đang xem (feature 002 FR-017; data-model
 * "Giá trị mặc định khi thêm nhanh"). Ô thêm nhanh không có ở Đã hoàn thành và Thùng rác.
 */
import type { TaskView } from '../../api/tasks';
import type { TaskInput } from '../../api/types';
import { addDays } from '../../lib/dates';

export type QuickAddDefaults = Pick<TaskInput, 'due_date' | 'list_id' | 'tag_ids'>;

/** View có ô thêm nhanh. */
export function hasQuickAdd(view: TaskView): boolean {
  return !(view.kind === 'smart' && (view.view === 'completed' || view.view === 'trash'));
}

export function quickAddDefaults(
  view: TaskView,
  today: string,
  studyListId: number,
): QuickAddDefaults {
  if (view.kind === 'list') return { due_date: null, list_id: view.id, tag_ids: [] };
  if (view.kind === 'tag') return { due_date: null, list_id: studyListId, tag_ids: [view.id] };
  const due = { today, tomorrow: addDays(today, 1), next7: today }[
    view.view as 'today' | 'tomorrow' | 'next7'
  ];
  return { due_date: due ?? null, list_id: studyListId, tag_ids: [] };
}

/** Payload đầy đủ cho POST /tasks: ưu tiên Trung bình, không Quan trọng, nhắc theo mặc định. */
export function quickAddInput(title: string, defaults: QuickAddDefaults): TaskInput {
  return {
    title: title.trim(),
    notes: null,
    due_time: null,
    priority: 2,
    is_important: false,
    reminder_minutes: null,
    ...defaults,
  };
}
