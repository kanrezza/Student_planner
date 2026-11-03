import { useState } from 'react';
import type { ApiWarning } from '../api/client';
import { useSemesters } from '../api/semesters';
import { useDeleteSubject, useSubjects } from '../api/subjects';
import type { Subject } from '../api/types';
import { BulkSubjectForm } from '../components/BulkSubjectForm';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { Modal } from '../components/Modal';
import { SemesterForm } from '../components/SemesterForm';
import { SubjectForm } from '../components/SubjectForm';
import { WarningToast } from '../components/WarningToast';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';
import { formatDate } from '../lib/dates';
import { weekdaysLabel } from '../lib/format';

/** Trang Môn học (US2): môn theo học kỳ, thêm một môn, nhập nhiều môn, sửa, xoá. */
export function SubjectsPage() {
  const semesters = useSemesters();
  const [semesterId, setSemesterId] = useState<number | null>(null);
  const [dialog, setDialog] = useState<'add' | 'bulk' | Subject | null>(null);
  const [deleting, setDeleting] = useState<Subject | null>(null);
  const [warnings, setWarnings] = useState<ApiWarning[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const remove = useDeleteSubject();

  const all = semesters.data ?? [];
  const current =
    all.find((s) => s.id === semesterId) ?? all.find((s) => s.is_current) ?? all[all.length - 1];
  const subjects = useSubjects(current?.id ?? null);

  if (semesters.isLoading) return <p className="muted">{t('common.loading')}</p>;

  if (!current) {
    return (
      <section className="narrow">
        <h1>{t('subjects.title')}</h1>
        <p>{t('subjects.noSemester')}</p>
        <div className="panel">
          <h2>{t('semesters.create')}</h2>
          <SemesterForm onDone={(s) => setSemesterId(s.id)} onCancel={() => undefined} />
        </div>
      </section>
    );
  }

  function finished(sessionCount?: number, newWarnings?: ApiWarning[]) {
    setDialog(null);
    if (sessionCount !== undefined) setNotice(t('subjects.created', { count: sessionCount }));
    setWarnings(newWarnings ?? []);
  }

  return (
    <section>
      <div className="page-header">
        <h1>{t('subjects.title')}</h1>
        <div className="row-actions">
          <select
            aria-label={t('subjects.semester')}
            value={current.id}
            onChange={(e) => setSemesterId(Number(e.target.value))}
          >
            {all.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
                {s.is_current ? ` (${t('semesters.current')})` : ''}
              </option>
            ))}
          </select>
          <button type="button" onClick={() => setDialog('bulk')}>
            {t('subjects.bulk')}
          </button>
          <button type="button" className="button--primary" onClick={() => setDialog('add')}>
            {t('subjects.add')}
          </button>
        </div>
      </div>
      <p className="muted">
        {formatDate(current.start_date)} – {formatDate(current.end_date)}
      </p>
      {notice && <p className="notice">{notice}</p>}

      {subjects.data?.length === 0 && <p className="muted">{t('subjects.empty')}</p>}
      <ul className="subject-list">
        {subjects.data?.map((s) => (
          <li key={s.id} className="subject-item">
            <span className="color-bar" style={{ backgroundColor: colorHex(s.color) }} />
            <div className="grow">
              <div className="subject-item__name">{s.name}</div>
              <div className="task-item__meta">
                <span>
                  {weekdaysLabel(s.weekdays)} · {s.start_time}–{s.end_time}
                </span>
                {s.room && <span>{s.room}</span>}
                {s.lecturer && <span>{s.lecturer}</span>}
                {s.class_code && <span className="muted">{s.class_code}</span>}
                <span className="muted">
                  {formatDate(s.start_date)} – {formatDate(s.end_date)} ·{' '}
                  {t('subjects.sessions', { count: s.session_count ?? 0 })}
                </span>
              </div>
            </div>
            <div className="row-actions">
              <button type="button" onClick={() => setDialog(s)}>
                {t('common.edit')}
              </button>
              <button type="button" onClick={() => setDeleting(s)}>
                {t('common.delete')}
              </button>
            </div>
          </li>
        ))}
      </ul>

      {(dialog === 'add' || (dialog && typeof dialog === 'object')) && (
        <Modal
          title={dialog === 'add' ? t('subjects.createSubject') : t('subjects.editSubject')}
          onClose={() => setDialog(null)}
        >
          <SubjectForm
            subject={dialog === 'add' ? undefined : dialog}
            semesters={all}
            defaultSemesterId={current.id}
            onDone={(result, w) => finished(result?.session_count, w)}
          />
        </Modal>
      )}
      {dialog === 'bulk' && (
        <Modal title={t('subjects.bulkTitle')} onClose={() => setDialog(null)} wide>
          <BulkSubjectForm
            semesters={all}
            defaultSemesterId={current.id}
            onDone={(result, w) => finished(result?.session_count, w)}
          />
        </Modal>
      )}
      <ConfirmDialog
        open={deleting !== null}
        message={t('subjects.deleteSubject', {
          name: deleting?.name ?? '',
          count: deleting?.session_count ?? 0,
        })}
        onCancel={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) remove.mutate(deleting.id);
          setDeleting(null);
        }}
      />
      <WarningToast warnings={warnings} onClose={() => setWarnings([])} />
    </section>
  );
}
