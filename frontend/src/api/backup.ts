import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from './client';

export type BackupKind = 'tu-dong' | 'thu-cong' | 'truoc-khoi-phuc';
export type DestinationState = 'ok' | 'missing' | 'no_permission' | 'icloud_off' | 'not_writable';

export type BackupConfig = {
  enabled: boolean;
  /** "HH:MM" */
  schedule_time: string;
  /** null = thư mục mặc định trong iCloud Drive. */
  destination_path: string | null;
  destination_display: string;
  retention_count: number;
};

export type BackupFile = {
  name: string;
  path: string;
  kind: BackupKind;
  created_at: string;
  size: number;
  location: 'local' | 'icloud';
};

export type BackupJob = {
  id: number;
  kind: 'backup_now' | 'restore';
  source_path: string | null;
  state: 'pending' | 'running' | 'done' | 'failed';
  step: string | null;
  message: string | null;
  created_at: string;
  finished_at: string | null;
};

export type BackupStatus = {
  config: BackupConfig;
  agent_online: boolean;
  destination: { state: DestinationState; message: string | null; path: string | null };
  last_attempt: {
    at: string | null;
    ok: boolean | null;
    size: number | null;
    error: string | null;
  };
  last_success: { at: string; size: number | null } | null;
  /** Quá 3 ngày chưa có bản sao lưu thành công (khi đang bật sao lưu tự động). */
  stale: boolean;
  files: BackupFile[];
  job: BackupJob | null;
};

export const backupStatusKey = ['backup-status'] as const;

export const isJobActive = (job: BackupJob | null | undefined): boolean =>
  job?.state === 'pending' || job?.state === 'running';

/** Có việc đang chạy thì hỏi lại mỗi 2 giây, ngược lại mỗi 30 giây. */
export function useBackupStatus() {
  return useQuery({
    queryKey: backupStatusKey,
    queryFn: async () => (await apiFetch<BackupStatus>('/backup/status')).data,
    refetchInterval: (query) => (isJobActive(query.state.data?.job) ? 2_000 : 30_000),
  });
}

export function usePatchBackupConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Partial<Omit<BackupConfig, 'destination_display'>>) =>
      apiFetch<BackupConfig>('/backup/config', { method: 'PATCH', body: patch }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: backupStatusKey }),
  });
}

export function useCreateBackupJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (job: { kind: 'backup_now' } | { kind: 'restore'; source_path: string }) =>
      apiFetch<BackupJob>('/backup/jobs', { method: 'POST', body: job }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: backupStatusKey }),
  });
}

/** Cần chú ý: quá 3 ngày chưa sao lưu, hoặc thư mục sao lưu đang có vấn đề (chấm trên biểu tượng Cài đặt). */
export function backupNeedsAttention(status: BackupStatus | undefined): boolean {
  if (!status?.config?.enabled) return false; // chưa tải xong hoặc API chưa trả đúng dạng
  return status.stale || status.destination?.state !== 'ok';
}
