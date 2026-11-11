/** Hàm thuần của bảng Kanban: vị trí thẻ, cập nhật lạc quan, thẻ kề (feature 005). */
import type { BoardColumns } from '../../../api/board';
import type { Task, TaskStatus } from '../../../api/types';

export const STATUS_ORDER: TaskStatus[] = ['todo', 'doing', 'done'];

export const emptyColumns = (): BoardColumns => ({ todo: [], doing: [], done: [] });

export function locate(
  columns: BoardColumns,
  id: number,
): { status: TaskStatus; index: number } | null {
  for (const status of STATUS_ORDER) {
    const index = columns[status].findIndex((task) => task.id === id);
    if (index !== -1) return { status, index };
  }
  return null;
}

/**
 * Đặt thẻ `id` vào cột `to` tại vị trí `index` (tính sau khi đã nhấc thẻ khỏi chỗ cũ).
 * Thẻ sang Xong/rời Xong đổi `completed` và `status` để giao diện khớp ngay.
 */
export function applyMove(
  columns: BoardColumns,
  id: number,
  to: TaskStatus,
  index: number,
): BoardColumns {
  const from = locate(columns, id);
  if (!from) return columns;
  const card = columns[from.status][from.index];
  const next: BoardColumns = {
    todo: columns.todo.filter((t) => t.id !== id),
    doing: columns.doing.filter((t) => t.id !== id),
    done: columns.done.filter((t) => t.id !== id),
  };
  const moved: Task = {
    ...card,
    status: to,
    completed: to === 'done',
    completed_at: to === 'done' ? (card.completed_at ?? new Date().toISOString()) : null,
  };
  const target = [...next[to]];
  target.splice(Math.min(Math.max(index, 0), target.length), 0, moved);
  next[to] = target;
  return next;
}

/** Thẻ ngay trên và ngay dưới thẻ `id` trong cột của nó (gửi cho `PATCH /tasks/{id}/board`). */
export function neighbours(
  columns: BoardColumns,
  id: number,
): { before_id: number | null; after_id: number | null } {
  const at = locate(columns, id);
  if (!at) return { before_id: null, after_id: null };
  const column = columns[at.status];
  return {
    before_id: column[at.index - 1]?.id ?? null,
    after_id: column[at.index + 1]?.id ?? null,
  };
}

/** Cột dưới đích của một phím mũi tên: trả cột kề theo hướng, hoặc null khi ở mép. */
export function adjacentStatus(status: TaskStatus, step: 1 | -1): TaskStatus | null {
  return STATUS_ORDER[STATUS_ORDER.indexOf(status) + step] ?? null;
}
