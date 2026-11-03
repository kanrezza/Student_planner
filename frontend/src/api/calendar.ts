import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';
import { keys } from './keys';
import type { CalendarData } from './types';

/** Buổi học và task trong khoảng ngày [from, to], lọc theo nhãn nếu có (FR-016, FR-045). */
export function useCalendar(range: { from: string; to: string } | null, tagIds: number[]) {
  return useQuery({
    queryKey: [...keys.calendar, range?.from, range?.to, tagIds.join(',')],
    queryFn: async () => {
      const params = new URLSearchParams({ from: range!.from, to: range!.to });
      if (tagIds.length) params.set('tags', tagIds.join(','));
      return (await apiFetch<CalendarData>(`/calendar?${params}`)).data;
    },
    enabled: range !== null,
    placeholderData: keepPreviousData, // giữ dữ liệu cũ khi chuyển tuần/tháng để không nhấp nháy
  });
}
