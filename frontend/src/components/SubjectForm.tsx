import { useState, type FormEvent } from 'react';
import { useSettings } from '../api/settings';
import { minutesLabel, ReminderSelect } from './ReminderSelect';
import { ApiError } from '../api/client';
import { useSaveSubject, type SubjectSaveResult } from '../api/subjects';
import type { Semester, Subject } from '../api/types';
import { t } from '../i18n/vi';
import { formatDate } from '../lib/dates';
import { blankToNull } from '../lib/format';
import { ColorPicker } from './ColorPicker';
import { ConfirmDialog } from './ConfirmDialog';
import { FormField, fieldError } from './FormField';
import { ShiftPicker, timeChoiceToInput, type TimeChoice } from './ShiftPicker';
import { TagPicker } from './TagPicker';
import { FormActions } from './TaskForm';
import { WeekdayPicker } from './WeekdayPicker';

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
    room: subject?.room ?? '',
    start_date: subject?.start_date ?? semester?.start_date ?? '',
    end_date: subject?.end_date ?? semester?.end_date ?? '',
  });
  const [weekdays, setWeekdays] = useState<number[]>(subject?.weekdays ?? []);
  const [color, setColor] = useState<string | null>(subject?.color ?? null);
  const [timeChoice, setTimeChoice] = useState<TimeChoice>({
    shift: subject?.shift ?? null,
    start_time: subject?.start_time ?? '',
    end_time: subject?.end_time ?? '',
  });
  const [tagIds, setTagIds] = useState<number[]>(subject?.tags.map((tag) => tag.id) ?? []);
  const [reminder, setReminder] = useState<number | null>(subject?.reminder_minutes ?? null);
  const settings = useSettings().data;
  const [conflicts, setConflicts] = useState<ExceptionConflict[] | null>(null);
  const save = useSaveSubject();

  const set = (field: keyof typeof form) => (value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  function changeSemester(id: number) {
    const next = semesters.find((s) => s.id === id);
    setSemesterId(id);
    if (next)
      setForm((prev) => ({ ...prev, start_date: next.start_date, end_date: next.end_date }));
  }

  function send(confirm = false) {
    const input = {
      name: form.name.trim(),
      class_code: blankToNull(form.class_code),
      lecturer: blankToNull(form.lecturer),
      room: blankToNull(form.room),
      weekdays,
      ...timeChoiceToInput(timeChoice),
      tag_ids: tagIds,
      reminder_minutes: reminder,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
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
      <FormField label={t('subjects.fieldWeekdays')} name="weekdays" error={error}>
        <WeekdayPicker value={weekdays} onChange={setWeekdays} />
      </FormField>
      <FormField label={t('shifts.pick')} name="shift" error={error}>
        <ShiftPicker value={timeChoice} onChange={setTimeChoice} />
        {(['start_time', 'end_time'] as const).map((field) => {
          const message = fieldError(error, field);
          return message ? (
            <span key={field} className="field__error" role="alert">
              {message}
            </span>
          ) : null;
        })}
      </FormField>
      <div className="form-row">
        <FormField label={t('subjects.fieldStartDate')} name="start_date" error={error}>
          <input
            type="date"
            value={form.start_date}
            onChange={(e) => set('start_date')(e.target.value)}
          />
        </FormField>
        <FormField label={t('subjects.fieldEndDate')} name="end_date" error={error}>
          <input
            type="date"
            value={form.end_date}
            onChange={(e) => set('end_date')(e.target.value)}
          />
        </FormField>
      </div>
      <div className="form-row">
        <FormField label={t('subjects.fieldRoom')} name="room" error={error}>
          <input value={form.room} onChange={(e) => set('room')(e.target.value)} />
        </FormField>
        <FormField label={t('subjects.fieldClassCode')} name="class_code" error={error}>
          <input value={form.class_code} onChange={(e) => set('class_code')(e.target.value)} />
        </FormField>
      </div>
      <FormField label={t('subjects.fieldLecturer')} name="lecturer" error={error}>
        <input value={form.lecturer} onChange={(e) => set('lecturer')(e.target.value)} />
      </FormField>
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
        {!color && <span className="muted">{t('subjects.autoColor')}</span>}
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
