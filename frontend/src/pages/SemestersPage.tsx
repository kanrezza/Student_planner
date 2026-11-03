import { useState } from 'react';
import { ApiError } from '../api/client';
import { useDeleteSemester, useSemesters } from '../api/semesters';
import type { Semester } from '../api/types';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { Modal } from '../components/Modal';
import { SemesterForm } from '../components/SemesterForm';
import { t } from '../i18n/vi';
import { formatDate } from '../lib/dates';

/** Quản lý học kỳ (FR-036, FR-037) — nằm trong trang Cài đặt. */
export function SemestersPage() {
  const semesters = useSemesters();
  const remove = useDeleteSemester();
  const [editing, setEditing] = useState<Semester | 'new' | null>(null);
  const [deleting, setDeleting] = useState<{ semester: Semester; subjectCount?: number } | null>(
    null,
  );

  function confirmDelete() {
    if (!deleting) return;
    const { semester, subjectCount } = deleting;
    remove.mutate(
      { id: semester.id, confirm: subjectCount !== undefined },
      {
        onSuccess: () => setDeleting(null),
        onError: (err) => {
          if (err instanceof ApiError && err.status === 409) {
            const count = (err.details as { subject_count: number }).subject_count;
            setDeleting({ semester, subjectCount: count });
          }
        },
      },
    );
  }

  return (
    <section className="panel">
      <div className="page-header">
        <h2>{t('semesters.title')}</h2>
        <button type="button" className="button--primary" onClick={() => setEditing('new')}>
          {t('semesters.create')}
        </button>
      </div>
      {semesters.data?.length === 0 && <p className="muted">{t('semesters.empty')}</p>}
      <ul className="subject-list">
        {semesters.data?.map((s) => (
          <li key={s.id} className="subject-item">
            <div className="grow">
              <span className="subject-item__name">{s.name}</span>{' '}
              {s.is_current && (
                <span className="badge badge--primary">{t('semesters.current')}</span>
              )}
              <div className="muted">
                {formatDate(s.start_date)} – {formatDate(s.end_date)}
              </div>
            </div>
            <div className="row-actions">
              <button type="button" onClick={() => setEditing(s)}>
                {t('common.edit')}
              </button>
              <button type="button" onClick={() => setDeleting({ semester: s })}>
                {t('common.delete')}
              </button>
            </div>
          </li>
        ))}
      </ul>

      {editing && (
        <Modal
          title={editing === 'new' ? t('semesters.create') : t('semesters.edit')}
          onClose={() => setEditing(null)}
        >
          <SemesterForm
            semester={editing === 'new' ? undefined : editing}
            onDone={() => setEditing(null)}
            onCancel={() => setEditing(null)}
          />
        </Modal>
      )}
      <ConfirmDialog
        open={deleting !== null}
        message={
          deleting?.subjectCount !== undefined
            ? t('semesters.deleteWithSubjects', {
                name: deleting.semester.name,
                count: deleting.subjectCount,
              })
            : t('semesters.deleteConfirm', { name: deleting?.semester.name ?? '' })
        }
        onCancel={() => setDeleting(null)}
        onConfirm={confirmDelete}
      />
    </section>
  );
}
