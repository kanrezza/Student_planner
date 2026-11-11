import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type CanonicalName = {
  id: number;
  name: string;
  course_code: string | null;
  created_at: string;
};

const KEY = ['canonical-names'] as const;

export function useCanonicalNames() {
  return useQuery({
    queryKey: KEY,
    queryFn: async () => (await apiFetch<CanonicalName[]>('/canonical-names')).data,
  });
}

export function useClearCanonicalNames() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch('/canonical-names', { method: 'DELETE' }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: KEY }),
  });
}
