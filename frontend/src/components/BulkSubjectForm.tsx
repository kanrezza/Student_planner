import { useState, type FormEvent } from 'react';
import { useCreateBulk, type BulkResult } from '../api/subjects';
import { ApiError, type ApiWarning } from '../api/client';
import type { Semester } from '../api/types';
import { t } from '../i18n/vi';
import { blankToNull } from '../lib/format';
import { FormField, fieldError } from './FormField';
import { FormActions } from './TaskForm';
import { WeekdayPicker } from './WeekdayPicker';

type Row = {
  key: number;
  name: string;
  weekdays: number[];
  start_time: string;
  end_time: string;
  room: string;
  class_code: string;
  lecturer: string;
};

const COLUMN_LABELS = {
  name: 'subjects.fieldName',
  start_time: 'subjects.fieldStartTime',
  end_time: 'subjects.fieldEndTime',
  room: 'subjects.fieldRoom',
  class_code: 'subjects.fieldClassCode',
  lecturer: 'subjects.fieldLecturer',
} as const;

let nextKey = 1;
const emptyRow = (): Row => ({
  key: nextKey++,
  name: '',
  weekdays: [],
  start_time: '',
  end_time: '',
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
    const filled = rows.filter((r) => r.name.trim() || r.weekdays.length || r.start_time);
    bulk.mutate(
      {
        semester_id: semesterId,
        start_date: startDate || null,
        end_date: endDate || null,
        rows: filled.map((r) => ({
          name: r.name.trim(),
          weekdays: r.weekdays,
          start_time: r.start_time || null,
          end_time: r.end_time || null,
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
      <div className="form-row">
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
      </div>
      <p className="muted">{t('subjects.sharedDates')}</p>

      <div className="bulk-table">
        <div className="bulk-table__head">
          <span>{t('subjects.fieldName')}</span>
          <span>{t('subjects.fieldWeekdays')}</span>
          <span>{t('subjects.fieldStartTime')}</span>
          <span>{t('subjects.fieldEndTime')}</span>
          <span>{t('subjects.fieldRoom')}</span>
          <span>{t('subjects.fieldClassCode')}</span>
          <span>{t('subjects.fieldLecturer')}</span>
          <span />
        </div>
        {rows.map((row, i) => (
          <div className="bulk-table__row" key={row.key}>
            {(
              [
                ['name', 'text'],
                ['weekdays', 'weekdays'],
                ['start_time', 'time'],
                ['end_time', 'time'],
                ['room', 'text'],
                ['class_code', 'text'],
                ['lecturer', 'text'],
              ] as const
            ).map(([field, kind]) => {
              const message = cellError(i, field);
              return (
                <div key={field} className={`bulk-cell${message ? ' field--error' : ''}`}>
                  {kind === 'weekdays' ? (
                    <WeekdayPicker
                      value={row.weekdays}
                      onChange={(days) => updateRow(i, { weekdays: days })}
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
                    <span className="field__error" role="alert">
                      {message}
                    </span>
                  )}
                </div>
              );
            })}
            <button
              type="button"
              className="button--ghost"
              aria-label={t('subjects.removeRow')}
              disabled={rows.length === 1}
              onClick={() => setRows((prev) => prev.filter((_, j) => j !== i))}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
      <button type="button" onClick={() => setRows((prev) => [...prev, emptyRow()])}>
        {t('subjects.addRow')}
      </button>
      {generalError && <p className="field__error">{generalError}</p>}
      <FormActions saving={bulk.isPending} onCancel={() => onDone()} />
    </form>
  );
}
