import { t } from '../i18n/vi';

/** Mốc nhắc có sẵn (phút trước giờ học/hạn chót). */
export const REMINDER_PRESETS = [5, 10, 15, 30, 60, 120, 1440];

export function minutesLabel(minutes: number): string {
  if (minutes >= 1440 && minutes % 1440 === 0) return t('reminders.days', { n: minutes / 1440 });
  if (minutes >= 60 && minutes % 60 === 0) return t('reminders.hours', { n: minutes / 60 });
  return t('reminders.minutes', { n: minutes });
}

/**
 * Nhắc riêng cho một môn học hoặc task (FR-022): `null` = theo mặc định, `-1` = không nhắc,
 * số ≥ 0 = số phút báo trước. `dateOnly` (task chỉ có ngày): chỉ "Theo mặc định (08:00)" hoặc
 * "Không nhắc".
 */
export function ReminderSelect({
  value,
  onChange,
  defaultLabel,
  dateOnly = false,
}: {
  value: number | null;
  onChange: (value: number | null) => void;
  defaultLabel: string;
  dateOnly?: boolean;
}) {
  const options = dateOnly ? [] : REMINDER_PRESETS;
  const current = value === null ? 'default' : String(value);
  return (
    <select
      value={current}
      onChange={(e) => onChange(e.target.value === 'default' ? null : Number(e.target.value))}
    >
      <option value="default">{defaultLabel}</option>
      <option value="-1">{t('reminders.off')}</option>
      {options.map((m) => (
        <option key={m} value={m}>
          {t('reminders.before', { time: minutesLabel(m) })}
        </option>
      ))}
      {value !== null && value >= 0 && !options.includes(value) && !dateOnly && (
        <option value={value}>{t('reminders.before', { time: minutesLabel(value) })}</option>
      )}
    </select>
  );
}
