import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateTaskViews, keys } from './keys';
import type { Task, TaskInput } from './types';

export function useTasks(listId: number | null, includeCompleted: boolean, tagIds: number[] = []) {
  const params = new URLSearchParams({ include_completed: String(includeCompleted) });
  if (listId !== null) params.set('list_id', String(listId));
  if (tagIds.length) params.set('tags', tagIds.join(','));
  return useQuery({
    queryKey: [...keys.tasks, listId, includeCompleted, tagIds.join(',')],
    queryFn: async () => (await apiFetch<Task[]>(`/tasks?${params}`)).data,
  });
}

function useTaskMutation<V>(request: (vars: V) => Promise<unknown>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: request, onSuccess: () => invalidateTaskViews(qc) });
}

export const useCreateTask = () =>
  useTaskMutation((input: TaskInput) => apiFetch<Task>('/tasks', { method: 'POST', body: input }));

export const useUpdateTask = () =>
  useTaskMutation(({ id, input }: { id: number; input: Partial<TaskInput> }) =>
    apiFetch<Task>(`/tasks/${id}`, { method: 'PATCH', body: input }),
  );

export const useCompleteTask = () =>
  useTaskMutation(({ id, completed }: { id: number; completed: boolean }) =>
    apiFetch<Task>(`/tasks/${id}/${completed ? 'complete' : 'uncomplete'}`, { method: 'POST' }),
  );

export const useDeleteTask = () =>
  useTaskMutation((id: number) => apiFetch(`/tasks/${id}`, { method: 'DELETE' }));
