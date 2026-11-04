import { useState } from 'react';
import { ApiError } from '../../api/client';
import { useDeleteSemester, useSemesters } from '../../api/semesters';
import type { Semester } from '../../api/types';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { Modal } from '../../components/Modal';
import { SemesterForm } from '../subjects/SemesterForm';
import { t } from '../../i18n/vi';
import { formatDate } from '../../lib/dates';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { Card, ItemList, ItemRow } from '../../ui/layout';

/** Quản lý học kỳ (FR-036, FR-037) — nằm trong trang Cài đặt. */
export function SemestersSettings() {
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
    <Card
      title={t('semesters.title')}
      actions={
        <Button variant="primary" size="sm" onClick={() => setEditing('new')}>
          {t('semesters.create')}
        </Button>
      }
    >
      {semesters.data?.length === 0 ? (
        <p className="text-muted">{t('semesters.empty')}</p>
      ) : (
        <ItemList>
          {semesters.data?.map((s) => (
            <ItemRow
              key={s.id}
              title={
                <span className="flex items-center gap-2">
                  {s.name}
                  {s.is_current && <Badge tone="accent">{t('semesters.current')}</Badge>}
                </span>
              }
              meta={
                <span>
                  {formatDate(s.start_date)} – {formatDate(s.end_date)}
                </span>
              }
              actions={
                <>
                  <Button size="sm" variant="ghost" onClick={() => setEditing(s)}>
                    {t('common.edit')}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setDeleting({ semester: s })}>
                    {t('common.delete')}
                  </Button>
                </>
              }
            />
          ))}
        </ItemList>
      )}

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
    </Card>
  );
}
