import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateScheduleViews } from './keys';
import type { ClassSession } from './types';

export type SessionPatch = {
  start_time?: string;
  end_time?: string;
  room?: string | null;
  important_override?: boolean | null;
};

/** Sửa, huỷ, khôi phục, gắn nhãn một buổi học (US4, FR-011, FR-012, FR-043). */
export function useSessionActions() {
  const qc = useQueryClient();
  const onSuccess = () => invalidateScheduleViews(qc);
  const update = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: SessionPatch }) =>
      apiFetch<ClassSession>(`/sessions/${id}`, { method: 'PATCH', body: patch }),
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
