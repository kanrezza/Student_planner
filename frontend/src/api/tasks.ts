import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ApiError, apiFetch, type ApiWarning } from './client';
import { invalidateTaskViews, keys } from './keys';
import type { Task, TaskCounts, TaskInput, TaskTransition } from './types';

/** Phạm vi áp dụng khi sửa/xoá task lặp (FR-020). */
export type Scope = 'this' | 'following';

/** API đòi chọn phạm vi (409 `scope_required`) → giao diện hỏi rồi gửi lại. */
export const isScopeRequired = (err: unknown): boolean =>
  err instanceof ApiError && err.code === 'scope_required';

/** Danh sách thông minh (feature 002 FR-009). */
export type SmartView = 'today' | 'tomorrow' | 'next7' | 'all' | 'completed' | 'trash';

/** View đang xem trong mục Công việc: danh sách thông minh, danh sách người dùng hoặc nhãn. */
export type TaskView =
  { kind: 'smart'; view: SmartView } | { kind: 'list'; id: number } | { kind: 'tag'; id: number };

export function viewQuery(view: TaskView): string {
  if (view.kind === 'list') return `list_id=${view.id}`;
  if (view.kind === 'tag') return `tag_id=${view.id}`;
  return `view=${view.view}`;
}

export const viewKey = (view: TaskView) => [...keys.tasks, 'view', viewQuery(view)] as const;

export function useSmartTasks(view: TaskView) {
  return useQuery({
    queryKey: viewKey(view),
    queryFn: async () => (await apiFetch<Task[]>(`/tasks?${viewQuery(view)}`)).data,
  });
}

export function useTaskCounts() {
  return useQuery({
    queryKey: keys.taskCounts,
    queryFn: async () => (await apiFetch<TaskCounts>('/task-counts')).data,
  });
}

export function useTask(id: number | null) {
  return useQuery({
    queryKey: [...keys.tasks, 'one', id],
    queryFn: async () => (await apiFetch<Task>(`/tasks/${id}`)).data,
    enabled: id !== null,
    retry: false,
  });
}

/** POST/PATCH trả task, hoặc `{task, warnings}` khi có cảnh báo (ví dụ `work_after_due`). */
export type TaskResult = { task: Task; warnings: ApiWarning[] };

export function toTaskResult(data: Task | { task: Task; warnings?: ApiWarning[] }): TaskResult {
  return 'task' in data && typeof data.task === 'object'
    ? { task: data.task, warnings: data.warnings ?? [] }
    : { task: data as Task, warnings: [] };
}

type TaskResponse = Task | { task: Task; warnings: ApiWarning[] };

function useTaskMutation<V, R>(request: (vars: V) => Promise<R>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: request, onSettled: () => invalidateTaskViews(qc) });
}

export const useCreateTask = () =>
  useTaskMutation(async (input: TaskInput) =>
    toTaskResult((await apiFetch<TaskResponse>('/tasks', { method: 'POST', body: input })).data),
  );

export const useUpdateTask = () =>
  useTaskMutation(
    async ({ id, input, scope }: { id: number; input: Partial<TaskInput>; scope?: Scope }) =>
      toTaskResult(
        (
          await apiFetch<TaskResponse>(`/tasks/${id}`, {
            method: 'PATCH',
            body: scope ? { ...input, scope } : input,
          })
        ).data,
      ),
  );

export const useCompleteTask = () =>
  useTaskMutation(({ id, completed }: { id: number; completed: boolean }) =>
    apiFetch<TaskTransition>(`/tasks/${id}/${completed ? 'complete' : 'uncomplete'}`, {
      method: 'POST',
    }),
  );

/** Chuyển vào Thùng rác (FR-030); trả task để có thể Hoàn tác. */
export const useTrashTask = () =>
  useTaskMutation(
    async ({ id, scope }: { id: number; scope?: Scope }) =>
      (
        await apiFetch<TaskTransition>(`/tasks/${id}${scope ? `?scope=${scope}` : ''}`, {
          method: 'DELETE',
        })
      ).data,
  );

export const useRestoreTask = () =>
  useTaskMutation(
    async (id: number) =>
      (await apiFetch<TaskResult>(`/tasks/${id}/restore`, { method: 'POST' })).data,
  );

export const useDeletePermanently = () =>
  useTaskMutation((id: number) => apiFetch(`/tasks/${id}?permanent=true`, { method: 'DELETE' }));

export const useEmptyTrash = () =>
  useTaskMutation(
    async () => (await apiFetch<{ deleted: number }>('/trash', { method: 'DELETE' })).data,
  );
