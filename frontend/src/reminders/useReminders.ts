import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { apiFetch } from '../api/client';
import { useSettings } from '../api/settings';
import { becomeLeader } from './leader';
import { ReminderScheduler, type UpcomingReminder } from './scheduler';

const POLL_MS = 5 * 60_000;

/** Chỉ nhắc bằng trình duyệt khi chưa bật đồng bộ Lịch và đã được cấp quyền thông báo (FR-021). */
export function shouldRunBrowserReminders(
  syncEnabled: boolean | undefined,
  permission: NotificationPermission | 'unsupported',
): boolean {
  return syncEnabled === false && permission === 'granted';
}

export function notificationPermission(): NotificationPermission | 'unsupported' {
  return typeof Notification === 'undefined' ? 'unsupported' : Notification.permission;
}

/** Gắn một lần ở App: tải nhắc mỗi 5 phút và ngay sau mỗi thay đổi dữ liệu (FR-023). */
export function useReminders() {
  const qc = useQueryClient();
  const settings = useSettings();
  const schedulerRef = useRef<ReminderScheduler | null>(null);
  const run = shouldRunBrowserReminders(
    settings.data?.calendar_sync_enabled,
    notificationPermission(),
  );

  useEffect(() => {
    if (!run) return;
    const scheduler = new ReminderScheduler((item) => {
      new Notification(item.title, { body: item.body, tag: item.sync_key });
    });
    schedulerRef.current = scheduler;
    let leader = false;
    const refresh = async () => {
      if (!leader) return;
      try {
        const { data } = await apiFetch<UpcomingReminder[]>('/reminders/upcoming?hours=24');
        scheduler.refresh(data);
      } catch {
        // mất kết nối tạm thời: giữ các hẹn giờ hiện có, thử lại ở lần sau
      }
    };
    const release = becomeLeader(() => {
      leader = true;
      void refresh();
    });
    const interval = setInterval(() => void refresh(), POLL_MS);
    const unsubscribe = qc.getMutationCache().subscribe((event) => {
      if (event.type === 'updated' && event.mutation.state.status === 'success') void refresh();
    });
    return () => {
      unsubscribe();
      clearInterval(interval);
      release();
      scheduler.clear();
      schedulerRef.current = null;
    };
  }, [run, qc]);
}
