import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateScheduleViews, keys } from './keys';
import type { Semester } from './types';

export type SemesterInput = { name: string; start_date: string; end_date: string };

export function useSemesters() {
  return useQuery({
    queryKey: keys.semesters,
    queryFn: async () => (await apiFetch<Semester[]>('/semesters')).data,
  });
}

export function useSaveSemester() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input, clamp }: { id?: number; input: SemesterInput; clamp?: boolean }) =>
      id
        ? apiFetch<Semester>(`/semesters/${id}${clamp ? '?clamp_subjects=true' : ''}`, {
            method: 'PATCH',
            body: input,
          })
        : apiFetch<Semester>('/semesters', { method: 'POST', body: input }),
    onSuccess: () => invalidateScheduleViews(qc),
  });
}

export function useDeleteSemester() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, confirm }: { id: number; confirm?: boolean }) =>
      apiFetch(`/semesters/${id}${confirm ? '?confirm=true' : ''}`, { method: 'DELETE' }),
    onSuccess: () => invalidateScheduleViews(qc),
  });
}
