import { useShifts } from '../../api/shifts';
import type { ShiftRef } from '../../api/types';
import { t } from '../../i18n/vi';
import { cx } from '../../ui/cx';
import { shiftRanges } from '../../lib/shifts';

export type TimeChoice = { shift: ShiftRef | null; start_time: string; end_time: string };

const CUSTOM = 'custom';

/**
 * Chọn ca ("Ca 2"), dãy ca liền nhau ("Ca 1–2") hoặc "Giờ tuỳ chỉnh" (FR-039).
 * `compact` dùng trong bảng nhập nhiều môn.
 */
export function ShiftPicker({
  value,
  onChange,
  compact = false,
  label,
}: {
  value: TimeChoice;
  onChange: (value: TimeChoice) => void;
  compact?: boolean;
  label?: string;
}) {
  const shifts = useShifts();
  const ranges = shiftRanges(shifts.data ?? []);
  const selectedKey = value.shift
    ? `${value.shift.start_shift_id}-${value.shift.end_shift_id}`
    : CUSTOM;

  function choose(key: string) {
    if (key === CUSTOM) {
      onChange({ shift: null, start_time: value.start_time, end_time: value.end_time });
      return;
    }
    const range = ranges.find((r) => r.key === key);
    if (range) {
      onChange({
        shift: { start_shift_id: range.start_shift_id, end_shift_id: range.end_shift_id },
        start_time: range.start_time,
        end_time: range.end_time,
      });
    }
  }

  return (
    <div className={cx('flex items-center gap-2', compact ? 'min-w-[140px]' : 'flex-wrap')}>
      <select
        aria-label={label ?? t('shifts.pick')}
        value={selectedKey}
        onChange={(e) => choose(e.target.value)}
      >
        {ranges.map((r) => (
          <option key={r.key} value={r.key}>
            {compact ? r.label : `${r.label} (${r.start_time}–${r.end_time})`}
          </option>
        ))}
        <option value={CUSTOM}>{t('shifts.custom')}</option>
      </select>
      {value.shift === null ? (
        <span className="flex items-center gap-1">
          <input
            type="time"
            aria-label={t('subjects.fieldStartTime')}
            value={value.start_time}
            onChange={(e) => onChange({ ...value, start_time: e.target.value })}
          />
          <span>–</span>
          <input
            type="time"
            aria-label={t('subjects.fieldEndTime')}
            value={value.end_time}
            onChange={(e) => onChange({ ...value, end_time: e.target.value })}
          />
        </span>
      ) : (
        !compact && (
          <span className="whitespace-nowrap text-muted">
            {value.start_time} – {value.end_time}
          </span>
        )
      )}
    </div>
  );
}

/** Dữ liệu gửi API: ca hoặc giờ tuỳ chỉnh, không bao giờ cả hai. */
export function timeChoiceToInput(choice: TimeChoice) {
  return choice.shift
    ? { shift: choice.shift, start_time: null, end_time: null }
    : { shift: null, start_time: choice.start_time || null, end_time: choice.end_time || null };
}
