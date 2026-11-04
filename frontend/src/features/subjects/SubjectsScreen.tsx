import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { ApiWarning } from '../../api/client';
import { useSemesters } from '../../api/semesters';
import { useDeleteSubject, useSubjects } from '../../api/subjects';
import type { Subject } from '../../api/types';
import { BulkSubjectForm } from '../subjects/BulkSubjectForm';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { Modal } from '../../components/Modal';
import { SemesterForm } from '../subjects/SemesterForm';
import { SubjectForm } from '../subjects/SubjectForm';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { formatDate } from '../../lib/dates';
import { weekdaysLabel } from '../../lib/format';
import { Button } from '../../ui/Button';
import { EmptyState } from '../../ui/EmptyState';
import { IconBook, IconPlus } from '../../ui/icons';
import { Card, ItemList, ItemRow, Notice, Screen } from '../../ui/layout';
import { useToast } from '../../ui/Toast';

/**
 * Mục Môn học (feature 002 US8 kịch bản 3): môn theo học kỳ, thêm một môn, nhập nhiều môn, sửa,
 * xoá có xác nhận, và lối vào "Nhập từ ảnh" (feature 001 US6).
 */
export function SubjectsScreen() {
  const semesters = useSemesters();
  const [semesterId, setSemesterId] = useState<number | null>(null);
  const [dialog, setDialog] = useState<'add' | 'bulk' | Subject | null>(null);
  const [deleting, setDeleting] = useState<Subject | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const remove = useDeleteSubject();
  const toast = useToast();

  const all = semesters.data ?? [];
  const current =
    all.find((s) => s.id === semesterId) ?? all.find((s) => s.is_current) ?? all[all.length - 1];
  const subjects = useSubjects(current?.id ?? null);

  if (semesters.isLoading) {
    return (
      <Screen title={t('subjects.title')}>
        <p className="text-muted">{t('common.loading')}</p>
      </Screen>
    );
  }

  if (!current) {
    return (
      <Screen title={t('subjects.title')}>
        <Card title={t('semesters.create')} description={t('subjects.noSemester')}>
          <SemesterForm onDone={(s) => setSemesterId(s.id)} onCancel={() => undefined} />
        </Card>
      </Screen>
    );
  }

  function finished(sessionCount?: number, newWarnings?: ApiWarning[]) {
    setDialog(null);
    if (sessionCount !== undefined) setNotice(t('subjects.created', { count: sessionCount }));
    for (const warning of newWarnings ?? []) toast.show(warning.message, { tone: 'warning' });
  }

  return (
    <Screen
      title={t('subjects.title')}
      subtitle={`${formatDate(current.start_date)} – ${formatDate(current.end_date)}`}
      actions={
        <>
          <select
            aria-label={t('subjects.semester')}
            value={current.id}
            onChange={(e) => setSemesterId(Number(e.target.value))}
            className="w-auto min-w-44"
          >
            {all.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
                {s.is_current ? ` (${t('semesters.current')})` : ''}
              </option>
            ))}
          </select>
          <Link
            to="/mon-hoc/nhap-anh"
            className="inline-flex h-8 items-center rounded-lg border border-border bg-surface px-3 hover:bg-surface-3"
          >
            {t('import.open')}
          </Link>
          <Button onClick={() => setDialog('bulk')}>{t('subjects.bulk')}</Button>
          <Button variant="primary" onClick={() => setDialog('add')}>
            <IconPlus size={15} />
            {t('subjects.add').replace('+ ', '')}
          </Button>
        </>
      }
    >
      {notice && <Notice tone="success">{notice}</Notice>}

      {subjects.data?.length === 0 ? (
        <EmptyState icon={<IconBook size={44} />} title={t('subjects.empty')} />
      ) : (
        <ItemList>
          {subjects.data?.map((s) => (
            <ItemRow
              key={s.id}
              color={colorHex(s.color)}
              title={s.name}
              meta={
                <>
                  <span className="tabular-nums">
                    {weekdaysLabel(s.weekdays)} · {s.start_time}–{s.end_time}
                  </span>
                  {s.room && <span>{s.room}</span>}
                  {s.lecturer && <span>{s.lecturer}</span>}
                  {s.class_code && <span>{s.class_code}</span>}
                  <span>
                    {formatDate(s.start_date)} – {formatDate(s.end_date)} ·{' '}
                    {t('subjects.sessions', { count: s.session_count ?? 0 })}
                  </span>
                </>
              }
              actions={
                <>
                  <Button size="sm" variant="ghost" onClick={() => setDialog(s)}>
                    {t('common.edit')}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setDeleting(s)}>
                    {t('common.delete')}
                  </Button>
                </>
              }
            />
          ))}
        </ItemList>
      )}

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
    </Screen>
  );
}
