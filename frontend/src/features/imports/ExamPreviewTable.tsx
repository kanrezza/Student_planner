import type { ExamRow } from '../../api/imports';
import { t } from '../../i18n/vi';
import { Badge } from '../../ui/Badge';
import { Checkbox } from '../../ui/Checkbox';
import { cx } from '../../ui/cx';
import { PreviewInput } from './PreviewCells';
import { confirmField, editField, endTimeNote, examProblems } from './previewState';

type Props = {
  rows: ExamRow[];
  onChange: (rows: ExamRow[]) => void;
  errors: Record<number, string[]>;
};

/**
 * Bảng xem trước lịch thi (US11, FR-059 đến FR-062): dòng đã qua hoặc đã có trong lịch mặc định
 * bỏ chọn; ô chưa chắc chắn tô vàng. Không có cột thông tin sinh viên (FR-061).
 */
export function ExamPreviewTable({ rows, onChange, errors }: Props) {
  const update = (index: number, next: ExamRow) =>
    onChange(rows.map((r, i) => (i === index ? next : r)));

  return (
    <ul className="flex flex-col gap-2">
      {rows.map((row, i) => {
        const f = row.fields;
        const set = (key: keyof ExamRow['fields']) => (value: string) =>
          update(i, editField(row, key, key === 'attempt' ? Number(value) || 1 : value || null));
        const confirm = (key: keyof ExamRow['fields']) => () => update(i, confirmField(row, key));
        const note = endTimeNote(row);
        return (
          <li
            key={i}
            data-testid="exam-import-row"
            className={cx(
              'rounded-xl border border-border bg-surface p-3',
              !row.selected && 'opacity-60',
            )}
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Checkbox
                checked={row.selected}
                onChange={(selected) => update(i, { ...row, selected })}
                label={t('import.selectRow')}
              />
              {row.is_past && <Badge>{t('import.past')}</Badge>}
              {row.duplicate_of_exam_id !== null && <Badge>{t('import.alreadyIn')}</Badge>}
              {row.duplicate_in_image && <Badge>{t('import.inImage')}</Badge>}
              {note && <Badge tone="accent">{t('import.endFromFormat', { format: note })}</Badge>}
              {(errors[i] ?? []).map((message) => (
                <span key={message} role="alert" className="text-[12px] text-danger">
                  {message}
                </span>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-6">
              <div className="col-span-2 sm:col-span-3">
                <PreviewInput
                  label={t('import.colCourse')}
                  field={f.course_name}
                  onChange={set('course_name')}
                  onConfirm={confirm('course_name')}
                />
              </div>
              <PreviewInput
                label={t('exams.fieldCode')}
                field={f.course_code}
                onChange={set('course_code')}
                onConfirm={confirm('course_code')}
                className="sm:col-span-2"
              />
              <PreviewInput
                label={t('import.colAttempt')}
                type="number"
                field={f.attempt}
                onChange={set('attempt')}
                onConfirm={confirm('attempt')}
              />
              <PreviewInput
                label={t('import.colDate')}
                type="date"
                field={f.date}
                onChange={set('date')}
                onConfirm={confirm('date')}
              />
              <PreviewInput
                label={t('exams.fieldStart')}
                type="time"
                field={f.start_time}
                onChange={set('start_time')}
                onConfirm={confirm('start_time')}
              />
              <PreviewInput
                label={t('exams.fieldEnd')}
                type="time"
                field={f.end_time}
                onChange={set('end_time')}
                onConfirm={confirm('end_time')}
              />
              <PreviewInput
                label={t('import.colFormat')}
                field={f.exam_format}
                onChange={set('exam_format')}
                onConfirm={confirm('exam_format')}
                className="sm:col-span-2"
              />
              <PreviewInput
                label={t('import.colRoom')}
                field={f.room}
                onChange={set('room')}
                onConfirm={confirm('room')}
              />
              <PreviewInput
                label={t('import.colCandidate')}
                field={f.candidate_number}
                onChange={set('candidate_number')}
                onConfirm={confirm('candidate_number')}
              />
            </div>
            {row.selected && examProblems(row).length > 0 && (
              <p className="mt-1 text-[12px] text-warning">{t('import.uncertainHelp')}</p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
