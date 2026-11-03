import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateAll, keys } from './keys';
import type { Shift } from './types';

export type ShiftInput = { name?: string; start_time?: string; end_time?: string };

export function useShifts() {
  return useQuery({
    queryKey: keys.shifts,
    queryFn: async () => (await apiFetch<Shift[]>('/shifts')).data,
    staleTime: 5 * 60_000,
  });
}

export function useSaveShift() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input, confirm }: { id?: number; input: ShiftInput; confirm?: boolean }) =>
      id
        ? apiFetch<Shift>(`/shifts/${id}${confirm ? '?confirm=true' : ''}`, {
            method: 'PATCH',
            body: input,
          })
        : apiFetch<Shift>('/shifts', { method: 'POST', body: input }),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDeleteShift() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, confirm }: { id: number; confirm?: boolean }) =>
      apiFetch(`/shifts/${id}${confirm ? '?confirm=true' : ''}`, { method: 'DELETE' }),
    onSuccess: () => invalidateAll(qc),
  });
}
