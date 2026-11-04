import { t } from '../../i18n/vi';
import { cx } from '../../ui/cx';
import { WEEKDAYS_VN } from '../../lib/dates';

/** Chọn một hoặc nhiều thứ trong tuần (1 = Thứ Hai … 7 = Chủ Nhật). */
export function WeekdayPicker({
  value,
  onChange,
}: {
  value: number[];
  onChange: (days: number[]) => void;
}) {
  function toggle(day: number) {
    onChange(value.includes(day) ? value.filter((d) => d !== day) : [...value, day].sort());
  }
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5, 6, 7].map((day) => (
        <button
          key={day}
          type="button"
          aria-pressed={value.includes(day)}
          title={WEEKDAYS_VN[day - 1]}
          className={cx(
            'h-8 w-9 rounded-md border text-[12px] font-medium',
            value.includes(day)
              ? 'border-accent bg-accent text-accent-contrast'
              : 'border-border bg-surface text-text hover:bg-surface-3',
          )}
          onClick={() => toggle(day)}
        >
          {t(`weekdaysShort.${day}`)}
        </button>
      ))}
    </div>
  );
}
