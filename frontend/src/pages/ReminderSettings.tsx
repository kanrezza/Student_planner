import { useState } from 'react';
import { apiFetch } from '../api/client';
import {
  useSaveSettings,
  useSettings,
  useSyncStatus,
  type AppSettings,
  type DigestPreview,
} from '../api/settings';
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

      <ImportantOffsets
        value={s.important_reminder_offsets}
        onChange={(v) => patch({ important_reminder_offsets: v })}
      />
      <DigestSettings settings={s} patch={patch} />

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

const MAX_IMPORTANT_OFFSETS = 6;
const OFFSET_CHOICES = [5, 10, 15, 30, 60, 120, 180, 360, 720, 1440, 2880, 10080];

/** Các mốc nhắc của mục quan trọng (FR-068): 1–6 mốc, dạng chip. */
export function ImportantOffsets({
  value,
  onChange,
}: {
  value: number[];
  onChange: (value: number[]) => void;
}) {
  const choices = OFFSET_CHOICES.filter((m) => !value.includes(m));
  const [adding, setAdding] = useState<number>(choices[0] ?? 15);
  const full = value.length >= MAX_IMPORTANT_OFFSETS;
  return (
    <>
      <h3>{t('important.offsetsTitle')}</h3>
      <p className="muted">{t('important.offsetsHelp')}</p>
      <div className="tag-chips">
        {value.map((m) => (
          <span key={m} className="tag-chip">
            {t('reminders.before', { time: minutesLabel(m) })}
            <button
              type="button"
              className="button--ghost"
              disabled={value.length <= 1}
              aria-label={t('important.removeOffset', { time: minutesLabel(m) })}
              onClick={() => onChange(value.filter((x) => x !== m))}
            >
              ✕
            </button>
          </span>
        ))}
      </div>
      {!full && choices.length > 0 && (
        <div className="row-actions" style={{ marginTop: '0.5rem' }}>
          <select
            aria-label={t('important.newOffset')}
            value={choices.includes(adding) ? adding : choices[0]}
            onChange={(e) => setAdding(Number(e.target.value))}
          >
            {choices.map((m) => (
              <option key={m} value={m}>
                {t('reminders.before', { time: minutesLabel(m) })}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => onChange([...value, choices.includes(adding) ? adding : choices[0]])}
          >
            {t('autoDeadline.add')}
          </button>
        </div>
      )}
    </>
  );
}

/** Thông báo tổng hợp hằng ngày (FR-065, FR-066). */
function DigestSettings({
  settings: s,
  patch,
}: {
  settings: AppSettings;
  patch: (p: Partial<AppSettings>) => void;
}) {
  const [preview, setPreview] = useState<DigestPreview | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadPreview() {
    setError(null);
    try {
      setPreview((await apiFetch<DigestPreview>('/digest')).data);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <>
      <h3>{t('digest.title')}</h3>
      <label className="checkbox-line">
        <input
          type="checkbox"
          checked={s.daily_digest_enabled}
          onChange={(e) => patch({ daily_digest_enabled: e.target.checked })}
        />
        {t('digest.enable')}
      </label>
      {s.daily_digest_enabled && (
        <>
          <div className="form-row">
            <label className="field">
              <span className="field__label">{t('digest.time')}</span>
              <input
                type="time"
                value={s.daily_digest_time}
                onChange={(e) => e.target.value && patch({ daily_digest_time: e.target.value })}
              />
            </label>
          </div>
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={s.daily_digest_overdue_only}
              onChange={(e) => patch({ daily_digest_overdue_only: e.target.checked })}
            />
            {t('digest.overdueOnly')}
          </label>
        </>
      )}
      <p className="muted">{t('digest.help')}</p>
      <button type="button" onClick={() => void loadPreview()}>
        {t('digest.preview')}
      </button>
      {error && <p className="field__error">{error}</p>}
      {preview &&
        (preview.empty ? (
          <p className="muted">{t('digest.empty')}</p>
        ) : (
          <div className="digest-preview">
            <strong>{preview.title}</strong>
            <ul>
              {preview.lines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        ))}
    </>
  );
}
