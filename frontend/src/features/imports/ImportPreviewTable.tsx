import { useState } from 'react';
import { DateInput } from '../../components/DateInput';
import type { ImportRow } from '../../api/imports';
import { useSemesters } from '../../api/semesters';
import { useShifts } from '../../api/shifts';
import { Modal } from '../../components/Modal';
import { t } from '../../i18n/vi';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { Checkbox } from '../../ui/Checkbox';
import { cx } from '../../ui/cx';
import { SemesterForm } from '../subjects/SemesterForm';
import { PreviewInput } from './PreviewCells';
import { confirmField, editField, setMerge, weekProblems } from './previewState';

type Props = {
  rows: ImportRow[];
  onChange: (rows: ImportRow[]) => void;
  /** Lỗi theo dòng từ API (`rows[i].field`). */
  errors: Record<number, string[]>;
  eLearning: Record<number, boolean>;
  onELearning: (index: number, on: boolean) => void;
};

/**
 * Bảng xem trước lịch học (US6, FR-030 đến FR-034): mỗi dòng một buổi, mọi ô sửa được, ô chưa chắc
 * chắn tô vàng, dòng đã có trong lịch mặc định bỏ chọn, dòng giống nhau gợi ý gộp.
 */
export function ImportPreviewTable({ rows, onChange, errors, eLearning, onELearning }: Props) {
  const semesters = useSemesters().data ?? [];
  const shifts = useShifts().data ?? [];
  const [creatingFor, setCreatingFor] = useState<number | null>(null);

  const update = (index: number, next: ImportRow) =>
    onChange(rows.map((r, i) => (i === index ? next : r)));

  const groups = [...new Set(rows.map((r) => r.merge_group).filter((g): g is string => !!g))];
  const shiftName = (row: ImportRow) =>
    row.shift ? shifts.find((s) => s.id === row.shift!.start_shift_id)?.name : null;

  return (
    <div className="flex flex-col gap-3">
      {groups.map((group) => {
        const members = rows.filter((r) => r.merge_group === group);
        const accepted = members.every((r) => r.merge_accepted);
        return (
          <div
            key={group}
            role="group"
            aria-label={t('import.mergeBar')}
            className="flex flex-wrap items-center gap-2 rounded-lg bg-accent-soft px-3 py-2 text-accent-strong"
          >
            <span className="min-w-0 flex-1">{t('import.mergeBar')}</span>
            <Button
              size="sm"
              variant={accepted ? 'primary' : 'secondary'}
              onClick={() => onChange(setMerge(rows, group, true))}
            >
              {t('import.merge')}
            </Button>
            <Button
              size="sm"
              variant={accepted ? 'secondary' : 'primary'}
              onClick={() => onChange(setMerge(rows, group, false))}
            >
              {t('import.keepSeparate')}
            </Button>
          </div>
        );
      })}

      <ul className="flex flex-col gap-2">
        {rows.map((row, i) => {
          const f = row.fields;
          const problems = weekProblems(row);
          const set = (key: keyof ImportRow['fields']) => (value: string) =>
            update(i, editField(row, key, value || null));
          const confirm = (key: keyof ImportRow['fields']) => () =>
            update(i, confirmField(row, key));
          return (
            <li
              key={i}
              data-testid="import-row"
              className={cx(
                'rounded-xl border bg-surface p-3',
                row.selected ? 'border-border' : 'border-border opacity-60',
              )}
            >
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Checkbox
                  checked={row.selected}
                  onChange={(selected) => update(i, { ...row, selected })}
                  label={t('import.selectRow')}
                />
                {row.duplicate_of_session_id !== null && <Badge>{t('import.alreadyIn')}</Badge>}
                {row.duplicate_in_image && <Badge>{t('import.inImage')}</Badge>}
                {shiftName(row) && <Badge tone="accent">{shiftName(row)}</Badge>}
                {row.shift_note && <Badge tone="warning">{row.shift_note}</Badge>}
                {row.suggested_tags.includes('e_learning') && (
                  <label className="flex items-center gap-1 text-[12px] text-muted">
                    <input
                      type="checkbox"
                      checked={eLearning[i] ?? true}
                      onChange={(e) => onELearning(i, e.target.checked)}
                    />
                    {t('import.eLearningTag')}
                  </label>
                )}
                {(errors[i] ?? []).map((message) => (
                  <span key={message} role="alert" className="text-[12px] text-danger">
                    {message}
                  </span>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-6">
                <div className="col-span-2 sm:col-span-3">
                  <PreviewInput
                    label={t('import.colName')}
                    field={f.name}
                    onChange={set('name')}
                    onConfirm={confirm('name')}
                  />
                </div>
                <PreviewInput
                  label={t('import.colDate')}
                  type="date"
                  field={f.date}
                  onChange={set('date')}
                  onConfirm={confirm('date')}
                />
                <PreviewInput
                  label={`${t('import.colTime')} (bắt đầu)`}
                  type="time"
                  field={f.start_time}
                  onChange={(v) =>
                    update(i, { ...editField(row, 'start_time', v || null), shift: null })
                  }
                  onConfirm={confirm('start_time')}
                />
                <PreviewInput
                  label={`${t('import.colTime')} (kết thúc)`}
                  type="time"
                  field={f.end_time}
                  onChange={(v) =>
                    update(i, { ...editField(row, 'end_time', v || null), shift: null })
                  }
                  onConfirm={confirm('end_time')}
                />
                <PreviewInput
                  label={t('import.colRoom')}
                  field={f.room}
                  onChange={set('room')}
                  onConfirm={confirm('room')}
                />
                <PreviewInput
                  label={t('import.colLecturer')}
                  field={f.lecturer}
                  onChange={set('lecturer')}
                  onConfirm={confirm('lecturer')}
                  className="sm:col-span-2"
                />
                <PreviewInput
                  label={t('import.colCode')}
                  field={f.class_code}
                  onChange={set('class_code')}
                  onConfirm={confirm('class_code')}
                  className="sm:col-span-2"
                />
                <div className="flex gap-1">
                  <select
                    aria-label={t('import.colSemester')}
                    value={row.semester_id ?? ''}
                    onChange={(e) => {
                      const id = e.target.value ? Number(e.target.value) : null;
                      const semester = semesters.find((s) => s.id === id);
                      update(i, {
                        ...row,
                        semester_id: id,
                        repeat: {
                          mode: semester ? row.repeat.mode : 'once',
                          until: semester ? semester.end_date : row.repeat.until,
                        },
                      });
                    }}
                    className={cx(
                      'h-8 min-w-0 flex-1',
                      row.semester_id === null && 'border-danger bg-danger-soft',
                    )}
                  >
                    <option value="">{t('import.noSemester')}</option>
                    {semesters.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>
                {row.semester_id === null && (
                  <Button size="sm" onClick={() => setCreatingFor(i)}>
                    {t('import.createSemester')}
                  </Button>
                )}
                <div className="col-span-2 flex items-center gap-2 sm:col-span-3">
                  <select
                    aria-label={t('import.colRepeat')}
                    value={row.repeat.mode}
                    onChange={(e) =>
                      update(i, {
                        ...row,
                        repeat: { ...row.repeat, mode: e.target.value as 'once' | 'weekly' },
                      })
                    }
                    className="h-8 w-auto"
                  >
                    <option value="once">{t('import.repeatOnce')}</option>
                    <option value="weekly">{t('import.repeatWeekly')}</option>
                  </select>
                  {row.repeat.mode === 'weekly' && (
                    <DateInput
                      label={t('import.repeatWeekly')}
                      value={row.repeat.until ?? ''}
                      onChange={(v) =>
                        update(i, {
                          ...row,
                          repeat: { ...row.repeat, until: v || null },
                        })
                      }
                      className="h-8 w-auto"
                    />
                  )}
                </div>
              </div>
              {row.selected && problems.length > 0 && (
                <p className="mt-1 text-[12px] text-warning">{t('import.uncertainHelp')}</p>
              )}
            </li>
          );
        })}
      </ul>

      {creatingFor !== null && (
        <Modal title={t('import.createSemester')} onClose={() => setCreatingFor(null)}>
          <SemesterForm
            onCancel={() => setCreatingFor(null)}
            onDone={(semester) => {
              update(creatingFor, {
                ...rows[creatingFor],
                semester_id: semester.id,
                repeat: { mode: 'weekly', until: semester.end_date },
              });
              setCreatingFor(null);
            }}
          />
        </Modal>
      )}
    </div>
  );
}
