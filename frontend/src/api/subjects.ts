import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateScheduleViews, keys } from './keys';
import type { Subject, SubjectInput } from './types';

export type SubjectSaveResult = { subject: Subject; session_count: number };
export type BulkResult = { subjects: Subject[]; session_count: number };

export function useSubjects(semesterId: number | null) {
  return useQuery({
    queryKey: [...keys.subjects, semesterId],
    queryFn: async () => (await apiFetch<Subject[]>(`/subjects?semester_id=${semesterId}`)).data,
    enabled: semesterId !== null,
  });
}

export type SubjectCreate = SubjectInput & {
  semester_id: number;
  start_date: string | null;
  end_date: string | null;
};

export function useSaveSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      input,
      confirm,
    }: {
      id?: number;
      input: Partial<SubjectCreate>;
      confirm?: boolean;
    }) =>
      id
        ? apiFetch<SubjectSaveResult>(`/subjects/${id}${confirm ? '?confirm=true' : ''}`, {
            method: 'PATCH',
            body: input,
          })
        : apiFetch<SubjectSaveResult>('/subjects', { method: 'POST', body: input }),
    onSuccess: () => invalidateScheduleViews(qc),
  });
}

export type BulkInput = {
  semester_id: number;
  start_date: string | null;
  end_date: string | null;
  rows: SubjectInput[];
};

export function useCreateBulk() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: BulkInput) =>
      apiFetch<BulkResult>('/subjects/bulk', { method: 'POST', body: input }),
    onSuccess: () => invalidateScheduleViews(qc),
  });
}

export function useDeleteSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, confirm }: { id: number; confirm?: boolean }) =>
      apiFetch(`/subjects/${id}${confirm ? '?confirm=true' : ''}`, { method: 'DELETE' }),
    onSuccess: () => invalidateScheduleViews(qc),
  });
}
