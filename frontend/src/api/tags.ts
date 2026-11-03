import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateAll, keys } from './keys';
import type { Tag } from './types';

export function useTags() {
  return useQuery({
    queryKey: keys.tags,
    queryFn: async () => (await apiFetch<Tag[]>('/tags')).data,
  });
}

export function useSaveTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name, color }: { id?: number; name?: string; color?: string }) =>
      id
        ? apiFetch<Tag>(`/tags/${id}`, { method: 'PATCH', body: { name, color } })
        : apiFetch<Tag>('/tags', { method: 'POST', body: { name, color } }),
    onSuccess: () => invalidateAll(qc), // đổi màu nhãn → màu trên lịch, danh sách đổi theo
  });
}

export function useDeleteTag() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch(`/tags/${id}`, { method: 'DELETE' }),
    onSuccess: () => invalidateAll(qc),
  });
}
