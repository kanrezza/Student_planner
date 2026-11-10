import { useEffect, useMemo, useRef, useState, type DragEvent } from 'react';
import { ApiError } from '../../api/client';
import {
  useCommitImport,
  useRecognize,
  type CommitResult,
  type ExamRow,
  type ImportKind,
  type ImportPreview,
  type ImportRow,
} from '../../api/imports';
import { useTags } from '../../api/tags';
import { t } from '../../i18n/vi';
import { Button } from '../../ui/Button';
import { cx } from '../../ui/cx';
import { Notice, Screen } from '../../ui/layout';
import { useToast } from '../../ui/Toast';
import { ExamPreviewTable } from './ExamPreviewTable';
import { ImportPreviewTable } from './ImportPreviewTable';
import { takePendingImage } from './pendingImage';
import { usePasteImage } from './usePasteImage';
import { canSaveExams, canSaveWeek, errorsByRow } from './previewState';

export const MAX_IMAGE_BYTES = 20 * 1024 * 1024;
const ACCEPT = 'image/png,image/jpeg,image/heic,.heic';
const SOURCE_LABELS: Record<string, string> = {
  grid_dates: 'import.sourceGrid',
  week_header: 'import.sourceHeader',
  mini_calendar: 'import.sourceMini',
  menu_bar: 'import.sourceMenu',
};

/** Kiểm tra ảnh phía trình duyệt trước khi gửi (FR-028); trả thông báo lỗi hoặc null. */
export function checkImageFile(file: { size: number; type: string; name: string }): string | null {
  const isImage = /^image\/(png|jpe?g|heic|heif)$/.test(file.type) || /\.heic$/i.test(file.name);
  if (!isImage) return t('import.notImage');
  if (file.size > MAX_IMAGE_BYTES) return t('import.tooBig');
  return null;
}

/** Nhập lịch học hoặc lịch thi từ ảnh (feature 001 US6, US11): thả ảnh → xem trước → sửa → lưu. */
export function ImportScreen() {
  const recognize = useRecognize();
  const commit = useCommitImport();
  const tags = useTags();
  const toast = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [rows, setRows] = useState<ImportRow[]>([]);
  const [examRows, setExamRows] = useState<ExamRow[]>([]);
  const [eLearning, setELearning] = useState<Record<number, boolean>>({});
  const [problem, setProblem] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const thumbnail = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => (thumbnail ? URL.revokeObjectURL(thumbnail) : undefined), [thumbnail]);

  function reset() {
    setFile(null);
    setPreview(null);
    setRows([]);
    setExamRows([]);
    setProblem(null);
    setSaved(null);
    recognize.reset();
    commit.reset();
  }

  function run(image: File, kind?: ImportKind) {
    setProblem(null);
    setSaved(null);
    recognize.mutate(
      { image, kind },
      {
        onSuccess: (result) => {
          setPreview(result);
          if (result.kind === 'week_schedule') {
            setRows(result.rows);
            setExamRows(result.exam_rows ?? []);
            setELearning({});
          }
          if (result.kind === 'exam_table') setExamRows(result.exam_rows);
        },
        onError: (err) => setProblem(err instanceof ApiError ? err.message : t('import.failed')),
      },
    );
  }

  function pick(image: File | undefined) {
    if (!image) return;
    const error = checkImageFile(image);
    if (error) {
      setProblem(error);
      return;
    }
    setFile(image);
    setPreview(null);
    run(image);
  }

  // Ảnh dán từ trang Môn học / Lịch thi (đang chờ trong bộ nhớ) và ⌘V ngay tại màn hình này.
  const pickRef = useRef(pick);
  pickRef.current = pick;
  useEffect(() => {
    const waiting = takePendingImage();
    if (waiting) pickRef.current(waiting);
  }, []);
  usePasteImage(
    (image) => {
      if (recognize.isPending || commit.isPending) return;
      reset();
      pick(image);
    },
    () => toast.show(t('import.noClipboardImage')),
  );

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    pick(e.dataTransfer.files[0]);
  }

  const eLearningTag = tags.data?.find((tag) => tag.system_key === 'e_learning');
  const apiErrors = commit.error instanceof ApiError ? commit.error : null;

  function save() {
    if (!preview) return;
    const onSuccess = (result: CommitResult) => {
      for (const warning of result.warnings) toast.show(warning.message, { tone: 'warning' });
      const weekMessage = t('import.saved', {
        subjects: result.created_subjects ?? 0,
        sessions: result.created_sessions ?? 0,
        skipped: result.skipped_duplicates,
      });
      setSaved(
        preview.kind === 'exam_table'
          ? t('import.savedExams', {
              count: result.created_exams ?? 0,
              skipped: result.skipped_duplicates,
            })
          : result.created_exams
            ? `${weekMessage} ${t('import.savedWeekExams', { count: result.created_exams })}`
            : weekMessage,
      );
      setPreview(null);
      setRows([]);
      setExamRows([]);
    };
    if (preview.kind === 'exam_table') {
      commit.mutate({ kind: 'exam_table', exam_rows: examRows }, { onSuccess });
    } else {
      const body = rows.map((row, i) => ({
        ...row,
        tag_ids:
          eLearningTag && row.suggested_tags.includes('e_learning') && (eLearning[i] ?? true)
            ? [eLearningTag.id]
            : [],
      }));
      commit.mutate({ kind: 'week_schedule', rows: body, exam_rows: examRows }, { onSuccess });
    }
  }

  const selectedExams = examRows.filter((r) => r.selected).length;
  const selectedRows = rows.filter((r) => r.selected).length;
  const selectedCount =
    preview?.kind === 'exam_table' ? selectedExams : selectedRows + selectedExams;
  // Ảnh tuần có thể chỉ có buổi thi (hoặc chỉ có buổi học): mỗi nhóm có dòng được chọn phải hợp lệ.
  const canSave =
    preview?.kind === 'exam_table'
      ? canSaveExams(examRows)
      : selectedCount > 0 &&
        (selectedRows === 0 || canSaveWeek(rows)) &&
        (selectedExams === 0 || canSaveExams(examRows));

  return (
    <Screen
      title={t('import.title')}
      subtitle={t('import.subtitle')}
      width="max-w-[1000px]"
      actions={
        file && (
          <Button onClick={reset} disabled={recognize.isPending}>
            {t('import.again')}
          </Button>
        )
      }
    >
      {saved && <Notice tone="success">{saved}</Notice>}
      {problem && <Notice tone="danger">{problem}</Notice>}

      {!file && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          data-testid="dropzone"
          className={cx(
            'flex flex-col items-center gap-2 rounded-2xl border-2 border-dashed px-6 py-16 text-center',
            dragging ? 'border-accent bg-accent-soft' : 'border-border-strong',
          )}
        >
          <p className="text-[15px] font-semibold">
            {t('import.drop')}{' '}
            <Button variant="primary" onClick={() => input.current?.click()}>
              {t('import.choose')}
            </Button>
          </p>
          <p className="text-muted">{t('import.formats')}</p>
          <input
            ref={input}
            type="file"
            accept={ACCEPT}
            hidden
            data-testid="file-input"
            onChange={(e) => pick(e.target.files?.[0])}
          />
        </div>
      )}

      {file && thumbnail && (
        <div className="flex items-start gap-3">
          <img
            src={thumbnail}
            alt={file.name}
            className="h-24 w-auto max-w-[220px] rounded-lg border border-border object-contain"
          />
          {recognize.isPending && (
            <p role="status" className="pt-2 text-muted">
              {t('import.recognizing')}
            </p>
          )}
        </div>
      )}

      {preview?.kind === 'unknown' && file && (
        <Notice tone="warning">
          <p className="font-medium">{t('import.askKind')}</p>
          <p className="mb-2">{t('import.askKindHelp')}</p>
          <div className="flex gap-2">
            <Button onClick={() => run(file, 'week_schedule')}>{t('import.kindWeek')}</Button>
            <Button onClick={() => run(file, 'exam_table')}>{t('import.kindExam')}</Button>
          </div>
        </Notice>
      )}

      {preview?.kind === 'week_schedule' && (
        <>
          {preview.month_year.value && (
            <Notice tone={preview.month_year.certain ? 'info' : 'warning'}>
              {t('import.monthYear', {
                source: t(SOURCE_LABELS[preview.month_year.source ?? ''] ?? ''),
                value: preview.month_year.value.split('-').reverse().join('/'),
              })}
              {preview.month_year.reason ? ` — ${preview.month_year.reason}` : ''}
            </Notice>
          )}
          {rows.length === 0 && examRows.length === 0 && (
            <Notice tone="warning">{t('import.noRows')}</Notice>
          )}
          {rows.length > 0 && (
            <ImportPreviewTable
              rows={rows}
              onChange={setRows}
              errors={apiErrors ? errorsByRow(apiErrors.fields, 'rows') : {}}
              eLearning={eLearning}
              onELearning={(i, on) => setELearning((prev) => ({ ...prev, [i]: on }))}
            />
          )}
          {examRows.length > 0 && (
            <section aria-label={t('import.examsInWeek')} className="flex flex-col gap-2">
              <h2 className="text-[15px] font-semibold">{t('import.examsInWeek')}</h2>
              <p className="text-muted">{t('import.examsInWeekHelp')}</p>
              <ExamPreviewTable
                rows={examRows}
                onChange={setExamRows}
                errors={apiErrors ? errorsByRow(apiErrors.fields, 'exam_rows') : {}}
              />
            </section>
          )}
        </>
      )}

      {preview?.kind === 'exam_table' &&
        (examRows.length === 0 ? (
          <Notice tone="warning">{t('import.noRows')}</Notice>
        ) : (
          <ExamPreviewTable
            rows={examRows}
            onChange={setExamRows}
            errors={apiErrors ? errorsByRow(apiErrors.fields, 'exam_rows') : {}}
          />
        ))}

      {apiErrors && !Object.keys(apiErrors.fields).length && (
        <Notice tone="danger">{apiErrors.message}</Notice>
      )}

      {(preview?.kind === 'week_schedule' || preview?.kind === 'exam_table') &&
        (rows.length > 0 || examRows.length > 0) && (
          <div className="sticky bottom-0 flex justify-end gap-2 border-t border-border bg-bg py-3">
            <Button onClick={reset}>{t('import.cancel')}</Button>
            <Button variant="primary" disabled={!canSave || commit.isPending} onClick={save}>
              {t('import.save', { count: selectedCount })}
            </Button>
          </div>
        )}
    </Screen>
  );
}
