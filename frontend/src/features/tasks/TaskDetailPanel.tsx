import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react';
import { DateInput } from '../../components/DateInput';
import { ApiError } from '../../api/client';
import { useLists } from '../../api/lists';
import { useSemesters } from '../../api/semesters';
import { useSettings } from '../../api/settings';
import { useSubjects } from '../../api/subjects';
import {
  isScopeRequired,
  useCreateTask,
  useTask,
  useUpdateTask,
  type Scope,
} from '../../api/tasks';
import type { Priority, RecurrenceRule, Task, TaskInput } from '../../api/types';
import { useNow } from '../../app/useNow';
import { ImportantToggle } from '../../components/ImportantToggle';
import { minutesLabel, ReminderSelect } from '../../components/ReminderSelect';
import { SessionLink } from '../../components/SessionLink';
import { TagPicker } from '../../components/TagPicker';
import { TimeInput } from '../../components/TimeInput';
import { t } from '../../i18n/vi';
import { formatDayLong, formatDayShort, formatTime } from '../../lib/dates';
import { PRIORITIES, blankToNull, priorityLabel } from '../../lib/format';
import { Button } from '../../ui/Button';
import { Checkbox } from '../../ui/Checkbox';
import { cx } from '../../ui/cx';
import { IconButton } from '../../ui/IconButton';
import { IconAlert, IconClose, IconRepeat, IconTrash } from '../../ui/icons';
import { SidePanel } from '../../ui/SidePanel';
import { Switch } from '../../ui/Switch';
import { useToast } from '../../ui/Toast';
import { AttachmentsSection } from '../attachments/AttachmentsSection';
import { RecurrenceEditor } from './recurrence/RecurrenceEditor';
import { useAskScope } from './recurrence/ScopeDialog';
import { useTaskActions } from './useTaskActions';
import { defaultWorkWindow, isWorkAfterDue, workWindowError, type WorkWindow } from './workWindow';

/**
 * Bảng chi tiết bên phải (feature 002 FR-013): xem và sửa mọi trường của task. Mỗi trường được lưu
 * khi rời ô (hoặc Enter ở ô một dòng); chỉ gửi trường đã đổi; lỗi hiện ngay dưới ô.
 */
export function TaskDetailPanel({ taskId, onClose }: { taskId: number; onClose: () => void }) {
  const query = useTask(taskId);
  return (
    <SidePanel label={t('detail.label')}>
      {query.data ? (
        <TaskEditor key={query.data.id} task={query.data} onClose={onClose} />
      ) : (
        <div className="flex flex-1 flex-col">
          <PanelHeader onClose={onClose} />
          <p className="px-5 py-6 text-muted">
            {query.isError ? t('detail.notFound') : t('common.loading')}
          </p>
        </div>
      )}
    </SidePanel>
  );
}

/** Giá trị truyền vào chế độ tạo mới: `?task=new&due=YYYY-MM-DD[&work_date=&work_start=&work_end=]`. */
export type NewTaskDefaults = {
  due_date: string | null;
  work_date: string | null;
  work_start: string | null;
  work_end: string | null;
};

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TIME_RE = /^\d{2}:\d{2}$/;

export function parseNewTaskParams(params: URLSearchParams): NewTaskDefaults {
  const pick = (key: string, re: RegExp) => {
    const value = params.get(key);
    return value && re.test(value) ? value : null;
  };
  const work_date = pick('work_date', DATE_RE);
  const work_start = pick('work_start', TIME_RE);
  const work_end = pick('work_end', TIME_RE);
  const fullWork = Boolean(work_date && work_start && work_end);
  return {
    due_date: pick('due', DATE_RE),
    work_date: fullWork ? work_date : null,
    work_start: fullWork ? work_start : null,
    work_end: fullWork ? work_end : null,
  };
}

/**
 * Chế độ tạo mới của bảng chi tiết (feature 002 US4 kịch bản 9; Đợt 3 dùng lại cho chọn vùng): mọi
 * trường để trống trừ giá trị truyền vào, con trỏ ở ô tiêu đề. Chỉ gọi POST khi rời ô tiêu đề hoặc
 * Enter với tiêu đề không trống, rồi `onCreated(id)` để chuyển sang bảng chi tiết thường. Esc khi tiêu
 * đề trống thì đóng và không tạo gì.
 */
export function NewTaskPanel({
  defaults,
  onCreated,
  onClose,
}: {
  defaults: NewTaskDefaults;
  onCreated: (id: number) => void;
  onClose: () => void;
}) {
  const create = useCreateTask();
  const lists = useLists();
  const toast = useToast();
  const [title, setTitle] = useState('');
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sentRef = useRef(false);
  const closeAfterRef = useRef(false);

  useEffect(() => inputRef.current?.focus(), []);

  const studyList = lists.data?.find((l) => l.is_default_study) ?? lists.data?.[0];

  function submit(closeAfter = false) {
    const value = title.trim();
    if (value === '' || sentRef.current || !studyList) return;
    sentRef.current = true;
    closeAfterRef.current = closeAfter;
    create.mutate(
      {
        title: value,
        notes: null,
        due_date: defaults.due_date,
        due_time: null,
        priority: 2,
        list_id: studyList.id,
        is_important: false,
        reminder_minutes: null,
        ...(defaults.work_date
          ? {
              work_date: defaults.work_date,
              work_start: defaults.work_start,
              work_end: defaults.work_end,
            }
          : {}),
      },
      {
        onSuccess: ({ task, warnings }) => {
          for (const warning of warnings) toast.show(warning.message, { tone: 'warning' });
          if (closeAfterRef.current) onClose();
          else onCreated(task.id);
        },
        onError: (err) => {
          sentRef.current = false;
          if (err instanceof ApiError && err.fields.title) setError(err.fields.title);
          else toast.show(t('detail.createFailed', { message: err.message }), { tone: 'danger' });
        },
      },
    );
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.nativeEvent.isComposing) return;
    if (e.key === 'Enter') {
      e.preventDefault();
      submit();
    } else if (e.key === 'Escape') {
      e.preventDefault(); // phím Esc chung của màn hình bỏ qua sự kiện đã xử lý
      if (title.trim() === '') onClose();
      else submit(true);
    }
  }

  return (
    <SidePanel label={t('detail.newLabel')}>
      <div className="flex min-h-0 flex-1 flex-col">
        <PanelHeader onClose={onClose}>
          <span className="truncate text-[12px] font-medium text-muted">
            {t('detail.newLabel')}
            {studyList ? ` · ${`${studyList.emoji ?? ''} ${studyList.name}`.trim()}` : ''}
          </span>
        </PanelHeader>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-6 pt-4">
          <input
            ref={inputRef}
            aria-label={t('tasks.fieldTitle')}
            value={title}
            maxLength={300}
            placeholder={t('detail.titlePlaceholder')}
            onChange={(e) => {
              setTitle(e.target.value);
              setError(null);
            }}
            onBlur={() => submit()}
            onKeyDown={onKeyDown}
            aria-invalid={Boolean(error)}
            readOnly={create.isPending}
            className="h-auto border-transparent bg-transparent px-1 py-0.5 text-[17px] font-semibold hover:border-border"
          />
          <FieldError message={error ?? undefined} />
          <p className="mt-2 px-1 text-[12px] text-muted">{t('detail.newHint')}</p>
          <dl className="mt-4 flex flex-col divide-y divide-border border-y border-border">
            <Row label={t('detail.due')}>
              <span>{defaults.due_date ? formatDayShort(defaults.due_date) : '—'}</span>
            </Row>
            {defaults.work_date && (
              <Row label={t('detail.workWindow')}>
                <span className="tabular-nums">
                  {formatDayShort(defaults.work_date)}, {defaults.work_start}–{defaults.work_end}
                </span>
              </Row>
            )}
          </dl>
        </div>
      </div>
    </SidePanel>
  );
}

function PanelHeader({ onClose, children }: { onClose: () => void; children?: ReactNode }) {
  return (
    <div className="flex h-12 shrink-0 items-center gap-2 border-b border-border px-3">
      <div className="flex min-w-0 flex-1 items-center gap-2">{children}</div>
      <IconButton
        label={t('detail.close')}
        icon={<IconClose size={16} />}
        onClick={onClose}
        tooltip={false}
      />
    </div>
  );
}

type FieldErrors = Record<string, string>;

const WORK_FIELDS = ['work_date', 'work_start', 'work_end'];

function withoutWorkErrors(errors: FieldErrors): FieldErrors {
  return Object.fromEntries(Object.entries(errors).filter(([key]) => !WORK_FIELDS.includes(key)));
}

function TaskEditor({ task, onClose }: { task: Task; onClose: () => void }) {
  const update = useUpdateTask();
  const actions = useTaskActions();
  const toast = useToast();
  const askScope = useAskScope();
  const lists = useLists().data ?? [];
  const settings = useSettings().data;
  const { now, today } = useNow();
  const currentSemester = useSemesters().data?.find((semester) => semester.is_current);
  const subjects = useSubjects(currentSemester?.id ?? null).data ?? [];

  const [title, setTitle] = useState(task.title);
  const [notes, setNotes] = useState(task.notes ?? '');
  const [dueDate, setDueDate] = useState(task.due_date ?? '');
  const [dueTime, setDueTime] = useState(task.due_time ?? '');
  const [work, setWork] = useState<Partial<WorkWindow> | null>(
    task.work_date
      ? { work_date: task.work_date, work_start: task.work_start!, work_end: task.work_end! }
      : null,
  );
  const [errors, setErrors] = useState<FieldErrors>({});

  /** Task lặp: người dùng bấm Huỷ ở hộp phạm vi → bỏ thay đổi chưa lưu, trả ô về giá trị đang lưu. */
  function resetFields() {
    setTitle(task.title);
    setNotes(task.notes ?? '');
    setDueDate(task.due_date ?? '');
    setDueTime(task.due_time ?? '');
    setWork(
      task.work_date
        ? { work_date: task.work_date, work_start: task.work_start!, work_end: task.work_end! }
        : null,
    );
  }

  function save(input: Partial<TaskInput>, fields: string[] = Object.keys(input), scope?: Scope) {
    setErrors((current) => {
      const next = { ...current };
      for (const field of fields) delete next[field];
      return next;
    });
    // `mutateAsync` (không phải `mutate`): lệnh lưu cũ vẫn báo lỗi/hỏi phạm vi được dù ô khác vừa
    // gửi lệnh lưu mới (callback của `mutate` chỉ chạy cho lần gọi sau cùng).
    update.mutateAsync({ id: task.id, input, scope }).catch((err: Error) => {
      if (isScopeRequired(err)) {
        // Sửa lần hiện tại của task lặp: hỏi "Chỉ lần này" hay "Lần này và các lần sau" (FR-020).
        void askScope('edit').then((chosen) => {
          if (chosen) save(input, fields, chosen);
          else resetFields();
        });
      } else if (err instanceof ApiError && Object.keys(err.fields).length) {
        setErrors((current) => ({ ...current, ...err.fields }));
      } else {
        toast.show(t('detail.saveFailed', { message: err.message }), { tone: 'danger' });
      }
    });
  }

  function saveTitle() {
    const value = title.trim();
    if (value === '') {
      setErrors((e) => ({ ...e, title: 'Trường này không được để trống' }));
      return;
    }
    if (value !== task.title) save({ title: value });
  }

  function saveDue(nextDate: string, nextTime: string) {
    const due_date = nextDate || null;
    const due_time = due_date && nextTime ? nextTime : null;
    if (due_date !== task.due_date || due_time !== task.due_time) save({ due_date, due_time });
  }

  function saveWork(next: Partial<WorkWindow> | null) {
    setWork(next);
    if (next === null) {
      if (task.work_date !== null) save({ work_date: null, work_start: null, work_end: null });
      return;
    }
    const invalid = workWindowError(next);
    if (invalid) {
      setErrors((current) => ({ ...withoutWorkErrors(current), ...invalid }));
      return;
    }
    const changed =
      next.work_date !== task.work_date ||
      next.work_start !== task.work_start ||
      next.work_end !== task.work_end;
    if (changed) save(next as WorkWindow, WORK_FIELDS);
  }

  const blurOnEnter = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.nativeEvent.isComposing) e.currentTarget.blur();
  };

  const dateOnly = Boolean(task.due_date) && !task.due_time;
  const workAfterDue = isWorkAfterDue(task);
  const currentList = lists.find((l) => l.id === task.list_id);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <PanelHeader onClose={onClose}>
        <Checkbox
          checked={task.completed}
          priority={task.priority}
          label={task.completed ? t('tasks.markUndone') : t('tasks.markDone')}
          onChange={(checked) => actions.toggleComplete(task, checked)}
        />
        <span className="truncate text-[12px] text-muted">
          {task.completed && task.completed_at
            ? t('detail.completedAt', {
                time: `${formatTime(task.completed_at)}, ${formatDayLong(task.completed_at)}`,
              })
            : currentList
              ? `${currentList.emoji ?? ''} ${currentList.name}`.trim()
              : ''}
        </span>
      </PanelHeader>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-6 pt-4">
        <input
          aria-label={t('tasks.fieldTitle')}
          value={title}
          maxLength={300}
          placeholder={t('detail.titlePlaceholder')}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={saveTitle}
          onKeyDown={blurOnEnter}
          aria-invalid={Boolean(errors.title)}
          className={cx(
            'h-auto border-transparent bg-transparent px-1 py-0.5 text-[17px] font-semibold',
            'hover:border-border',
            task.completed && 'text-muted line-through',
          )}
        />
        <FieldError message={errors.title} />

        <textarea
          aria-label={t('tasks.fieldNotes')}
          value={notes}
          rows={3}
          placeholder={t('detail.notesPlaceholder')}
          onChange={(e) => setNotes(e.target.value)}
          onBlur={() => {
            const value = blankToNull(notes);
            if (value !== task.notes) save({ notes: value });
          }}
          className="mt-2 resize-y border-transparent bg-transparent px-1 hover:border-border"
        />
        <FieldError message={errors.notes} />

        {task.is_auto && (
          <div className="mt-3 flex items-start gap-2 rounded-lg bg-surface-2 px-3 py-2 text-[12px] text-muted">
            <IconRepeat size={14} className="mt-0.5 shrink-0" />
            <span>
              {t('tasks.autoNote')}{' '}
              {task.source_session_id && <SessionLink sessionId={task.source_session_id} />}
            </span>
          </div>
        )}

        <dl className="mt-4 flex flex-col divide-y divide-border border-y border-border">
          <Row label={t('detail.status')}>
            <select
              aria-label={t('detail.status')}
              value={task.status ?? (task.completed ? 'done' : 'todo')}
              onChange={(e) => {
                const value = e.target.value;
                if (value === 'done') actions.toggleComplete(task, true);
                else save({ status: value as 'todo' | 'doing' }, ['status']);
              }}
            >
              <option value="todo">{t('board.columns.todo')}</option>
              <option value="doing">{t('board.columns.doing')}</option>
              <option value="done">{t('board.columns.done')}</option>
            </select>
          </Row>

          <Row label={t('detail.subject')}>
            {task.is_auto && task.source_session_id ? (
              <p className="text-[12px] text-muted">{t('detail.subjectAuto')}</p>
            ) : (
              <select
                aria-label={t('detail.subject')}
                value={task.subject_id ?? ''}
                onChange={(e) =>
                  save({ subject_id: e.target.value ? Number(e.target.value) : null }, [
                    'subject_id',
                  ])
                }
              >
                <option value="">{t('detail.noSubject')}</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>
            )}
          </Row>

          <Row label={t('detail.due')}>
            <div className="flex items-center gap-1.5">
              <DateInput
                label={t('detail.dueDate')}
                value={dueDate}
                onChange={setDueDate}
                onBlur={() => saveDue(dueDate, dueTime)}
                invalid={Boolean(errors.due_date)}
                className="w-[9.5rem]"
              />
              <TimeInput
                label={t('detail.dueTime')}
                value={dueTime}
                disabled={!dueDate}
                onChange={setDueTime}
                onBlur={(time) => saveDue(dueDate, time)}
                invalid={Boolean(errors.due_time)}
                className="w-[5.6rem]"
              />
              {dueDate && dueTime && (
                <IconButton
                  label={t('detail.clearDueTime')}
                  icon={<IconClose size={14} />}
                  size="sm"
                  onClick={() => {
                    setDueTime('');
                    saveDue(dueDate, '');
                  }}
                />
              )}
              {dueDate && (
                <IconButton
                  label={t('detail.clearDue')}
                  icon={<IconClose size={14} />}
                  size="sm"
                  onClick={() => {
                    setDueDate('');
                    setDueTime('');
                    saveDue('', '');
                  }}
                />
              )}
            </div>
            <FieldError message={errors.due_date || errors.due_time} />
          </Row>

          <Row
            label={t('detail.workWindow')}
            action={
              <Switch
                label={t('detail.workWindow')}
                checked={work !== null}
                onChange={(on) =>
                  saveWork(
                    on
                      ? defaultWorkWindow(task, today, now.getHours() * 60 + now.getMinutes())
                      : null,
                  )
                }
              />
            }
          >
            {work === null ? (
              <p className="text-[12px] text-muted">{t('detail.workWindowHelp')}</p>
            ) : (
              <>
                <div className="flex items-center gap-1">
                  <DateInput
                    label={t('detail.workDate')}
                    value={work.work_date ?? ''}
                    onChange={(v) => setWork({ ...work, work_date: v })}
                    onBlur={() => saveWork(work)}
                    invalid={Boolean(errors.work_date)}
                    className="w-[9.5rem]"
                  />
                  <TimeInput
                    label={t('detail.workStart')}
                    value={work.work_start ?? ''}
                    onChange={(v) => setWork({ ...work, work_start: v })}
                    onBlur={(v) => saveWork({ ...work, work_start: v })}
                    invalid={Boolean(errors.work_start)}
                    className="w-[5.6rem]"
                  />
                  <span className="text-muted">–</span>
                  <TimeInput
                    label={t('detail.workEnd')}
                    value={work.work_end ?? ''}
                    onChange={(v) => setWork({ ...work, work_end: v })}
                    onBlur={(v) => saveWork({ ...work, work_end: v })}
                    invalid={Boolean(errors.work_end)}
                    className="w-[5.6rem]"
                  />
                </div>
                <FieldError message={errors.work_date || errors.work_start || errors.work_end} />
                {workAfterDue && !errors.work_date && !errors.work_end && (
                  <p className="mt-1 flex items-center gap-1 text-[12px] text-warning">
                    <IconAlert size={13} />
                    {t('detail.workAfterDue')}
                  </p>
                )}
              </>
            )}
          </Row>

          {!task.is_auto && !task.completed && (
            <Row label={t('recurrence.label')}>
              {task.due_date ? (
                <RecurrenceEditor
                  value={task.recurrence}
                  dueDate={task.due_date}
                  onChange={(recurrence: RecurrenceRule | null) => save({ recurrence })}
                />
              ) : (
                <p className="text-[12px] text-muted">{t('recurrence.needsDue')}</p>
              )}
              <FieldError message={errors.recurrence} />
            </Row>
          )}
          {task.completed && task.series_finished && (
            <Row label={t('recurrence.label')}>
              <p className="text-[13px] text-muted">{t('recurrence.finished')}</p>
            </Row>
          )}

          <Row label={t('detail.priority')}>
            <select
              aria-label={t('detail.priority')}
              value={task.priority}
              onChange={(e) => save({ priority: Number(e.target.value) as Priority })}
              className="w-40"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {priorityLabel(p)}
                </option>
              ))}
            </select>
          </Row>

          <Row label={t('detail.list')}>
            <select
              aria-label={t('detail.list')}
              value={task.list_id}
              onChange={(e) => save({ list_id: Number(e.target.value) })}
              className="w-56"
            >
              {lists.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.emoji ? `${l.emoji} ${l.name}` : l.name}
                </option>
              ))}
            </select>
            <FieldError message={errors.list_id} />
          </Row>

          <Row label={t('detail.tags')}>
            <TagPicker
              value={task.tags.map((tag) => tag.id)}
              onChange={(ids) => save({ tag_ids: ids })}
            />
          </Row>

          <Row label={t('important.label')}>
            <ImportantToggle
              value={task.is_important}
              onChange={(value) => save({ is_important: value })}
            />
          </Row>

          {task.due_date && (
            <Row label={t('detail.reminder')}>
              <ReminderSelect
                value={
                  dateOnly && (task.reminder_minutes ?? -1) >= 0 ? null : task.reminder_minutes
                }
                onChange={(value) => save({ reminder_minutes: value })}
                dateOnly={dateOnly}
                defaultLabel={
                  settings
                    ? dateOnly
                      ? t('reminders.defaultDateOnly', {
                          time: settings.date_only_task_reminder_time,
                        })
                      : t('reminders.defaultSession', {
                          time: t('reminders.before', {
                            time: minutesLabel(settings.task_reminder_minutes),
                          }).toLowerCase(),
                        })
                    : t('reminders.defaultTask')
                }
              />
            </Row>
          )}
        </dl>
        <AttachmentsSection owner={{ type: 'task', id: task.id }} ownerTitle={task.title} />
      </div>

      <div className="flex shrink-0 justify-end border-t border-border px-3 py-2">
        <Button variant="ghost" size="sm" onClick={() => actions.trash(task, onClose)}>
          <IconTrash size={15} className="text-danger" />
          {t('detail.trash')}
          <kbd className="ml-1 text-[11px] text-muted">⌘⌫</kbd>
        </Button>
      </div>
    </div>
  );
}

function Row({
  label,
  action,
  children,
}: {
  label: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="py-2.5">
      <div className="mb-1.5 flex items-center justify-between">
        <dt className="text-[12px] font-medium text-muted">{label}</dt>
        {action}
      </div>
      <dd>{children}</dd>
    </div>
  );
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p role="alert" className="mt-1 text-[12px] text-danger">
      {message}
    </p>
  );
}
