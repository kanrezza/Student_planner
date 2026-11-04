import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateScheduleViews, keys } from './keys';
import type { Exam, ExamInput } from './types';

export const examKeys = { all: ['exams'] as const };

/** Buổi thi sắp tới (kèm đã qua nếu `includePast`), sắp theo giờ bắt đầu. */
export function useExams(includePast: boolean) {
  return useQuery({
    queryKey: [...examKeys.all, includePast],
    queryFn: async () =>
      (await apiFetch<{ exams: Exam[] }>(`/exams?include_past=${includePast}`)).data.exams,
  });
}

/** Buổi thi thay đổi → danh sách buổi thi, trang Hôm nay, lịch. */
function useRefresh() {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: examKeys.all });
    invalidateScheduleViews(qc);
    void qc.invalidateQueries({ queryKey: keys.today });
  };
}

export function useSaveExam() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: ({ id, input }: { id?: number; input: Partial<ExamInput> }) =>
      id
        ? apiFetch<{ exam: Exam }>(`/exams/${id}`, { method: 'PATCH', body: input })
        : apiFetch<{ exam: Exam }>('/exams', { method: 'POST', body: input }),
    onSuccess: refresh,
  });
}

export function useDeleteExam() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (id: number) => apiFetch(`/exams/${id}`, { method: 'DELETE' }),
    onSuccess: refresh,
  });
}
