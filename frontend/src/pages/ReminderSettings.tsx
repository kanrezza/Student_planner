import { useState } from 'react';
import { useSaveSettings, useSettings, useSyncStatus, type AppSettings } from '../api/settings';
import { minutesLabel, REMINDER_PRESETS } from '../components/ReminderSelect';
import { t } from '../i18n/vi';
import { formatDayLong, formatTime } from '../lib/dates';
import { notificationPermission } from '../reminders/useReminders';

/** Cài đặt → Nhắc lịch (US7): mốc nhắc mặc định, đồng bộ Lịch/Lời nhắc, trạng thái agent. */
export function ReminderSettings() {
  const settings = useSettings();
  const save = useSaveSettings();
  const s = settings.data;
  const status = useSyncStatus(Boolean(s?.calendar_sync_enabled));
  const [permission, setPermission] = useState(notificationPermission());
  if (!s) return null;

  const patch = (p: Partial<AppSettings>) => save.mutate(p);

  return (
    <section className="panel">
      <h2>{t('reminders.title')}</h2>

      <div className="form-row">
        <label className="field">
          <span className="field__label">{t('reminders.sessionDefault')}</span>
          <select
            value={s.session_reminder_minutes}
            onChange={(e) => patch({ session_reminder_minutes: Number(e.target.value) })}
          >
            {REMINDER_PRESETS.map((m) => (
              <option key={m} value={m}>
                {t('reminders.before', { time: minutesLabel(m) })}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field__label">{t('reminders.taskDefault')}</span>
          <select
            value={s.task_reminder_minutes}
            onChange={(e) => patch({ task_reminder_minutes: Number(e.target.value) })}
          >
            {REMINDER_PRESETS.map((m) => (
              <option key={m} value={m}>
                {t('reminders.before', { time: minutesLabel(m) })}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field__label">{t('reminders.dateOnlyTime')}</span>
          <input
            type="time"
            value={s.date_only_task_reminder_time}
            onChange={(e) =>
              e.target.value && patch({ date_only_task_reminder_time: e.target.value })
            }
          />
        </label>
      </div>

      <h3>{t('reminders.syncTitle')}</h3>
      <label className="checkbox-line">
        <input
          type="checkbox"
          checked={s.calendar_sync_enabled}
          onChange={(e) =>
            patch({ calendar_sync_enabled: e.target.checked, calendar_sync_prompted: true })
          }
        />
        {t('reminders.syncToggle')}
      </label>
      <p className="muted">{t('reminders.syncHelp')}</p>
      {s.calendar_sync_enabled && status.data && <AgentStatusLine status={status.data} />}

      {!s.calendar_sync_enabled && (
        <>
          <h3>{t('reminders.browserTitle')}</h3>
          <p className="muted">{t('reminders.browserHelp')}</p>
          {permission === 'granted' && <p>✅ {t('reminders.browserOn')}</p>}
          {permission === 'denied' && <p className="notice">{t('reminders.browserDenied')}</p>}
          {permission === 'default' && (
            <button
              type="button"
              className="button--primary"
              onClick={() => void Notification.requestPermission().then(setPermission)}
            >
              {t('reminders.browserEnable')}
            </button>
          )}
          {permission === 'unsupported' && (
            <p className="muted">{t('reminders.browserUnsupported')}</p>
          )}
        </>
      )}
    </section>
  );
}

function AgentStatusLine({ status }: { status: import('../api/settings').SyncStatus }) {
  if (status.permission === 'denied') {
    return <p className="notice">{t('reminders.agentDenied')}</p>;
  }
  if (!status.agent_online) {
    return (
      <div className="notice">
        <p>{t('reminders.agentOffline')}</p>
        <pre className="code">mac-agent/scripts/install.sh</pre>
      </div>
    );
  }
  return (
    <>
      {status.icloud_source === 'local_only' && <p className="notice">{t('reminders.noIcloud')}</p>}
      <p>
        ✅{' '}
        {t('reminders.agentOk', {
          time: status.last_seen_at
            ? `${formatTime(status.last_seen_at)}, ${formatDayLong(status.last_seen_at)}`
            : '',
        })}
      </p>
      {status.last_error && <p className="field__error">{status.last_error}</p>}
    </>
  );
}
