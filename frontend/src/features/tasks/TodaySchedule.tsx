import { useState } from 'react';
import { useToday } from '../../api/today';
import type { ClassSession } from '../../api/types';
import { SessionDetail } from '../../components/SessionDetail';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { sessionTimeRange } from '../../lib/format';
import { Badge } from '../../ui/Badge';
import { cx } from '../../ui/cx';
import { IconAlert, IconStarFilled } from '../../ui/icons';

/**
 * Khối "Lịch hôm nay" ở đầu danh sách Hôm nay (feature 002 FR-012): buổi thi (khi có) rồi buổi
 * học, kèm các cảnh báo hiện có của trang Hôm nay (đồng bộ, quyền).
 */
export function TodaySchedule() {
  const today = useToday();
  const [open, setOpen] = useState<ClassSession | null>(null);
  const data = today.data;
  if (!data || (data.sessions.length === 0 && data.notices.length === 0)) return null;

  return (
    <section aria-label={t('schedule.title')} className="flex flex-col gap-2">
      {data.notices.map((notice) => (
        <p
          key={notice.code}
          className="flex items-start gap-2 rounded-lg bg-warning-soft px-3 py-2 text-warning"
        >
          <IconAlert size={16} className="mt-0.5 shrink-0" />
          {notice.message}
        </p>
      ))}
      {data.sessions.length > 0 && (
        <div className="rounded-xl border border-border bg-surface p-2">
          <h2 className="px-2 pb-1 pt-0.5 text-[12px] font-semibold uppercase tracking-wide text-muted">
            {t('schedule.title')}
          </h2>
          <ul className="flex flex-col">
            {data.sessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setOpen(session)}
                  className={cx(
                    'flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left hover:bg-surface-2',
                    session.is_cancelled && 'opacity-60',
                  )}
                >
                  <span
                    className="h-8 w-1 shrink-0 rounded-full"
                    style={{ backgroundColor: colorHex(session.display_color) }}
                  />
                  <span className="w-[92px] shrink-0 text-[12px] text-muted tabular-nums">
                    {sessionTimeRange(session)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span
                      className={cx(
                        'flex items-center gap-1 truncate font-medium',
                        session.is_cancelled && 'line-through',
                      )}
                    >
                      {session.is_important && (
                        <span aria-label={t('important.label')} className="text-warning">
                          <IconStarFilled size={13} />
                        </span>
                      )}
                      {session.subject_name}
                    </span>
                    {session.room && (
                      <span className="block truncate text-[12px] text-muted">{session.room}</span>
                    )}
                  </span>
                  {session.is_cancelled && <Badge tone="danger">{t('schedule.cancelled')}</Badge>}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {open && <SessionDetail session={open} onClose={() => setOpen(null)} />}
    </section>
  );
}
