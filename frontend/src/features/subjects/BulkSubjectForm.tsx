import { useState, type FormEvent } from 'react';
import { useCreateBulk, type BulkResult } from '../../api/subjects';
import { ApiError, type ApiWarning } from '../../api/client';
import type { Semester } from '../../api/types';
import { t } from '../../i18n/vi';
import { blankToNull } from '../../lib/format';
import { FormField, FormRow, fieldError } from '../../components/FormField';
import { Button } from '../../ui/Button';
import { cx } from '../../ui/cx';
import { IconButton } from '../../ui/IconButton';
import { IconClose } from '../../ui/icons';
import { ShiftPicker, timeChoiceToInput, type TimeChoice } from './ShiftPicker';
import { FormActions } from '../../components/FormActions';
import { WeekdayPicker } from './WeekdayPicker';

type Row = {
  key: number;
  name: string;
  weekdays: number[];
  time: TimeChoice;
  room: string;
  class_code: string;
  lecturer: string;
};

const COLUMN_LABELS = {
  name: 'subjects.fieldName',
  room: 'subjects.fieldRoom',
  class_code: 'subjects.fieldClassCode',
  lecturer: 'subjects.fieldLecturer',
} as const;

/** Cột của bảng nhập nhiều môn. */
const GRID =
  'grid min-w-[880px] grid-cols-[minmax(140px,1.4fr)_auto_minmax(150px,1fr)_minmax(80px,0.7fr)_minmax(80px,0.7fr)_minmax(110px,1fr)_28px] gap-2';

let nextKey = 1;
const emptyRow = (): Row => ({
  key: nextKey++,
  name: '',
  weekdays: [],
  time: { shift: null, start_time: '', end_time: '' },
  room: '',
  class_code: '',
  lecturer: '',
});

/**
 * Nhập nhiều môn trong một lần (FR-009): các môn dùng chung học kỳ và khoảng ngày (mặc định cả học
 * kỳ). Lỗi của dòng nào hiện đúng ô của dòng đó; dữ liệu các dòng khác được giữ nguyên (FR-010).
 */
export function BulkSubjectForm({
  semesters,
  defaultSemesterId,
  onDone,
}: {
  semesters: Semester[];
  defaultSemesterId: number;
  onDone: (result?: BulkResult, warnings?: ApiWarning[]) => void;
}) {
  const [semesterId, setSemesterId] = useState(defaultSemesterId);
  const semester = semesters.find((s) => s.id === semesterId);
  const [startDate, setStartDate] = useState(semester?.start_date ?? '');
  const [endDate, setEndDate] = useState(semester?.end_date ?? '');
  const [rows, setRows] = useState<Row[]>([emptyRow(), emptyRow(), emptyRow()]);
  const bulk = useCreateBulk();
  const error = bulk.error;

  function changeSemester(id: number) {
    const next = semesters.find((s) => s.id === id);
    setSemesterId(id);
    if (next) {
      setStartDate(next.start_date);
      setEndDate(next.end_date);
    }
  }

  function updateRow(index: number, patch: Partial<Row>) {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    // Bỏ qua dòng trống hoàn toàn để người dùng không phải xoá các dòng thừa.
    const filled = rows.filter(
      (r) => r.name.trim() || r.weekdays.length || r.time.shift || r.time.start_time,
    );
    bulk.mutate(
      {
        semester_id: semesterId,
        start_date: startDate || null,
        end_date: endDate || null,
        rows: filled.map((r) => ({
          name: r.name.trim(),
          weekdays: r.weekdays,
          ...timeChoiceToInput(r.time),
          room: blankToNull(r.room),
          class_code: blankToNull(r.class_code),
          lecturer: blankToNull(r.lecturer),
        })),
      },
      {
        onSuccess: (result) => onDone(result.data, result.warnings),
        onError: () => {
          // Lỗi trả theo chỉ số trong `filled`; nếu có dòng trống ở giữa thì bỏ hẳn chúng khỏi bảng
          // để chỉ số khớp với dòng hiển thị.
          if (filled.length !== rows.length) setRows(filled.length ? filled : [emptyRow()]);
        },
      },
    );
  }

  const cellError = (i: number, field: string) => fieldError(error, `rows[${i}].${field}`);
  const generalError =
    error instanceof ApiError && Object.keys(error.fields).length === 0 ? error.message : undefined;

  return (
    <form onSubmit={submit} noValidate>
      <FormRow>
        <FormField label={t('subjects.semester')} name="semester_id" error={error}>
          <select value={semesterId} onChange={(e) => changeSemester(Number(e.target.value))}>
            {semesters.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label={t('subjects.fieldStartDate')} name="start_date" error={error}>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </FormField>
        <FormField label={t('subjects.fieldEndDate')} name="end_date" error={error}>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </FormField>
      </FormRow>
      <p className="-mt-1 mb-3 text-[12px] text-muted">{t('subjects.sharedDates')}</p>

      <div className="overflow-x-auto">
        <div className={cx(GRID, 'pb-1 text-[12px] font-medium text-muted')}>
          <span>{t('subjects.fieldName')}</span>
          <span>{t('subjects.fieldWeekdays')}</span>
          <span>{t('shifts.pick')}</span>
          <span>{t('subjects.fieldRoom')}</span>
          <span>{t('subjects.fieldClassCode')}</span>
          <span>{t('subjects.fieldLecturer')}</span>
          <span />
        </div>
        {rows.map((row, i) => (
          <div className={cx(GRID, 'items-start border-t border-border py-2')} key={row.key}>
            {(
              [
                ['name', 'text'],
                ['weekdays', 'weekdays'],
                ['time', 'shift'],
                ['room', 'text'],
                ['class_code', 'text'],
                ['lecturer', 'text'],
              ] as const
            ).map(([field, kind]) => {
              const message =
                field === 'time'
                  ? (cellError(i, 'shift') ??
                    cellError(i, 'start_time') ??
                    cellError(i, 'end_time'))
                  : cellError(i, field);
              return (
                <div key={field} className="flex min-w-0 flex-col gap-1">
                  {kind === 'weekdays' ? (
                    <WeekdayPicker
                      value={row.weekdays}
                      onChange={(days) => updateRow(i, { weekdays: days })}
                    />
                  ) : kind === 'shift' ? (
                    <ShiftPicker
                      compact
                      label={`${t('shifts.pick')} – dòng ${i + 1}`}
                      value={row.time}
                      onChange={(time) => updateRow(i, { time })}
                    />
                  ) : (
                    <input
                      type={kind}
                      aria-label={`${t(COLUMN_LABELS[field])} – dòng ${i + 1}`}
                      value={row[field]}
                      onChange={(e) => updateRow(i, { [field]: e.target.value })}
                    />
                  )}
                  {message && (
                    <span className="text-[12px] text-danger" role="alert">
                      {message}
                    </span>
                  )}
                </div>
              );
            })}
            <IconButton
              label={t('subjects.removeRow')}
              icon={<IconClose size={14} />}
              disabled={rows.length === 1}
              onClick={() => setRows((prev) => prev.filter((_, j) => j !== i))}
            />
          </div>
        ))}
      </div>
      <Button size="sm" className="mt-2" onClick={() => setRows((prev) => [...prev, emptyRow()])}>
        {t('subjects.addRow')}
      </Button>
      {generalError && <p className="mt-2 text-[12px] text-danger">{generalError}</p>}
      <FormActions saving={bulk.isPending} onCancel={() => onDone()} />
    </form>
  );
}
