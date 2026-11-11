import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { keys } from './keys';

export type Period = {
  number: number;
  start_time: string;
  end_time: string;
  is_manual: boolean;
  shift_id: number | null;
};

export function usePeriods() {
  return useQuery({
    queryKey: keys.periods,
    queryFn: async () => (await apiFetch<Period[]>('/periods')).data,
  });
}

function useRefresh() {
  const qc = useQueryClient();
  return () => void qc.invalidateQueries({ queryKey: keys.periods });
}

export function useSavePeriod() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: ({ number, start_time, end_time }: Omit<Period, 'is_manual' | 'shift_id'>) =>
      apiFetch<Period>(`/periods/${number}`, { method: 'PUT', body: { start_time, end_time } }),
    onSuccess: refresh,
  });
}

export function useResetPeriod() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (number: number) => apiFetch(`/periods/${number}/reset`, { method: 'POST' }),
    onSuccess: refresh,
  });
}

export function useDeletePeriod() {
  const refresh = useRefresh();
  return useMutation({
    mutationFn: (number: number) => apiFetch(`/periods/${number}`, { method: 'DELETE' }),
    onSuccess: refresh,
  });
}
