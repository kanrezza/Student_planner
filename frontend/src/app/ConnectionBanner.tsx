/**
 * Dải "Mất kết nối…" khi các truy vấn lỗi mạng liên tiếp (desktop-shell §2, FR-002).
 * QueryCache báo lỗi/thành công vào `connectionMonitor`; dải tự ẩn khi có truy vấn thành công.
 */
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useSyncExternalStore } from 'react';
import { ApiError } from '../api/client';
import { t } from '../i18n/vi';
import { IconAlert } from '../ui/icons';

const FAILURES_BEFORE_BANNER = 2;
const RETRY_EVERY_MS = 3000;

function createConnectionMonitor() {
  let failures = 0;
  let lost = false;
  const listeners = new Set<() => void>();
  const set = (next: boolean) => {
    if (next === lost) return;
    lost = next;
    listeners.forEach((listener) => listener());
  };
  return {
    onError(error: unknown) {
      const network = error instanceof ApiError && error.code === 'network_error';
      const gateway = error instanceof ApiError && [502, 503, 504].includes(error.status);
      if (!network && !gateway) return;
      failures += 1;
      if (failures >= FAILURES_BEFORE_BANNER) set(true);
    },
    onSuccess() {
      failures = 0;
      set(false);
    },
    subscribe(listener: () => void) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    isLost: () => lost,
  };
}

export const connectionMonitor = createConnectionMonitor();

export function ConnectionBanner() {
  const lost = useSyncExternalStore(connectionMonitor.subscribe, connectionMonitor.isLost);
  const qc = useQueryClient();

  useEffect(() => {
    if (!lost) return;
    const timer = window.setInterval(() => {
      void qc.refetchQueries({ type: 'active' });
    }, RETRY_EVERY_MS);
    return () => window.clearInterval(timer);
  }, [lost, qc]);

  if (!lost) return null;
  return (
    <div
      role="status"
      className="flex items-center gap-2 border-b border-border bg-warning-soft px-4 py-1.5 text-warning"
    >
      <IconAlert size={16} />
      {t('connection.lost')}
    </div>
  );
}
