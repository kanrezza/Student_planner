import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';
import { keys } from './keys';
import type { TodayData } from './types';

export function useToday() {
  return useQuery({
    queryKey: keys.today,
    queryFn: async () => (await apiFetch<TodayData>('/today')).data,
    refetchInterval: 5 * 60_000, // qua nửa đêm thì trang tự chuyển sang ngày mới
  });
}
