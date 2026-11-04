import { useState } from 'react';
import { apiFetch } from '../../api/client';
import {
  useSaveSettings,
  useSettings,
  useSyncStatus,
  type AppSettings,
  type DigestPreview,
} from '../../api/settings';
import { minutesLabel, REMINDER_PRESETS } from '../../components/ReminderSelect';
import { t } from '../../i18n/vi';
import { formatDayLong, formatTime } from '../../lib/dates';
import { notificationPermission } from '../../reminders/useReminders';
import { Button } from '../../ui/Button';
import { IconButton } from '../../ui/IconButton';
import { IconClose } from '../../ui/icons';
import { Card, CheckboxLine, Code, Notice, SubHeading } from '../../ui/layout';
import { Switch } from '../../ui/Switch';
import type { SyncStatus } from '../../api/settings';

function useSettingsPatch() {
  const settings = useSettings();
  const save = useSaveSettings();
  return { s: settings.data, patch: (p: Partial<AppSettings>) => save.mutate(p) };
}

function ReminderPresetSelect({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="flex min-w-0 flex-col gap-1">
      <span className="text-[12px] font-medium text-muted">{label}</span>
      <select value={value} onChange={(e) => onChange(Number(e.target.value))}>
        {REMINDER_PRESETS.map((m) => (
          <option key={m} value={m}>
            {t('reminders.before', { time: minutesLabel(m) })}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Cài đặt → Nhắc lịch và đồng bộ (FR-021 đến FR-023, FR-051 đến FR-056). */
export function ReminderSettings() {
  const { s, patch } = useSettingsPatch();
  const status = useSyncStatus(Boolean(s?.calendar_sync_enabled));
  const [permission, setPermission] = useState(notificationPermission());
  if (!s) return null;

  return (
    <>
      <Card title={t('reminders.title')}>
        <div className="grid gap-3 sm:grid-cols-3">
          <ReminderPresetSelect
            label={t('reminders.sessionDefault')}
            value={s.session_reminder_minutes}
            onChange={(v) => patch({ session_reminder_minutes: v })}
          />
          <ReminderPresetSelect
            label={t('reminders.taskDefault')}
            value={s.task_reminder_minutes}
            onChange={(v) => patch({ task_reminder_minutes: v })}
          />
          <label className="flex min-w-0 flex-col gap-1">
            <span className="text-[12px] font-medium text-muted">
              {t('reminders.dateOnlyTime')}
            </span>
            <input
              type="time"
              value={s.date_only_task_reminder_time}
              onChange={(e) =>
                e.target.value && patch({ date_only_task_reminder_time: e.target.value })
              }
            />
          </label>
        </div>
      </Card>

      <Card
        title={t('reminders.syncTitle')}
        description={t('reminders.syncHelp')}
        actions={
          <Switch
            label={t('reminders.syncToggle')}
            checked={s.calendar_sync_enabled}
            onChange={(on) => patch({ calendar_sync_enabled: on, calendar_sync_prompted: true })}
          />
        }
      >
        {s.calendar_sync_enabled && status.data && <AgentStatusLine status={status.data} />}
      </Card>

      {!s.calendar_sync_enabled && (
        <Card title={t('reminders.browserTitle')} description={t('reminders.browserHelp')}>
          {permission === 'granted' && (
            <Notice tone="success">✅ {t('reminders.browserOn')}</Notice>
          )}
          {permission === 'denied' && (
            <Notice tone="warning">{t('reminders.browserDenied')}</Notice>
          )}
          {permission === 'default' && (
            <Button
              variant="primary"
              onClick={() => void Notification.requestPermission().then(setPermission)}
            >
              {t('reminders.browserEnable')}
            </Button>
          )}
          {permission === 'unsupported' && (
            <p className="text-muted">{t('reminders.browserUnsupported')}</p>
          )}
        </Card>
      )}
    </>
  );
}

function AgentStatusLine({ status }: { status: SyncStatus }) {
  if (status.permission === 'denied') {
    return <Notice tone="warning">{t('reminders.agentDenied')}</Notice>;
  }
  if (!status.agent_online) {
    return (
      <Notice tone="warning">
        <p>{t('reminders.agentOffline')}</p>
        <Code>mac-agent/scripts/install.sh</Code>
      </Notice>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {status.icloud_source === 'local_only' && (
        <Notice tone="warning">{t('reminders.noIcloud')}</Notice>
      )}
      <Notice tone="success">
        ✅{' '}
        {t('reminders.agentOk', {
          time: status.last_seen_at
            ? `${formatTime(status.last_seen_at)}, ${formatDayLong(status.last_seen_at)}`
            : '',
        })}
      </Notice>
      {status.last_error && <p className="text-danger">{status.last_error}</p>}
    </div>
  );
}

const MAX_IMPORTANT_OFFSETS = 6;
const OFFSET_CHOICES = [5, 10, 15, 30, 60, 120, 180, 360, 720, 1440, 2880, 10080];

/** Cài đặt → Mốc nhắc quan trọng. */
export function ImportantOffsetsSettings() {
  const { s, patch } = useSettingsPatch();
  if (!s) return null;
  return (
    <Card title={t('important.offsetsTitle')} description={t('important.offsetsHelp')}>
      <ImportantOffsets
        value={s.important_reminder_offsets}
        onChange={(v) => patch({ important_reminder_offsets: v })}
      />
    </Card>
  );
}

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
      <div className="flex flex-wrap gap-1.5">
        {value.map((m) => (
          <span
            key={m}
            className="inline-flex h-7 items-center gap-1 rounded-full bg-accent-soft pl-3 pr-1 text-[12px] font-medium text-accent-strong"
          >
            {t('reminders.before', { time: minutesLabel(m) })}
            <IconButton
              size="sm"
              tooltip={false}
              icon={<IconClose size={12} />}
              disabled={value.length <= 1}
              label={t('important.removeOffset', { time: minutesLabel(m) })}
              onClick={() => onChange(value.filter((x) => x !== m))}
            />
          </span>
        ))}
      </div>
      {!full && choices.length > 0 && (
        <div className="mt-3 flex items-center gap-2">
          <select
            aria-label={t('important.newOffset')}
            value={choices.includes(adding) ? adding : choices[0]}
            onChange={(e) => setAdding(Number(e.target.value))}
            className="w-56"
          >
            {choices.map((m) => (
              <option key={m} value={m}>
                {t('reminders.before', { time: minutesLabel(m) })}
              </option>
            ))}
          </select>
          <Button
            onClick={() => onChange([...value, choices.includes(adding) ? adding : choices[0]])}
          >
            {t('autoDeadline.add')}
          </Button>
        </div>
      )}
    </>
  );
}

/** Cài đặt → Thông báo tổng hợp hằng ngày (FR-065, FR-066). */
export function DigestSettings() {
  const { s, patch } = useSettingsPatch();
  const [preview, setPreview] = useState<DigestPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (!s) return null;

  async function loadPreview() {
    setError(null);
    try {
      setPreview((await apiFetch<DigestPreview>('/digest')).data);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <Card
      title={t('digest.title')}
      description={t('digest.help')}
      actions={
        <Switch
          label={t('digest.enable')}
          checked={s.daily_digest_enabled}
          onChange={(on) => patch({ daily_digest_enabled: on })}
        />
      }
    >
      {s.daily_digest_enabled && (
        <>
          <label className="flex w-40 flex-col gap-1">
            <span className="text-[12px] font-medium text-muted">{t('digest.time')}</span>
            <input
              type="time"
              value={s.daily_digest_time}
              onChange={(e) => e.target.value && patch({ daily_digest_time: e.target.value })}
            />
          </label>
          <CheckboxLine
            checked={s.daily_digest_overdue_only}
            onChange={(checked) => patch({ daily_digest_overdue_only: checked })}
            label={t('digest.overdueOnly')}
          />
        </>
      )}
      <SubHeading>{t('digest.preview')}</SubHeading>
      <Button size="sm" onClick={() => void loadPreview()}>
        {t('digest.preview')}
      </Button>
      {error && <p className="mt-2 text-danger">{error}</p>}
      {preview &&
        (preview.empty ? (
          <p className="mt-2 text-muted">{t('digest.empty')}</p>
        ) : (
          <div className="mt-3 rounded-lg bg-surface-2 px-3 py-2">
            <p className="font-semibold">{preview.title}</p>
            <ul className="mt-1 list-disc pl-5">
              {preview.lines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        ))}
    </Card>
  );
}
