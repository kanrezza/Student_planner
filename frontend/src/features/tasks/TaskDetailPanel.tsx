import { useState, type KeyboardEvent, type ReactNode } from 'react';
import { ApiError } from '../../api/client';
import { useLists } from '../../api/lists';
import { useSettings } from '../../api/settings';
import { useTask, useUpdateTask } from '../../api/tasks';
import type { Priority, Task, TaskInput } from '../../api/types';
import { useNow } from '../../app/useNow';
import { ImportantToggle } from '../../components/ImportantToggle';
import { minutesLabel, ReminderSelect } from '../../components/ReminderSelect';
import { SessionLink } from '../../components/SessionLink';
import { TagPicker } from '../../components/TagPicker';
import { t } from '../../i18n/vi';
import { formatDayLong, formatTime } from '../../lib/dates';
import { PRIORITIES, blankToNull, priorityLabel } from '../../lib/format';
import { Button } from '../../ui/Button';
import { Checkbox } from '../../ui/Checkbox';
import { cx } from '../../ui/cx';
import { IconButton } from '../../ui/IconButton';
import { IconAlert, IconClose, IconRepeat, IconTrash } from '../../ui/icons';
import { SidePanel } from '../../ui/SidePanel';
import { Switch } from '../../ui/Switch';
import { useToast } from '../../ui/Toast';
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
  const lists = useLists().data ?? [];
  const settings = useSettings().data;
  const { now, today } = useNow();

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

  function save(input: Partial<TaskInput>, fields: string[] = Object.keys(input)) {
    setErrors((current) => {
      const next = { ...current };
      for (const field of fields) delete next[field];
      return next;
    });
    update.mutate(
      { id: task.id, input },
      {
        onError: (err) => {
          if (err instanceof ApiError && Object.keys(err.fields).length) {
            setErrors((current) => ({ ...current, ...err.fields }));
          } else {
            toast.show(t('detail.saveFailed', { message: err.message }), { tone: 'danger' });
          }
        },
      },
    );
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
          <Row label={t('detail.due')}>
            <div className="flex items-center gap-1.5">
              <input
                type="date"
                aria-label={t('detail.dueDate')}
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                onBlur={() => saveDue(dueDate, dueTime)}
                aria-invalid={Boolean(errors.due_date)}
                className="w-[8.75rem] px-2"
              />
              <input
                type="time"
                aria-label={t('detail.dueTime')}
                value={dueTime}
                disabled={!dueDate}
                onChange={(e) => setDueTime(e.target.value)}
                onBlur={() => saveDue(dueDate, dueTime)}
                aria-invalid={Boolean(errors.due_time)}
                className="w-[5.6rem] px-2"
              />
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
                  <input
                    type="date"
                    aria-label={t('detail.workDate')}
                    value={work.work_date ?? ''}
                    onChange={(e) => setWork({ ...work, work_date: e.target.value })}
                    onBlur={() => saveWork(work)}
                    aria-invalid={Boolean(errors.work_date)}
                    className="w-[8.75rem] px-2"
                  />
                  <input
                    type="time"
                    aria-label={t('detail.workStart')}
                    value={work.work_start ?? ''}
                    onChange={(e) => setWork({ ...work, work_start: e.target.value })}
                    onBlur={() => saveWork(work)}
                    aria-invalid={Boolean(errors.work_start)}
                    className="w-[5.6rem] px-2"
                  />
                  <span className="text-muted">–</span>
                  <input
                    type="time"
                    aria-label={t('detail.workEnd')}
                    value={work.work_end ?? ''}
                    onChange={(e) => setWork({ ...work, work_end: e.target.value })}
                    onBlur={() => saveWork(work)}
                    aria-invalid={Boolean(errors.work_end)}
                    className="w-[5.6rem] px-2"
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
