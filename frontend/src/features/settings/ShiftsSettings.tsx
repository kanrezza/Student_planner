import { useState } from 'react';
import { ApiError } from '../../api/client';
import { useDeleteShift, useSaveShift, useShifts, type ShiftInput } from '../../api/shifts';
import type { Shift } from '../../api/types';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { fieldError } from '../../components/FormField';
import { t } from '../../i18n/vi';
import { Button } from '../../ui/Button';
import { Card } from '../../ui/layout';
import { PeriodsTable } from './PeriodsTable';

type Pending =
  | { kind: 'change'; shift: Shift; input: ShiftInput; count: number }
  | { kind: 'delete'; shift: Shift; count?: number };

/** Bảng ca học trong Cài đặt (US8, FR-038, FR-040): sửa giờ, thêm, xoá ca. */
export function ShiftsSettings() {
  const shifts = useShifts();
  const save = useSaveShift();
  const remove = useDeleteShift();
  const [pending, setPending] = useState<Pending | null>(null);
  const [draft, setDraft] = useState<ShiftInput>({ name: '', start_time: '', end_time: '' });

  function saveRow(shift: Shift, input: ShiftInput, confirm = false) {
    save.mutate(
      { id: shift.id, input, confirm },
      {
        onError: (err) => {
          if (err instanceof ApiError && err.status === 409) {
            const count = (err.details as { subject_count: number }).subject_count;
            setPending({ kind: 'change', shift, input, count });
          }
        },
      },
    );
  }

  function deleteShift(shift: Shift, confirm: boolean) {
    remove.mutate(
      { id: shift.id, confirm },
      {
        onSuccess: () => setPending(null),
        onError: (err) => {
          if (err instanceof ApiError && err.status === 409) {
            const count = (err.details as { subject_count: number }).subject_count;
            setPending({ kind: 'delete', shift, count });
          }
        },
      },
    );
  }

  function confirmPending() {
    if (!pending) return;
    if (pending.kind === 'change') {
      saveRow(pending.shift, pending.input, true);
      setPending(null);
    } else {
      deleteShift(pending.shift, pending.count !== undefined);
    }
  }

  const createError = save.error instanceof ApiError && !save.variables?.id ? save.error : null;

  return (
    <Card title={t('shifts.title')}>
      <table className="w-full border-separate border-spacing-x-0 border-spacing-y-1.5">
        <thead className="text-left text-[12px] font-medium text-muted">
          <tr>
            <th>{t('shifts.fieldName')}</th>
            <th>{t('subjects.fieldStartTime')}</th>
            <th>{t('subjects.fieldEndTime')}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {shifts.data?.map((shift) => (
            <ShiftRow
              key={`${shift.id}-${shift.start_time}-${shift.end_time}-${shift.name}`}
              shift={shift}
              error={save.variables?.id === shift.id ? save.error : null}
              onSave={(input) => saveRow(shift, input)}
              onDelete={() => setPending({ kind: 'delete', shift })}
            />
          ))}
          <tr>
            <td className="pr-2">
              <input
                aria-label={t('shifts.fieldName')}
                placeholder="Ca 5"
                value={draft.name}
                onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              />
            </td>
            <td className="pr-2">
              <input
                type="time"
                aria-label={t('subjects.fieldStartTime')}
                value={draft.start_time}
                onChange={(e) => setDraft({ ...draft, start_time: e.target.value })}
              />
            </td>
            <td className="pr-2">
              <input
                type="time"
                aria-label={t('subjects.fieldEndTime')}
                value={draft.end_time}
                onChange={(e) => setDraft({ ...draft, end_time: e.target.value })}
              />
            </td>
            <td className="pl-2">
              <Button
                variant="primary"
                size="sm"
                onClick={() =>
                  save.mutate(
                    { input: draft },
                    { onSuccess: () => setDraft({ name: '', start_time: '', end_time: '' }) },
                  )
                }
              >
                {t('shifts.add')}
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
      {createError && (
        <p className="text-[12px] text-danger" role="alert">
          {Object.values(createError.fields)[0] ?? createError.message}
        </p>
      )}
      <PeriodsTable />
      <ConfirmDialog
        open={pending !== null}
        title={pending?.kind === 'change' ? t('shifts.title') : t('confirm.deleteTitle')}
        message={
          pending?.kind === 'change'
            ? t('shifts.confirmChange', { count: pending.count })
            : pending?.count !== undefined
              ? t('shifts.confirmDelete', { name: pending.shift.name, count: pending.count })
              : t('shifts.deleteConfirm', { name: pending?.shift.name ?? '' })
        }
        confirmLabel={pending?.kind === 'change' ? t('confirm.continue') : t('confirm.delete')}
        onCancel={() => setPending(null)}
        onConfirm={() =>
          pending?.kind === 'delete' && pending.count === undefined
            ? deleteShift(pending.shift, false)
            : confirmPending()
        }
      />
    </Card>
  );
}

function ShiftRow({
  shift,
  error,
  onSave,
  onDelete,
}: {
  shift: Shift;
  error: Error | null;
  onSave: (input: ShiftInput) => void;
  onDelete: () => void;
}) {
  const [input, setInput] = useState<ShiftInput>({
    name: shift.name,
    start_time: shift.start_time,
    end_time: shift.end_time,
  });
  const changed =
    input.name !== shift.name ||
    input.start_time !== shift.start_time ||
    input.end_time !== shift.end_time;
  const message = fieldError(error, 'end_time') ?? fieldError(error, 'name');
  return (
    <tr>
      <td className="pr-2">
        <input
          aria-label={t('shifts.fieldName')}
          value={input.name}
          onChange={(e) => setInput({ ...input, name: e.target.value })}
        />
      </td>
      <td className="pr-2">
        <input
          type="time"
          aria-label={t('subjects.fieldStartTime')}
          value={input.start_time}
          onChange={(e) => setInput({ ...input, start_time: e.target.value })}
        />
      </td>
      <td className="pr-2">
        <input
          type="time"
          aria-label={t('subjects.fieldEndTime')}
          value={input.end_time}
          onChange={(e) => setInput({ ...input, end_time: e.target.value })}
        />
        {message && <div className="text-[12px] text-danger">{message}</div>}
      </td>
      <td className="whitespace-nowrap pl-2">
        <Button size="sm" disabled={!changed} onClick={() => onSave(input)}>
          {t('common.save')}
        </Button>
        <Button size="sm" variant="ghost" onClick={onDelete}>
          {t('common.delete')}
        </Button>
      </td>
    </tr>
  );
}
