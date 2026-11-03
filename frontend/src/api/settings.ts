import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';
import { invalidateAll } from './keys';

export type AppSettings = {
  session_reminder_minutes: number;
  task_reminder_minutes: number;
  date_only_task_reminder_time: string;
  calendar_sync_enabled: boolean;
  calendar_sync_prompted: boolean;
  auto_deadline_evening_from: string;
  auto_deadline_due_time: string;
  auto_deadline_excluded_keywords: string[];
  important_reminder_offsets: number[];
  exam_extra_reminder_offsets: number[];
  exam_reminder_minutes: number;
  daily_digest_enabled: boolean;
  daily_digest_time: string;
  daily_digest_overdue_only: boolean;
};

export type DigestPreview =
  | { date: string; empty: true }
  | {
      date: string;
      empty: false;
      fire_at: string;
      title: string;
      lines: string[];
      is_important: boolean;
    };

export type SyncStatus = {
  sync_enabled: boolean;
  revision: number;
  agent_online: boolean;
  last_seen_at: string | null;
  permission: 'unknown' | 'granted' | 'denied';
  icloud_source: 'icloud' | 'local_only' | 'unknown';
  last_synced_revision: number;
  last_error: string | null;
};

export const settingsKey = ['settings'] as const;

export function useSettings() {
  return useQuery({
    queryKey: settingsKey,
    queryFn: async () => (await apiFetch<AppSettings>('/settings')).data,
  });
}

export function useSaveSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Partial<AppSettings>) =>
      apiFetch<AppSettings>('/settings', { method: 'PATCH', body: patch }),
    onSuccess: () => invalidateAll(qc), // quy tắc deadline đổi → task tự tạo đổi theo
  });
}

export function useSyncStatus(enabled: boolean) {
  return useQuery({
    queryKey: ['sync-status'],
    queryFn: async () => (await apiFetch<SyncStatus>('/sync/status')).data,
    enabled,
    refetchInterval: 15_000,
  });
}
