/**
 * Giá trị mặc định khi thêm nhanh theo view đang xem (feature 002 FR-017; data-model
 * "Giá trị mặc định khi thêm nhanh"). Ô thêm nhanh không có ở Đã hoàn thành và Thùng rác.
 */
import type { TaskView } from '../../api/tasks';
import type { TaskInput } from '../../api/types';
import { addDays } from '../../lib/dates';
import type { QuickFields } from './quickParse';

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

/**
 * Payload đầy đủ cho POST /tasks: ưu tiên Trung bình, không Quan trọng, nhắc theo mặc định.
 * Giá trị hiểu được từ câu (`parsed`) được ưu tiên hơn mặc định của danh sách đang xem; nhãn hiểu được
 * cộng thêm vào nhãn mặc định (feature 003 FR-033).
 */
export function quickAddInput(
  title: string,
  defaults: QuickAddDefaults,
  parsed?: QuickFields,
): TaskInput {
  const input: TaskInput = {
    title: title.trim(),
    notes: null,
    due_time: parsed?.due_time ?? null,
    priority: parsed?.priority ?? 2,
    is_important: parsed?.is_important ?? false,
    reminder_minutes: null,
    ...defaults,
    due_date: parsed?.due_date ?? defaults.due_date,
    list_id: parsed?.list_id ?? defaults.list_id,
    tag_ids: [...new Set([...(defaults.tag_ids ?? []), ...(parsed?.tag_ids ?? [])])],
  };
  if (parsed?.tag_names.length) input.tag_names = parsed.tag_names;
  if (parsed?.recurrence) input.recurrence = parsed.recurrence;
  return input;
}
