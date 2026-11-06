import { useEffect, useState } from 'react';
import type { RecurrenceRule } from '../../../api/types';
import { DateInput } from '../../../components/DateInput';
import { t } from '../../../i18n/vi';
import { WEEKDAYS_VN } from '../../../lib/dates';
import { cx } from '../../../ui/cx';
import { describeRule } from './describeRule';

type Freq = 'none' | RecurrenceRule['freq'];
type EndKind = RecurrenceRule['end']['kind'];

const SHORT_DAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];

/** Thứ (1 = Thứ Hai … 7 = Chủ Nhật) của ngày "YYYY-MM-DD". */
function isoWeekday(iso: string): number {
  const d = new Date(`${iso}T12:00:00`);
  return ((d.getDay() + 6) % 7) + 1;
}

type Draft = {
  freq: Freq;
  interval: string;
  weekdays: number[];
  monthDay: string;
  endKind: EndKind;
  endDate: string;
  endCount: string;
};

function toDraft(rule: RecurrenceRule | null, dueDate: string): Draft {
  return {
    freq: rule?.freq ?? 'none',
    interval: String(rule?.interval_days ?? 2),
    weekdays: rule?.weekdays ?? (dueDate ? [isoWeekday(dueDate)] : [1]),
    monthDay: String(rule?.month_day ?? (dueDate ? Number(dueDate.slice(8, 10)) : 1)),
    endKind: rule?.end.kind ?? 'never',
    endDate: rule?.end.kind === 'on_date' ? rule.end.date : '',
    endCount: String(rule?.end.kind === 'after_count' ? rule.end.count : 5),
  };
}

/** Quy tắc từ bản nháp, hoặc lỗi tiếng Việt khi chưa hợp lệ (null = Không lặp). */
export function draftToRule(draft: Draft): { rule: RecurrenceRule | null; error?: string } {
  if (draft.freq === 'none') return { rule: null };
  let end: RecurrenceRule['end'] = { kind: 'never' };
  if (draft.endKind === 'on_date') {
    if (!draft.endDate) return { rule: null, error: t('recurrence.errEndDate') };
    end = { kind: 'on_date', date: draft.endDate };
  } else if (draft.endKind === 'after_count') {
    const count = Number(draft.endCount);
    if (!Number.isInteger(count) || count < 1 || count > 999)
      return { rule: null, error: t('recurrence.errEndCount') };
    end = { kind: 'after_count', count };
  }
  switch (draft.freq) {
    case 'daily':
      return { rule: { freq: 'daily', end } };
    case 'every_n_days': {
      const n = Number(draft.interval);
      if (!Number.isInteger(n) || n < 2 || n > 365)
        return { rule: null, error: t('recurrence.errInterval') };
      return { rule: { freq: 'every_n_days', interval_days: n, end } };
    }
    case 'weekly':
      if (draft.weekdays.length === 0) return { rule: null, error: t('recurrence.errWeekdays') };
      return { rule: { freq: 'weekly', weekdays: [...draft.weekdays].sort(), end } };
    case 'monthly': {
      const day = Number(draft.monthDay);
      if (!Number.isInteger(day) || day < 1 || day > 31)
        return { rule: null, error: t('recurrence.errMonthDay') };
      return { rule: { freq: 'monthly', month_day: day, end } };
    }
  }
}

/**
 * Trường "Lặp lại" của bảng chi tiết (FR-015): kiểu lặp + kết thúc. Chỉ gọi `onChange` khi quy tắc
 * hợp lệ; hằng tuần không chọn thứ thì không lưu và báo lỗi ngay dưới ô.
 */
export function RecurrenceEditor({
  value,
  dueDate,
  onChange,
}: {
  value: RecurrenceRule | null;
  dueDate: string;
  onChange: (rule: RecurrenceRule | null) => void;
}) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(value, dueDate));
  const [error, setError] = useState<string | null>(null);
  const signature = JSON.stringify(value);
  useEffect(() => {
    setDraft(toDraft(value, dueDate));
    setError(null);
    // Chỉ đồng bộ lại khi quy tắc trên server đổi, không khi người dùng đang sửa bản nháp.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);

  function update(patch: Partial<Draft>, commit = true) {
    const next = { ...draft, ...patch };
    setDraft(next);
    if (!commit) return;
    const { rule, error: message } = draftToRule(next);
    setError(message ?? null);
    if (!message) onChange(rule);
  }

  const field = 'h-8 px-2';
  return (
    <div className="flex flex-col gap-2">
      <select
        aria-label={t('recurrence.label')}
        value={draft.freq}
        onChange={(e) => update({ freq: e.target.value as Freq })}
        className="w-56"
      >
        <option value="none">{t('recurrence.none')}</option>
        <option value="daily">{t('recurrence.daily')}</option>
        <option value="every_n_days">{t('recurrence.everyN')}</option>
        <option value="weekly">{t('recurrence.weekly')}</option>
        <option value="monthly">{t('recurrence.monthly')}</option>
      </select>

      {draft.freq === 'every_n_days' && (
        <label className="flex items-center gap-2 text-[13px]">
          {t('recurrence.every')}
          <input
            type="number"
            min={2}
            max={365}
            aria-label={t('recurrence.intervalLabel')}
            value={draft.interval}
            onChange={(e) => update({ interval: e.target.value }, false)}
            onBlur={() => update({})}
            className={cx(field, 'w-20')}
          />
          {t('recurrence.days')}
        </label>
      )}

      {draft.freq === 'weekly' && (
        <div role="group" aria-label={t('recurrence.weekdaysLabel')} className="flex gap-1">
          {SHORT_DAYS.map((label, index) => {
            const day = index + 1;
            const on = draft.weekdays.includes(day);
            return (
              <button
                key={day}
                type="button"
                aria-pressed={on}
                title={WEEKDAYS_VN[index]}
                onClick={() =>
                  update({
                    weekdays: on
                      ? draft.weekdays.filter((d) => d !== day)
                      : [...draft.weekdays, day],
                  })
                }
                className={cx(
                  'h-8 min-w-8 rounded-md border px-1.5 text-[12px] font-medium',
                  on
                    ? 'border-accent bg-accent text-accent-contrast'
                    : 'border-border bg-surface hover:bg-surface-2',
                )}
              >
                {label}
              </button>
            );
          })}
        </div>
      )}

      {draft.freq === 'monthly' && (
        <label className="flex items-center gap-2 text-[13px]">
          {t('recurrence.monthDay')}
          <input
            type="number"
            min={1}
            max={31}
            aria-label={t('recurrence.monthDayLabel')}
            value={draft.monthDay}
            onChange={(e) => update({ monthDay: e.target.value }, false)}
            onBlur={() => update({})}
            className={cx(field, 'w-20')}
          />
        </label>
      )}

      {draft.freq !== 'none' && (
        <div className="flex flex-wrap items-center gap-2">
          <select
            aria-label={t('recurrence.endLabel')}
            value={draft.endKind}
            onChange={(e) => update({ endKind: e.target.value as EndKind })}
            className="w-44"
          >
            <option value="never">{t('recurrence.endNever')}</option>
            <option value="on_date">{t('recurrence.endOnDate')}</option>
            <option value="after_count">{t('recurrence.endAfterCount')}</option>
          </select>
          {draft.endKind === 'on_date' && (
            <DateInput
              label={t('recurrence.endDateLabel')}
              value={draft.endDate}
              onChange={(v) => update({ endDate: v }, false)}
              onBlur={() => update({})}
              className="w-[9.5rem]"
            />
          )}
          {draft.endKind === 'after_count' && (
            <label className="flex items-center gap-2 text-[13px]">
              <input
                type="number"
                min={1}
                max={999}
                aria-label={t('recurrence.endCountLabel')}
                value={draft.endCount}
                onChange={(e) => update({ endCount: e.target.value }, false)}
                onBlur={() => update({})}
                className={cx(field, 'w-20')}
              />
              {t('recurrence.endCountSuffix')}
            </label>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="text-[12px] text-danger">
          {error}
        </p>
      )}
      {!error && value && <p className="text-[12px] text-muted">{describeRule(value)}</p>}
    </div>
  );
}
