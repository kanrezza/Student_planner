import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateTaskViews, keys } from './keys';
import type { Task, TaskStatus } from './types';

export type BoardFilters = { list_ids: number[]; tag_ids: number[]; subject_ids: number[] };
export const NO_FILTERS: BoardFilters = { list_ids: [], tag_ids: [], subject_ids: [] };

export type BoardColumns = Record<TaskStatus, Task[]>;
export type BoardData = { columns: BoardColumns; done_hidden_count: number };
export type BoardUndo = { status: TaskStatus; before_id: number | null; after_id: number | null };
export type MoveInput = {
  id: number;
  status: TaskStatus;
  before_id: number | null;
  after_id: number | null;
};
export type MoveResult = { task: Task; next_task: Task | null; undo: BoardUndo };

export function boardKey(filters: BoardFilters, doneAll: boolean) {
  return [...keys.tasks, 'board', filters, doneAll ? 'all' : '7d'] as const;
}

function boardQuery(filters: BoardFilters, doneAll: boolean): string {
  const parts: string[] = [`done_window=${doneAll ? 'all' : '7d'}`];
  for (const key of ['list_ids', 'tag_ids', 'subject_ids'] as const) {
    if (filters[key].length) parts.push(`${key}=${filters[key].join(',')}`);
  }
  return parts.join('&');
}

export function useBoard(filters: BoardFilters, doneAll: boolean) {
  return useQuery({
    queryKey: boardKey(filters, doneAll),
    queryFn: async () =>
      (await apiFetch<BoardData>(`/tasks/board?${boardQuery(filters, doneAll)}`)).data,
  });
}

/** Chuyển thẻ; gọi `onMutate` bên ngoài để cập nhật lạc quan, lỗi thì giao diện tự hoàn lại. */
export function useMoveCard(qc?: QueryClient) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: MoveInput) =>
      apiFetch<MoveResult>(`/tasks/${id}/board`, { method: 'PATCH', body }),
    onSettled: () => invalidateTaskViews(qc ?? client),
  });
}
