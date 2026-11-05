import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { backupStatusKey, isJobActive, useBackupStatus } from '../../api/backup';
import { RESTORING_EVENT } from '../../api/client';
import { invalidateAll } from '../../api/keys';
import { t } from '../../i18n/vi';
import { useToast } from '../../ui/Toast';

/**
 * Theo dõi việc sao lưu/khôi phục: hiện lớp phủ toàn app khi đang khôi phục (spec US2-3, FR-012e),
 * báo kết quả bằng thông báo nhỏ và làm mới toàn bộ dữ liệu khi khôi phục xong.
 */
export function RestoreOverlay() {
  const status = useBackupStatus();
  const qc = useQueryClient();
  const toast = useToast();
  const [forced, setForced] = useState(false); // API vừa trả 503 "restoring"
  const seenActive = useRef(new Set<number>());

  useEffect(() => {
    const onRestoring = () => {
      setForced(true);
      void qc.invalidateQueries({ queryKey: backupStatusKey });
    };
    window.addEventListener(RESTORING_EVENT, onRestoring);
    return () => window.removeEventListener(RESTORING_EVENT, onRestoring);
  }, [qc]);

  const job = status.data?.job ?? null;
  const active = isJobActive(job);

  useEffect(() => {
    if (!job) return;
    if (active) {
      seenActive.current.add(job.id);
      return;
    }
    if (!seenActive.current.has(job.id)) return; // việc cũ đã xong từ trước: không báo lại
    seenActive.current.delete(job.id);
    const reason = job.message ?? t('errors.unknown');
    if (job.kind === 'restore') {
      if (job.state === 'done') {
        invalidateAll(qc);
        toast.show(job.message ?? t('backup.restored'));
      } else {
        toast.show(t('backup.restoreFailed', { reason }), { tone: 'danger' });
      }
    } else if (job.state === 'done') {
      toast.show(t('backup.backupDone'));
    } else {
      toast.show(t('backup.backupFailed', { reason }), { tone: 'danger' });
    }
  }, [job, active, qc, toast]);

  useEffect(() => {
    // Hết khôi phục (đã lấy được trạng thái mới mà không còn việc khôi phục đang chạy) → gỡ lớp phủ.
    if (forced && status.isSuccess && !(active && job?.kind === 'restore')) setForced(false);
  }, [forced, status.isSuccess, status.dataUpdatedAt, active, job?.kind]);

  const restoring = (active && job?.kind === 'restore') || forced;
  if (!restoring) return null;
  const step = job?.step ? t(`backup.steps.${job.step}`) : t('backup.restoring');
  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-label={t('backup.restoring')}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm"
    >
      <div className="rounded-2xl border border-border bg-surface px-8 py-6 text-center shadow-lg">
        <p className="text-[16px] font-semibold">{step}</p>
        <p className="mt-1 text-muted">{t('backup.restoreHelp')}</p>
      </div>
    </div>
  );
}
