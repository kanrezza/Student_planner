import { useState, type FormEvent } from 'react';
import { ApiError } from '../../api/client';
import { useSaveSemester, type SemesterInput } from '../../api/semesters';
import type { Semester } from '../../api/types';
import { t } from '../../i18n/vi';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { FormField, FormRow } from '../../components/FormField';
import { FormActions } from '../../components/FormActions';

type ClampSubject = { name: string; will_be_deleted: boolean };

/** Tạo/sửa học kỳ (FR-036). Thu hẹp ngày làm môn ra ngoài → hỏi trước khi thu hẹp ngày các môn. */
export function SemesterForm({
  semester,
  onDone,
  onCancel,
}: {
  semester?: Semester;
  onDone: (semester: Semester) => void;
  onCancel: () => void;
}) {
  const [input, setInput] = useState<SemesterInput>({
    name: semester?.name ?? '',
    start_date: semester?.start_date ?? '',
    end_date: semester?.end_date ?? '',
  });
  const [clampSubjects, setClampSubjects] = useState<ClampSubject[] | null>(null);
  const save = useSaveSemester();

  function send(clamp = false) {
    save.mutate(
      { id: semester?.id, input, clamp },
      {
        onSuccess: (result) => onDone(result.data),
        onError: (err) => {
          if (err instanceof ApiError && err.status === 409) {
            setClampSubjects((err.details as { subjects: ClampSubject[] }).subjects);
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
  const set = (field: keyof SemesterInput) => (value: string) =>
    setInput((prev) => ({ ...prev, [field]: value }));

  return (
    <form onSubmit={submit} noValidate>
      <FormField label={t('semesters.fieldName')} name="name" error={error}>
        <input
          value={input.name}
          placeholder={t('semesters.namePlaceholder')}
          onChange={(e) => set('name')(e.target.value)}
        />
      </FormField>
      <FormRow>
        <FormField label={t('semesters.fieldStart')} name="start_date" error={error}>
          <input
            type="date"
            value={input.start_date}
            onChange={(e) => set('start_date')(e.target.value)}
          />
        </FormField>
        <FormField label={t('semesters.fieldEnd')} name="end_date" error={error}>
          <input
            type="date"
            value={input.end_date}
            onChange={(e) => set('end_date')(e.target.value)}
          />
        </FormField>
      </FormRow>
      <FormActions saving={save.isPending} onCancel={onCancel} />
      <ConfirmDialog
        open={clampSubjects !== null}
        title={t('semesters.clampTitle')}
        message={t('semesters.clampMessage', {
          subjects: (clampSubjects ?? [])
            .map((s) => (s.will_be_deleted ? `${s.name} ${t('semesters.willBeDeleted')}` : s.name))
            .join(', '),
        })}
        confirmLabel={t('semesters.clampConfirm')}
        onCancel={() => setClampSubjects(null)}
        onConfirm={() => {
          setClampSubjects(null);
          send(true);
        }}
      />
    </form>
  );
}
