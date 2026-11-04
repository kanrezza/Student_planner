import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch, type ApiWarning } from './client';
import { invalidateScheduleViews } from './keys';
import type { ClassSession } from './types';

export type SessionPatch = {
  /** Dời buổi sang ngày khác (feature 002 FR-028). */
  date?: string;
  start_time?: string;
  end_time?: string;
  room?: string | null;
  important_override?: boolean | null;
};

/** PATCH /sessions/:id trả `{session, warnings}` (ví dụ `outside_semester`). */
export type SessionResult = { session: ClassSession; warnings: ApiWarning[] };

/** Sửa, huỷ, khôi phục, gắn nhãn một buổi học (US4, FR-011, FR-012, FR-043). */
export function useSessionActions() {
  const qc = useQueryClient();
  const onSuccess = () => invalidateScheduleViews(qc);
  const update = useMutation({
    mutationFn: async ({ id, patch }: { id: number; patch: SessionPatch }) =>
      (await apiFetch<SessionResult>(`/sessions/${id}`, { method: 'PATCH', body: patch })).data,
    onSuccess,
  });
  const setCancelled = useMutation({
    mutationFn: ({ id, cancelled }: { id: number; cancelled: boolean }) =>
      apiFetch<ClassSession>(`/sessions/${id}/${cancelled ? 'cancel' : 'restore'}`, {
        method: 'POST',
      }),
    onSuccess,
  });
  const setTags = useMutation({
    mutationFn: ({ id, tagIds }: { id: number; tagIds: number[] }) =>
      apiFetch<ClassSession>(`/sessions/${id}/tags`, { method: 'PUT', body: { tag_ids: tagIds } }),
    onSuccess,
  });
  return { update, setCancelled, setTags };
}
