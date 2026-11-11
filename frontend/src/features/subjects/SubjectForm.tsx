import { useState, type FormEvent } from 'react';
import { useSettings } from '../../api/settings';
import { minutesLabel, ReminderSelect } from '../../components/ReminderSelect';
import { ApiError } from '../../api/client';
import { useSaveSubject, type SubjectSaveResult } from '../../api/subjects';
import type { Semester, Subject } from '../../api/types';
import { t } from '../../i18n/vi';
import { formatDate } from '../../lib/dates';
import { blankToNull } from '../../lib/format';
import { ColorPicker } from '../../components/ColorPicker';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { FormField, FormRow } from '../../components/FormField';
import { ImportantToggle } from '../../components/ImportantToggle';
import { blankRow, rowToInput, ScheduleRows, type ScheduleRow } from './ScheduleRows';
import { TagPicker } from '../../components/TagPicker';
import { FormActions } from '../../components/FormActions';

type ExceptionConflict = { id: number; date: string };

/**
 * Thêm hoặc sửa một môn học (FR-007). Ngày mặc định theo học kỳ. Khi sửa mà buổi đã huỷ/sửa riêng
 * nằm ngoài lịch mới, hỏi lại trước khi xoá chúng (FR-013).
 */
export function SubjectForm({
  subject,
  semesters,
  defaultSemesterId,
  onDone,
}: {
  subject?: Subject;
  semesters: Semester[];
  defaultSemesterId: number;
  onDone: (result?: SubjectSaveResult, warnings?: { code: string; message: string }[]) => void;
}) {
  const [semesterId, setSemesterId] = useState(subject?.semester_id ?? defaultSemesterId);
  const semester = semesters.find((s) => s.id === semesterId);
  const [form, setForm] = useState({
    name: subject?.name ?? '',
    class_code: subject?.class_code ?? '',
    lecturer: subject?.lecturer ?? '',
    course_code: subject?.course_code ?? '',
    credits: subject?.credits == null ? '' : String(subject.credits),
  });
  const [rows, setRows] = useState<ScheduleRow[]>(() =>
    subject
      ? subject.schedules.map((rule) => ({
          id: rule.id,
          weekdays: rule.weekdays,
          start_date: rule.start_date,
          end_date: rule.end_date,
          time: { shift: rule.shift, start_time: rule.start_time, end_time: rule.end_time },
          period_from: rule.period_from,
          period_to: rule.period_to,
          room: rule.room ?? '',
        }))
      : [blankRow(semester?.start_date ?? '', semester?.end_date ?? '')],
  );
  const [color, setColor] = useState<string | null>(subject?.color ?? null);
  const [tagIds, setTagIds] = useState<number[]>(subject?.tags.map((tag) => tag.id) ?? []);
  const [reminder, setReminder] = useState<number | null>(subject?.reminder_minutes ?? null);
  const [important, setImportant] = useState(subject?.is_important ?? false);
  const settings = useSettings().data;
  const [conflicts, setConflicts] = useState<ExceptionConflict[] | null>(null);
  const save = useSaveSubject();

  const set = (field: keyof typeof form) => (value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  function changeSemester(id: number) {
    const next = semesters.find((s) => s.id === id);
    setSemesterId(id);
    if (next && !subject)
      setRows((prev) =>
        prev.map((row) => ({ ...row, start_date: next.start_date, end_date: next.end_date })),
      );
  }

  function send(confirm = false) {
    const input = {
      name: form.name.trim(),
      class_code: blankToNull(form.class_code),
      lecturer: blankToNull(form.lecturer),
      course_code: blankToNull(form.course_code),
      credits: form.credits.trim() === '' ? null : Number(form.credits),
      schedules: rows.map(rowToInput),
      tag_ids: tagIds,
      reminder_minutes: reminder,
      is_important: important,
      ...(color ? { color } : {}),
      ...(subject ? {} : { semester_id: semesterId }),
    };
    save.mutate(
      { id: subject?.id, input, confirm },
      {
        onSuccess: (result) => onDone(result.data, result.warnings),
        onError: (err) => {
          if (err instanceof ApiError && err.status === 409) {
            setConflicts((err.details as { sessions: ExceptionConflict[] }).sessions);
          }
        },
      },
    );
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    send();
  }

  const error = save.error instanceof ApiError && save.error.status === 409 ? null : save.error;

  return (
    <form onSubmit={submit} noValidate>
      <FormField label={t('subjects.fieldName')} name="name" error={error}>
        <input autoFocus value={form.name} onChange={(e) => set('name')(e.target.value)} />
      </FormField>
      {!subject && (
        <FormField label={t('subjects.semester')} name="semester_id" error={error}>
          <select value={semesterId} onChange={(e) => changeSemester(Number(e.target.value))}>
            {semesters.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </FormField>
      )}
      <ScheduleRows
        rows={rows}
        onChange={setRows}
        errors={error instanceof ApiError ? error.fields : {}}
      />
      <FormRow>
        <FormField label={t('subjects.fieldCourseCode')} name="course_code" error={error}>
          <input value={form.course_code} onChange={(e) => set('course_code')(e.target.value)} />
        </FormField>
        <FormField label={t('subjects.fieldClassCode')} name="class_code" error={error}>
          <input value={form.class_code} onChange={(e) => set('class_code')(e.target.value)} />
        </FormField>
        <FormField label={t('subjects.fieldCredits')} name="credits" error={error}>
          <input
            type="number"
            min={0}
            max={30}
            value={form.credits}
            onChange={(e) => set('credits')(e.target.value)}
          />
        </FormField>
      </FormRow>
      <FormField label={t('subjects.fieldLecturer')} name="lecturer" error={error}>
        <input value={form.lecturer} onChange={(e) => set('lecturer')(e.target.value)} />
      </FormField>
      <div className="mb-3">
        <ImportantToggle value={important} onChange={setImportant} />
      </div>
      <FormField label={t('tags.pick')} name="tag_ids" error={error}>
        <TagPicker value={tagIds} onChange={setTagIds} />
      </FormField>
      <FormField label={t('reminders.field')} name="reminder_minutes" error={error}>
        <ReminderSelect
          value={reminder}
          onChange={setReminder}
          defaultLabel={
            settings
              ? t('reminders.defaultSession', {
                  time: t('reminders.before', {
                    time: minutesLabel(settings.session_reminder_minutes),
                  }).toLowerCase(),
                })
              : t('reminders.defaultTask')
          }
        />
      </FormField>
      <FormField label={t('subjects.fieldColor')} name="color" error={error}>
        <ColorPicker value={color} onChange={setColor} />
        {!color && <span className="text-[12px] text-muted">{t('subjects.autoColor')}</span>}
      </FormField>
      <FormActions saving={save.isPending} onCancel={() => onDone()} />
      <ConfirmDialog
        open={conflicts !== null}
        title={t('subjects.editSubject')}
        message={t('subjects.confirmExceptions', {
          dates: (conflicts ?? []).map((c) => formatDate(c.date)).join(', '),
        })}
        confirmLabel={t('confirm.continue')}
        onCancel={() => setConflicts(null)}
        onConfirm={() => {
          setConflicts(null);
          send(true);
        }}
      />
    </form>
  );
}
