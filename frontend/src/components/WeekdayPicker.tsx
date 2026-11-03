import { t } from '../i18n/vi';
import { WEEKDAYS_VN } from '../lib/dates';

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
    <div className="weekday-picker">
      {[1, 2, 3, 4, 5, 6, 7].map((day) => (
        <button
          key={day}
          type="button"
          aria-pressed={value.includes(day)}
          title={WEEKDAYS_VN[day - 1]}
          className={value.includes(day) ? 'is-selected' : undefined}
          onClick={() => toggle(day)}
        >
          {t(`weekdaysShort.${day}`)}
        </button>
      ))}
    </div>
  );
}
