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

export function useSaveList() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name, color }: { id?: number; name: string; color?: string }) =>
      id
        ? apiFetch<TaskList>(`/lists/${id}`, { method: 'PATCH', body: { name, color } })
        : apiFetch<TaskList>('/lists', { method: 'POST', body: { name, color } }),
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
