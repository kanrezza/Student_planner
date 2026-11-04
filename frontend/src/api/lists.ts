import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateTaskViews, keys } from './keys';
import type { TaskList } from './types';

export function useLists() {
  return useQuery({
    queryKey: keys.lists,
    queryFn: async () => (await apiFetch<TaskList[]>('/lists')).data,
  });
}

/** `emoji: null` bỏ emoji; không gửi `emoji` thì giữ nguyên (feature 002 FR-015). */
export type ListInput = { id?: number; name: string; color?: string; emoji?: string | null };

export function useSaveList() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: ListInput) =>
      id
        ? apiFetch<TaskList>(`/lists/${id}`, { method: 'PATCH', body })
        : apiFetch<TaskList>('/lists', { method: 'POST', body }),
    onSuccess: () => invalidateTaskViews(qc),
  });
}

export type DeleteListOptions = { moveTo?: number; deleteTasks?: boolean };

export function useDeleteList() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, moveTo, deleteTasks }: { id: number } & DeleteListOptions) => {
      const params = new URLSearchParams();
      if (moveTo !== undefined) params.set('move_to', String(moveTo));
      if (deleteTasks) params.set('delete_tasks', 'true');
      return apiFetch(`/lists/${id}?${params}`, { method: 'DELETE' });
    },
    onSuccess: () => invalidateTaskViews(qc),
  });
}
