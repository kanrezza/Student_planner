import { useCreateBackupJob } from '../../api/backup';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { t } from '../../i18n/vi';
import { formatMoment } from '../../lib/format';

export type RestoreTarget = { path: string; name: string; createdAt?: string };

/**
 * Hộp xác nhận khôi phục (spec US2-2). Xác nhận → tạo việc `restore` cho agent; agent sẽ tự sao lưu
 * dữ liệu hiện tại trước rồi mới khôi phục (FR-012).
 */
export function RestoreDialog({
  target,
  onCancel,
  onConfirmed,
}: {
  target: RestoreTarget | null;
  onCancel: () => void;
  onConfirmed: () => void;
}) {
  const createJob = useCreateBackupJob();
  const message = target
    ? target.createdAt
      ? t('backup.restoreConfirm', { when: formatMoment(target.createdAt) })
      : t('backup.restoreConfirmFile', { name: target.name })
    : '';
  return (
    <ConfirmDialog
      open={target !== null}
      title={t('backup.restoreTitle')}
      message={message}
      confirmLabel={t('backup.restore')}
      onCancel={onCancel}
      onConfirm={() => {
        if (!target) return;
        createJob.mutate({ kind: 'restore', source_path: target.path }, { onSettled: onConfirmed });
      }}
    />
  );
}
