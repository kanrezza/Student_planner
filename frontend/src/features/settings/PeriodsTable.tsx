import { useState } from 'react';
import { ApiError } from '../../api/client';
import {
  useDeletePeriod,
  usePeriods,
  useResetPeriod,
  useSavePeriod,
  type Period,
} from '../../api/periods';
import { useShifts } from '../../api/shifts';
import { fieldError } from '../../components/FormField';
import { t } from '../../i18n/vi';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';

/** Bảng tiết trong Cài đặt → Ca học (feature 004, FR-011…FR-015): giờ từng tiết, sửa tay được. */
export function PeriodsTable() {
  const periods = usePeriods();
  const shifts = useShifts();
  const save = useSavePeriod();
  const reset = useResetPeriod();
  const remove = useDeletePeriod();
  const [draft, setDraft] = useState({ number: '', start_time: '', end_time: '' });
  const [notice, setNotice] = useState<string | null>(null);
  const shiftName = (id: number | null) => shifts.data?.find((s) => s.id === id)?.name ?? '—';

  function put(number: number, start_time: string, end_time: string, done?: () => void) {
    setNotice(null);
    save.mutate(
      { number, start_time, end_time },
      {
        onSuccess: (result) => {
          done?.();
          if (result.warnings.length) setNotice(result.warnings.map((w) => w.message).join(' '));
        },
      },
    );
  }

  const draftNumber = Number(draft.number);
  const addError = save.error instanceof ApiError && save.variables?.number === draftNumber;

  return (
    <section aria-label={t('periods.title')} className="mt-5">
      <h3 className="text-[14px] font-semibold">{t('periods.title')}</h3>
      <p className="mb-2 text-[12px] text-muted">{t('periods.note')}</p>
      <table className="w-full border-separate border-spacing-x-0 border-spacing-y-1">
        <thead className="text-left text-[12px] font-medium text-muted">
          <tr>
            <th>{t('periods.number')}</th>
            <th>{t('subjects.fieldStartTime')}</th>
            <th>{t('subjects.fieldEndTime')}</th>
            <th>{t('periods.shift')}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {periods.data?.map((period) => (
            <PeriodRow
              key={`${period.number}-${period.start_time}-${period.end_time}`}
              period={period}
              shift={shiftName(period.shift_id)}
              error={save.variables?.number === period.number ? save.error : null}
              onSave={(start, end) => put(period.number, start, end)}
              onReset={() => reset.mutate(period.number)}
              onDelete={() => remove.mutate(period.number)}
            />
          ))}
          <tr>
            <td className="pr-2">
              <input
                type="number"
                min={13}
                max={30}
                aria-label={t('periods.newNumber')}
                placeholder="13"
                className="w-20"
                value={draft.number}
                onChange={(e) => setDraft({ ...draft, number: e.target.value })}
              />
            </td>
            <td className="pr-2">
              <input
                type="time"
                aria-label={`${t('subjects.fieldStartTime')} ${t('periods.new')}`}
                value={draft.start_time}
                onChange={(e) => setDraft({ ...draft, start_time: e.target.value })}
              />
            </td>
            <td className="pr-2">
              <input
                type="time"
                aria-label={`${t('subjects.fieldEndTime')} ${t('periods.new')}`}
                value={draft.end_time}
                onChange={(e) => setDraft({ ...draft, end_time: e.target.value })}
              />
            </td>
            <td />
            <td className="pl-2">
              <Button
                size="sm"
                variant="primary"
                onClick={() =>
                  put(draftNumber, draft.start_time, draft.end_time, () =>
                    setDraft({ number: '', start_time: '', end_time: '' }),
                  )
                }
              >
                {t('periods.add')}
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
      {addError && (
        <p role="alert" className="text-[12px] text-danger">
          {Object.values((save.error as ApiError).fields)[0] ?? (save.error as ApiError).message}
        </p>
      )}
      {notice && (
        <p role="status" className="text-[12px] text-warning">
          {notice}
        </p>
      )}
    </section>
  );
}

function PeriodRow({
  period,
  shift,
  error,
  onSave,
  onReset,
  onDelete,
}: {
  period: Period;
  shift: string;
  error: Error | null;
  onSave: (start: string, end: string) => void;
  onReset: () => void;
  onDelete: () => void;
}) {
  const [start, setStart] = useState(period.start_time);
  const [end, setEnd] = useState(period.end_time);
  const changed = start !== period.start_time || end !== period.end_time;
  const message = fieldError(error, 'end_time') ?? fieldError(error, 'start_time');
  return (
    <tr>
      <td className="pr-2 tabular-nums">
        {period.number}
        {period.is_manual && (
          <Badge tone="warning" className="ml-1">
            {t('periods.manual')}
          </Badge>
        )}
      </td>
      <td className="pr-2">
        <input
          type="time"
          aria-label={`${t('subjects.fieldStartTime')} ${period.number}`}
          value={start}
          onChange={(e) => setStart(e.target.value)}
        />
      </td>
      <td className="pr-2">
        <input
          type="time"
          aria-label={`${t('subjects.fieldEndTime')} ${period.number}`}
          value={end}
          onChange={(e) => setEnd(e.target.value)}
        />
        {message && (
          <div role="alert" className="text-[12px] text-danger">
            {message}
          </div>
        )}
      </td>
      <td className="pr-2 text-muted">{shift}</td>
      <td className="whitespace-nowrap pl-2">
        <Button size="sm" disabled={!changed} onClick={() => onSave(start, end)}>
          {t('common.save')}
        </Button>
        {period.is_manual && (
          <Button
            size="sm"
            variant="ghost"
            aria-label={`${t('periods.reset')} ${period.number}`}
            onClick={onReset}
          >
            {t('periods.reset')}
          </Button>
        )}
        {period.shift_id === null && (
          <Button
            size="sm"
            variant="ghost"
            aria-label={`${t('common.delete')} ${period.number}`}
            onClick={onDelete}
          >
            {t('common.delete')}
          </Button>
        )}
      </td>
    </tr>
  );
}
