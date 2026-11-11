import { DateInput } from '../../components/DateInput';
import { Button } from '../../ui/Button';
import { t } from '../../i18n/vi';
import type { ScheduleInput } from '../../api/types';
import { blankToNull } from '../../lib/format';
import { ShiftPicker, timeChoiceToInput, type TimeChoice } from './ShiftPicker';
import { WeekdayPicker } from './WeekdayPicker';

/** Một hàng lịch trong form (trạng thái nhập, chưa chuẩn hoá để gửi API). */
export type ScheduleRow = {
  id?: number;
  weekdays: number[];
  start_date: string;
  end_date: string;
  time: TimeChoice;
  period_from: number | null;
  period_to: number | null;
  room: string;
};

export function blankRow(start_date = '', end_date = ''): ScheduleRow {
  return {
    weekdays: [],
    start_date,
    end_date,
    time: { shift: null, start_time: '', end_time: '' },
    period_from: null,
    period_to: null,
    room: '',
  };
}

/** Hàng → dữ liệu gửi API (ca hoặc giờ tuỳ chỉnh, ngày rỗng = theo học kỳ). */
export function rowToInput(row: ScheduleRow): ScheduleInput {
  return {
    ...(row.id ? { id: row.id } : {}),
    weekdays: row.weekdays,
    start_date: row.start_date || null,
    end_date: row.end_date || null,
    ...timeChoiceToInput(row.time),
    period_from: row.period_from,
    period_to: row.period_to,
    room: blankToNull(row.room),
  };
}

/**
 * Danh sách quy tắc lặp của một môn (FR-020a): mỗi hàng có thứ, khoảng ngày, ca/giờ, phòng. Luôn
 * còn ít nhất một hàng; "Thêm lịch" chép hàng cuối. `errors` là `ApiError.fields` của form.
 */
export function ScheduleRows({
  rows,
  onChange,
  errors = {},
}: {
  rows: ScheduleRow[];
  onChange: (rows: ScheduleRow[]) => void;
  errors?: Record<string, string>;
}) {
  const update = (i: number, patch: Partial<ScheduleRow>) =>
    onChange(rows.map((row, j) => (j === i ? { ...row, ...patch } : row)));
  const rowError = (i: number) =>
    Object.entries(errors)
      .filter(([key]) => key === `schedules[${i}]` || key.startsWith(`schedules[${i}].`))
      .map(([, message]) => message);

  function add() {
    const last = rows[rows.length - 1];
    onChange([...rows, { ...last, id: undefined, time: { ...last.time } }]);
  }

  return (
    <fieldset className="mb-3 flex flex-col gap-2">
      <legend className="text-[12px] font-medium text-muted">{t('subjects.schedulesTitle')}</legend>
      {rows.map((row, i) => {
        const messages = rowError(i);
        return (
          <div
            key={row.id ?? `new-${i}`}
            role="group"
            aria-label={t('subjects.scheduleN', { n: i + 1 })}
            className="flex flex-col gap-2 rounded-md border border-border p-2"
          >
            <WeekdayPicker value={row.weekdays} onChange={(weekdays) => update(i, { weekdays })} />
            <ShiftPicker
              value={row.time}
              onChange={(time) => update(i, { time, period_from: null, period_to: null })}
            />
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <label className="flex flex-col gap-1">
                <span className="text-[12px] text-muted">{t('subjects.fieldStartDate')}</span>
                <DateInput
                  value={row.start_date}
                  onChange={(start_date) => update(i, { start_date })}
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[12px] text-muted">{t('subjects.fieldEndDate')}</span>
                <DateInput value={row.end_date} onChange={(end_date) => update(i, { end_date })} />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-[12px] text-muted">{t('subjects.fieldRoom')}</span>
                <input
                  aria-label={`${t('subjects.fieldRoom')} ${i + 1}`}
                  value={row.room}
                  onChange={(e) => update(i, { room: e.target.value })}
                />
              </label>
            </div>
            {messages.map((message) => (
              <span key={message} className="text-[12px] text-danger" role="alert">
                {message}
              </span>
            ))}
            {rows.length > 1 && (
              <div>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => onChange(rows.filter((_, j) => j !== i))}
                >
                  {t('subjects.removeSchedule')}
                </Button>
              </div>
            )}
          </div>
        );
      })}
      {errors.schedules && (
        <span className="text-[12px] text-danger" role="alert">
          {errors.schedules}
        </span>
      )}
      <div>
        <Button type="button" size="sm" onClick={add}>
          {t('subjects.addSchedule')}
        </Button>
      </div>
    </fieldset>
  );
}
