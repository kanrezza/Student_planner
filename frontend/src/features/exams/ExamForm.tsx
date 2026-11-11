import { useState, type FormEvent } from 'react';
import { DateInput } from '../../components/DateInput';
import type { ApiWarning } from '../../api/client';
import { useSaveExam } from '../../api/exams';
import type { Exam } from '../../api/types';
import { FormActions } from '../../components/FormActions';
import { AttachmentsSection } from '../attachments/AttachmentsSection';
import { FormField, FormRow } from '../../components/FormField';
import { ImportantToggle } from '../../components/ImportantToggle';
import { minutesLabel } from '../../components/ReminderSelect';
import { TagPicker } from '../../components/TagPicker';
import { t } from '../../i18n/vi';
import { formatTime } from '../../lib/dates';
import { blankToNull } from '../../lib/format';

/** Giá trị của ô chọn nhắc: theo mặc định, tắt, hoặc một mốc riêng (phút báo trước). */
const REMINDER_CHOICES = [60, 180, 1440, 10080];

function reminderValue(offsets: number[] | null): string {
  if (offsets === null) return 'default';
  if (offsets.length === 0) return 'off';
  return String(offsets[0]);
}

function reminderLabel(minutes: number): string {
  return t('reminders.before', { time: minutesLabel(minutes) });
}

/** Thêm hoặc sửa một buổi thi (FR-055, FR-063). Phòng thi được để trống. */
export function ExamForm({
  exam,
  defaultDate,
  onDone,
}: {
  exam?: Exam;
  defaultDate?: string;
  onDone: (warnings?: ApiWarning[]) => void;
}) {
  const [form, setForm] = useState({
    course_name: exam?.course_name ?? '',
    course_code: exam?.course_code ?? '',
    attempt: String(exam?.attempt ?? 1),
    date: exam?.date ?? defaultDate ?? '',
    start_time: exam ? formatTime(exam.start_at) : '',
    end_time: exam ? formatTime(exam.end_at) : '',
    exam_format: exam?.exam_format ?? '',
    room: exam?.room ?? '',
    candidate_number: exam?.candidate_number ?? '',
  });
  const [important, setImportant] = useState(exam?.is_important ?? true);
  const [reminder, setReminder] = useState(reminderValue(exam?.reminder_offsets ?? null));
  const [tagIds, setTagIds] = useState<number[]>(
    exam?.tags.filter((tag) => tag.system_key !== 'exam').map((tag) => tag.id) ?? [],
  );
  const save = useSaveExam();
  const set = (field: keyof typeof form) => (value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  function submit(e: FormEvent) {
    e.preventDefault();
    const offsets = reminder === 'default' ? null : reminder === 'off' ? [] : [Number(reminder)];
    const input = {
      course_name: form.course_name.trim(),
      course_code: blankToNull(form.course_code),
      attempt: Number(form.attempt) || 1,
      date: form.date,
      start_time: form.start_time,
      end_time: form.end_time,
      exam_format: blankToNull(form.exam_format),
      room: blankToNull(form.room),
      candidate_number: blankToNull(form.candidate_number),
      reminder_offsets: offsets,
      is_important: important,
      ...(exam ? {} : { tag_ids: tagIds }),
    };
    save.mutate({ id: exam?.id, input }, { onSuccess: (result) => onDone(result.warnings) });
  }

  const error = save.error;
  return (
    <>
      <form onSubmit={submit} noValidate>
        <FormField label={t('exams.fieldName')} name="course_name" error={error}>
          <input
            autoFocus
            value={form.course_name}
            onChange={(e) => set('course_name')(e.target.value)}
          />
        </FormField>
        <FormRow>
          <FormField label={t('exams.fieldCode')} name="course_code" error={error}>
            <input value={form.course_code} onChange={(e) => set('course_code')(e.target.value)} />
          </FormField>
          <FormField label={t('exams.fieldAttempt')} name="attempt" error={error}>
            <input
              type="number"
              min={1}
              value={form.attempt}
              onChange={(e) => set('attempt')(e.target.value)}
            />
          </FormField>
        </FormRow>
        <FormRow>
          <FormField label={t('exams.fieldDate')} name="date" error={error}>
            <DateInput value={form.date} onChange={set('date')} />
          </FormField>
          <FormField label={t('exams.fieldStart')} name="start_time" error={error}>
            <input
              type="time"
              value={form.start_time}
              onChange={(e) => set('start_time')(e.target.value)}
            />
          </FormField>
          <FormField label={t('exams.fieldEnd')} name="end_time" error={error}>
            <input
              type="time"
              value={form.end_time}
              onChange={(e) => set('end_time')(e.target.value)}
            />
          </FormField>
        </FormRow>
        <FormField label={t('exams.fieldFormat')} name="exam_format" error={error}>
          <input value={form.exam_format} onChange={(e) => set('exam_format')(e.target.value)} />
        </FormField>
        <FormRow>
          <FormField label={t('exams.fieldRoom')} name="room" error={error}>
            <input value={form.room} onChange={(e) => set('room')(e.target.value)} />
          </FormField>
          <FormField label={t('exams.fieldCandidate')} name="candidate_number" error={error}>
            <input
              value={form.candidate_number}
              onChange={(e) => set('candidate_number')(e.target.value)}
            />
          </FormField>
        </FormRow>
        <div className="mb-3">
          <ImportantToggle value={important} onChange={setImportant} />
        </div>
        <FormField label={t('reminders.field')} name="reminder_offsets" error={error}>
          <select value={reminder} onChange={(e) => setReminder(e.target.value)}>
            <option value="default">{t('exams.reminderDefault')}</option>
            <option value="off">{t('exams.reminderOff')}</option>
            {REMINDER_CHOICES.map((minutes) => (
              <option key={minutes} value={minutes}>
                {reminderLabel(minutes)}
              </option>
            ))}
          </select>
        </FormField>
        {!exam && (
          <FormField label={t('tags.pick')} name="tag_ids" error={error}>
            <TagPicker value={tagIds} onChange={setTagIds} />
          </FormField>
        )}
        <FormActions saving={save.isPending} onCancel={() => onDone()} />
      </form>
      {exam && (
        <AttachmentsSection owner={{ type: 'exam', id: exam.id }} ownerTitle={exam.course_name} />
      )}
    </>
  );
}
