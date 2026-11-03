import { useState } from 'react';
import { useToday } from '../api/today';
import type { ClassSession } from '../api/types';
import { SessionDetail } from '../components/SessionDetail';
import { TaskItem } from '../components/TaskItem';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';
import { formatDayLong } from '../lib/dates';
import { sessionTimeRange } from '../lib/format';

/** Trang "Hôm nay" (US3, FR-019, FR-020): buổi học, công việc hạn hôm nay, nhóm Quá hạn. */
export function TodayPage() {
  const today = useToday();
  const [openSession, setOpenSession] = useState<ClassSession | null>(null);
  if (today.isLoading) return <p className="muted">{t('common.loading')}</p>;
  if (today.error) return <p className="field__error">{today.error.message}</p>;
  const data = today.data!;
  const nothing =
    data.sessions.length === 0 &&
    data.tasks_due_today.length === 0 &&
    data.overdue_tasks.length === 0;

  return (
    <section className="narrow">
      <h1>{t('today.title', { date: formatDayLong(data.date) })}</h1>
      {data.notices.map((n) => (
        <p key={n.code} className="notice">
          {n.message}
        </p>
      ))}
      {nothing ? (
        <p className="empty-day">{t('today.empty')}</p>
      ) : (
        <>
          <h2>{t('today.sessions')}</h2>
          {data.sessions.length === 0 ? (
            <p className="muted">{t('today.noSessions')}</p>
          ) : (
            <ul className="task-list">
              {data.sessions.map((s) => (
                <SessionRow key={s.id} session={s} onOpen={() => setOpenSession(s)} />
              ))}
            </ul>
          )}

          <h2>{t('today.tasks')}</h2>
          {data.tasks_due_today.length === 0 ? (
            <p className="muted">{t('today.noTasks')}</p>
          ) : (
            <ul className="task-list">
              {data.tasks_due_today.map((task) => (
                <TaskItem key={task.id} task={task} showList />
              ))}
            </ul>
          )}

          {data.overdue_tasks.length > 0 && (
            <>
              <h2 className="text-danger">{t('today.overdue')}</h2>
              <ul className="task-list">
                {data.overdue_tasks.map((task) => (
                  <TaskItem key={task.id} task={task} showList />
                ))}
              </ul>
            </>
          )}
        </>
      )}
      {openSession && <SessionDetail session={openSession} onClose={() => setOpenSession(null)} />}
    </section>
  );
}

function SessionRow({ session, onOpen }: { session: ClassSession; onOpen: () => void }) {
  return (
    <li
      className={`task-item task-item--clickable${session.is_cancelled ? ' is-done' : ''}${session.is_important ? ' is-important' : ''}`}
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onOpen()}
    >
      <span className="color-bar" style={{ backgroundColor: colorHex(session.display_color) }} />
      <div className="session-time">{sessionTimeRange(session)}</div>
      <div className="task-item__body">
        <div className="task-item__title">
          {session.is_important && (
            <span className="star" aria-label={t('important.label')}>
              ★{' '}
            </span>
          )}
          {session.subject_name}
        </div>
        <div className="task-item__meta">
          {session.room && <span>{session.room}</span>}
          {session.lecturer && <span>{session.lecturer}</span>}
          {session.is_cancelled && (
            <span className="badge badge--danger">{t('today.cancelled')}</span>
          )}
        </div>
      </div>
    </li>
  );
}
