import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import type { ApiWarning } from '../../api/client';
import { useDeleteExam, useExams } from '../../api/exams';
import type { Exam } from '../../api/types';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { Modal } from '../../components/Modal';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { formatDayLong, formatTime } from '../../lib/dates';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { EmptyState } from '../../ui/EmptyState';
import { IconExam, IconPlus, IconStarFilled } from '../../ui/icons';
import { ItemList, ItemRow, Screen, SubHeading } from '../../ui/layout';
import { Switch } from '../../ui/Switch';
import { useToast } from '../../ui/Toast';
import { usePasteToImport } from '../imports/usePasteImage';
import { ExamForm } from './ExamForm';

/** Mục Lịch thi (feature 001 US11, FR-055 đến FR-058): buổi thi sắp tới theo ngày. */
export function ExamsScreen() {
  usePasteToImport();
  const [showPast, setShowPast] = useState(false);
  const exams = useExams(showPast);
  const [dialog, setDialog] = useState<'add' | Exam | null>(null);
  const [deleting, setDeleting] = useState<Exam | null>(null);
  const remove = useDeleteExam();

  // Từ kết quả tìm kiếm: `?thi=<id>` mở buổi thi đó (kể cả buổi đã qua) — feature 003 FR-042.
  const [params, setParams] = useSearchParams();
  const wantedExam = Number(params.get('thi')) || null;
  useEffect(() => {
    if (!wantedExam || !exams.data) return;
    const found = exams.data.find((e) => e.id === wantedExam);
    if (found) {
      setDialog(found);
      setParams({}, { replace: true });
    } else if (!showPast) {
      setShowPast(true);
    }
  }, [wantedExam, exams.data, showPast, setParams]);
  const toast = useToast();

  function finished(warnings?: ApiWarning[]) {
    setDialog(null);
    for (const warning of warnings ?? []) toast.show(warning.message, { tone: 'warning' });
  }

  const byDate = new Map<string, Exam[]>();
  for (const exam of exams.data ?? [])
    byDate.set(exam.date, [...(byDate.get(exam.date) ?? []), exam]);

  return (
    <Screen
      title={t('exams.title')}
      actions={
        <>
          <label className="flex items-center gap-2 text-[12px] text-muted">
            <Switch checked={showPast} onChange={setShowPast} label={t('exams.showPast')} />
            {t('exams.showPast')}
          </label>
          <Link
            to="/mon-hoc/nhap-anh"
            className="inline-flex h-8 items-center rounded-lg border border-border bg-surface px-3 hover:bg-surface-3"
          >
            {t('exams.importFromImage')}
          </Link>
          <Button variant="primary" onClick={() => setDialog('add')}>
            <IconPlus size={15} />
            {t('exams.add')}
          </Button>
        </>
      }
    >
      {exams.isLoading ? (
        <p className="text-muted">{t('common.loading')}</p>
      ) : byDate.size === 0 ? (
        <EmptyState icon={<IconExam size={44} />} title={t('exams.empty')} />
      ) : (
        [...byDate.entries()].map(([day, items]) => (
          <section key={day} className="flex flex-col gap-2">
            <SubHeading>{formatDayLong(day)}</SubHeading>
            <ItemList>
              {items.map((exam) => (
                <ExamRow
                  key={exam.id}
                  exam={exam}
                  onEdit={() => setDialog(exam)}
                  onDelete={() => setDeleting(exam)}
                />
              ))}
            </ItemList>
          </section>
        ))
      )}

      {dialog && (
        <Modal
          title={dialog === 'add' ? t('exams.add') : t('exams.edit')}
          onClose={() => setDialog(null)}
        >
          <ExamForm exam={dialog === 'add' ? undefined : dialog} onDone={finished} />
        </Modal>
      )}
      <ConfirmDialog
        open={deleting !== null}
        message={t('exams.deleteConfirm', { name: deleting?.course_name ?? '' })}
        onCancel={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) remove.mutate(deleting.id);
          setDeleting(null);
        }}
      />
    </Screen>
  );
}

function ExamRow({
  exam,
  onEdit,
  onDelete,
}: {
  exam: Exam;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <ItemRow
      color={colorHex(exam.display_color)}
      title={
        <span className="flex items-center gap-1.5">
          {exam.is_important && (
            <span aria-label={t('important.label')} className="text-warning">
              <IconStarFilled size={13} />
            </span>
          )}
          {exam.course_name}
          {exam.attempt > 1 && <Badge>{t('exams.attempt', { n: exam.attempt })}</Badge>}
          {exam.is_past && <Badge>{t('exams.past')}</Badge>}
          {exam.conflicts.length > 0 && (
            <Badge tone="warning">
              <span title={exam.conflicts.map((c) => c.title).join(', ')}>
                {t('exams.conflict')}
              </span>
            </Badge>
          )}
        </span>
      }
      meta={
        <>
          <span className="tabular-nums">
            {formatTime(exam.start_at)} – {formatTime(exam.end_at)}
          </span>
          <span>{exam.room ?? t('exams.noRoom')}</span>
          {exam.exam_format && <span>{exam.exam_format}</span>}
          {exam.candidate_number && <span>SBD {exam.candidate_number}</span>}
        </>
      }
      actions={
        <>
          <Button size="sm" variant="ghost" onClick={onEdit}>
            {t('common.edit')}
          </Button>
          <Button size="sm" variant="ghost" onClick={onDelete}>
            {t('common.delete')}
          </Button>
        </>
      }
    />
  );
}
