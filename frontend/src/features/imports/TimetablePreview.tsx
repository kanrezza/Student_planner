import { useSemesters } from '../../api/semesters';
import type { PreviewSchedule } from '../../api/timetableImport';
import { DateInput } from '../../components/DateInput';
import { t } from '../../i18n/vi';
import { formatDate } from '../../lib/dates';
import { Badge } from '../../ui/Badge';
import { Checkbox } from '../../ui/Checkbox';
import { cx } from '../../ui/cx';
import { Notice } from '../../ui/layout';
import { ShiftPicker } from '../subjects/ShiftPicker';
import {
  patchSchedule,
  patchSubject,
  ruleProblems,
  toggleSubject,
  type TimetableState,
} from './timetablePreviewState';

const STATUS_TONE = { new: 'accent', unchanged: 'neutral', changed: 'warning' } as const;

function cellTone(rule: PreviewSchedule, fields: string[]) {
  const problems = ruleProblems(rule).filter((p) => fields.includes(p.field));
  if (problems.some((p) => p.level === 'error'))
    return {
      cls: 'border-danger bg-danger-soft',
      title: problems.map((p) => p.message).join('; '),
    };
  if (problems.length)
    return {
      cls: 'border-warning bg-warning-soft',
      title: problems.map((p) => p.message).join('; '),
    };
  return { cls: '', title: undefined };
}

/**
 * Bản xem trước thời khoá biểu PDF (feature 004, FR-016 đến FR-019): dải học kỳ, khối từng môn và
 * bảng quy tắc lặp, mọi ô sửa được. Không hiển thị gì ngoài bảng (không họ tên, mã sinh viên).
 */
export function TimetablePreview({
  state,
  onChange,
}: {
  state: TimetableState;
  onChange: (next: TimetableState) => void;
}) {
  const semesters = useSemesters().data ?? [];
  const { semester } = state;
  const range = `${formatDate(semester.start_date)} – ${formatDate(semester.end_date)}`;
  const containing = semesters.filter(
    (s) =>
      s.start_date <= semester.start_date &&
      semester.end_date <= s.end_date &&
      !(semester.choice === 'use' && s.id === semester.semester_id),
  );

  function chooseSemester(value: string) {
    if (value === 'create') {
      onChange({
        ...state,
        semester: { ...semester, choice: 'create', semester_id: undefined, conflicts: undefined },
      });
      return;
    }
    const existing = semesters.find((s) => String(s.id) === value);
    if (existing) {
      onChange({
        ...state,
        semester: {
          ...semester,
          choice: 'use',
          semester_id: existing.id,
          name: existing.name,
          conflicts: undefined,
        },
      });
    }
  }

  const selectValue = semester.choice === 'create' ? 'create' : String(semester.semester_id ?? '');
  const label =
    semester.choice === 'create'
      ? t('timetable.semesterNew')
      : semester.choice === 'extend'
        ? t('timetable.semesterExtend')
        : semester.choice === 'use'
          ? t('timetable.semesterUse')
          : '';

  return (
    <div className="flex flex-col gap-4">
      <section
        aria-label={t('timetable.semester')}
        className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2"
      >
        <span className="font-medium">{t('timetable.semester')}:</span>
        {semester.choice === 'create' ? (
          <input
            aria-label={t('timetable.semesterName')}
            value={state.semesterName}
            onChange={(e) => onChange({ ...state, semesterName: e.target.value })}
            className="h-8 w-[200px] px-2"
          />
        ) : (
          <span>{semester.name}</span>
        )}
        {label && <Badge tone="accent">{label}</Badge>}
        <span className="tabular-nums text-muted">· {range}</span>
        {semester.choice !== 'conflict' && (semesters.length > 0 || containing.length > 0) && (
          <select
            aria-label={t('timetable.changeSemester')}
            value={selectValue}
            onChange={(e) => chooseSemester(e.target.value)}
            className="ml-auto"
          >
            <option value="create">{t('timetable.createNew')}</option>
            {semester.choice !== 'create' && semester.semester_id !== undefined && (
              <option value={String(semester.semester_id)}>{semester.name}</option>
            )}
            {containing.map((s) => (
              <option key={s.id} value={String(s.id)}>
                {s.name}
              </option>
            ))}
          </select>
        )}
      </section>

      {semester.choice === 'conflict' && (
        <Notice tone="danger">
          {t('timetable.conflict', {
            names: (semester.conflicts ?? []).map((c) => c.name).join(', '),
          })}
        </Notice>
      )}

      {state.subjects.map((subject, si) => (
        <section
          key={`${subject.course_code}-${subject.class_code}-${si}`}
          aria-label={subject.name}
          className={cx(
            'rounded-lg border border-border bg-surface p-3',
            !subject.selected && 'opacity-60',
          )}
        >
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Checkbox
              checked={subject.selected}
              label={t('timetable.selectSubject', { name: subject.name })}
              onChange={(on) => onChange(toggleSubject(state, si, on))}
            />
            <input
              aria-label={t('timetable.subjectName')}
              value={subject.name}
              onChange={(e) => onChange(patchSubject(state, si, { name: e.target.value }))}
              className="h-8 min-w-[220px] flex-1 px-2 font-medium"
            />
            <Badge tone={STATUS_TONE[subject.status]}>
              {t(`timetable.status.${subject.status}`)}
            </Badge>
            {subject.suggested_tags.includes('e_learning') && (
              <label className="flex items-center gap-1 text-[12px]">
                <input
                  type="checkbox"
                  checked={subject.eLearning}
                  onChange={(e) =>
                    onChange(patchSubject(state, si, { eLearning: e.target.checked }))
                  }
                />
                {t('import.eLearningTag')}
              </label>
            )}
          </div>
          <p className="mb-2 text-[12px] text-muted">
            {[subject.course_code, subject.class_code].filter(Boolean).join(' · ')}
            {subject.credits !== null && ` · ${t('timetable.credits', { count: subject.credits })}`}
          </p>
          {subject.diff.length > 0 && (
            <ul className="mb-2 text-[12px] text-muted">
              {subject.diff.map((d) => (
                <li key={d.field}>
                  {d.field}: {d.before ?? '—'} → {d.after ?? '—'}
                </li>
              ))}
            </ul>
          )}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-[13px]">
              <thead>
                <tr className="text-left text-[12px] text-muted">
                  <th className="w-8" />
                  <th>{t('timetable.colWeekday')}</th>
                  <th>{t('subjects.fieldStartDate')}</th>
                  <th>{t('subjects.fieldEndDate')}</th>
                  <th>{t('timetable.colPeriods')}</th>
                  <th>{t('timetable.colTime')}</th>
                  <th>{t('subjects.fieldRoom')}</th>
                  <th className="text-right">{t('timetable.colSessions')}</th>
                </tr>
              </thead>
              <tbody>
                {subject.schedules.map((rule, ri) => {
                  const dates = cellTone(rule, ['start_date', 'end_date']);
                  const time = cellTone(rule, ['start_time', 'end_time', 'period_from']);
                  const room = cellTone(rule, ['room']);
                  const patch = (p: Partial<PreviewSchedule>) =>
                    onChange(patchSchedule(state, si, ri, p));
                  return (
                    <tr key={ri} className={cx(!rule.selected && 'opacity-50')}>
                      <td>
                        <Checkbox
                          checked={rule.selected}
                          label={t('timetable.selectRule', { n: ri + 1 })}
                          onChange={(on) => patch({ selected: on })}
                        />
                      </td>
                      <td>
                        <select
                          aria-label={t('timetable.colWeekday')}
                          value={rule.weekday}
                          onChange={(e) => patch({ weekday: Number(e.target.value) })}
                        >
                          {[1, 2, 3, 4, 5, 6, 7].map((d) => (
                            <option key={d} value={d}>
                              {t(`weekdaysShort.${d}`)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td title={dates.title}>
                        <DateInput
                          label={t('subjects.fieldStartDate')}
                          value={rule.start_date ?? ''}
                          onChange={(v) => patch({ start_date: v || null })}
                          className={cx('h-8', dates.cls)}
                        />
                      </td>
                      <td title={dates.title}>
                        <DateInput
                          label={t('subjects.fieldEndDate')}
                          value={rule.end_date ?? ''}
                          onChange={(v) => patch({ end_date: v || null })}
                          className={cx('h-8', dates.cls)}
                        />
                      </td>
                      <td className="tabular-nums">
                        {rule.period_from === null
                          ? '—'
                          : rule.period_from === rule.period_to
                            ? rule.period_from
                            : `${rule.period_from}–${rule.period_to}`}
                      </td>
                      <td title={time.title} className={cx('rounded', time.cls)}>
                        {rule.needsPeriods && (
                          <div className="text-[11px] text-warning">
                            {t('timetable.missingPeriods', {
                              periods:
                                rule.period_from === rule.period_to
                                  ? String(rule.period_from)
                                  : `${rule.period_from}–${rule.period_to}`,
                            })}
                          </div>
                        )}
                        <ShiftPicker
                          compact
                          label={t('timetable.colTime')}
                          value={{
                            shift: rule.shift,
                            start_time: rule.start_time ?? '',
                            end_time: rule.end_time ?? '',
                          }}
                          onChange={(c) =>
                            patch({
                              shift: c.shift,
                              start_time: c.start_time || null,
                              end_time: c.end_time || null,
                            })
                          }
                        />
                        {rule.needsPeriods && (
                          <label className="mt-1 flex items-center gap-1 text-[11px]">
                            <input
                              type="checkbox"
                              checked={!!rule.savePeriods}
                              onChange={(e) => patch({ savePeriods: e.target.checked })}
                            />
                            {t('timetable.savePeriods')}
                          </label>
                        )}
                      </td>
                      <td title={room.title}>
                        <input
                          aria-label={t('subjects.fieldRoom')}
                          value={rule.room ?? ''}
                          onChange={(e) => patch({ room: e.target.value || null })}
                          className={cx('h-8 w-full min-w-[110px] px-2', room.cls)}
                        />
                      </td>
                      <td className="text-right tabular-nums">{rule.session_count}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {subject.schedules.flatMap((r, ri) =>
            ruleProblems(r)
              .filter((p) => p.level === 'error')
              .map((p) => (
                <p key={`${ri}-${p.field}`} role="alert" className="mt-1 text-[12px] text-danger">
                  {t('timetable.ruleError', { n: ri + 1, message: p.message })}
                </p>
              )),
          )}
        </section>
      ))}
    </div>
  );
}
