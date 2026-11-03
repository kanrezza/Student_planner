import { useState, type FormEvent } from 'react';
import { useCreateTask, useUpdateTask } from '../api/tasks';
import type { Priority, Task, TaskList } from '../api/types';
import { t } from '../i18n/vi';
import { PRIORITIES, blankToNull, priorityLabel } from '../lib/format';
import { FormField } from './FormField';
import { TagPicker } from './TagPicker';

/** Thêm hoặc sửa một công việc (FR-001, FR-002). Lỗi từ API hiện ngay dưới ô tương ứng. */
export function TaskForm({
  task,
  lists,
  defaultListId,
  onDone,
}: {
  task?: Task;
  lists: TaskList[];
  defaultListId: number;
  onDone: () => void;
}) {
  const [title, setTitle] = useState(task?.title ?? '');
  const [notes, setNotes] = useState(task?.notes ?? '');
  const [dueDate, setDueDate] = useState(task?.due_date ?? '');
  const [dueTime, setDueTime] = useState(task?.due_time ?? '');
  const [priority, setPriority] = useState<Priority>(task?.priority ?? 2);
  const [listId, setListId] = useState(task?.list_id ?? defaultListId);
  const [titleError, setTitleError] = useState<string | null>(null);
  const [tagIds, setTagIds] = useState<number[]>(task?.tags.map((tag) => tag.id) ?? []);

  const create = useCreateTask();
  const update = useUpdateTask();
  const saving = create.isPending || update.isPending;
  const error = create.error ?? update.error;

  function submit(e: FormEvent) {
    e.preventDefault();
    if (title.trim() === '') {
      setTitleError('Trường này không được để trống');
      return;
    }
    setTitleError(null);
    const input = {
      title: title.trim(),
      notes: blankToNull(notes),
      due_date: dueDate || null,
      due_time: dueDate && dueTime ? dueTime : null,
      priority,
      list_id: listId,
      tag_ids: tagIds,
    };
    const options = { onSuccess: onDone };
    if (task) update.mutate({ id: task.id, input }, options);
    else create.mutate(input, options);
  }

  return (
    <form onSubmit={submit} noValidate>
      <FormField label={t('tasks.fieldTitle')} name="title" error={error}>
        <input
          autoFocus
          value={title}
          maxLength={300}
          onChange={(e) => setTitle(e.target.value)}
          aria-invalid={titleError !== null}
        />
        {titleError && (
          <span className="field__error" role="alert">
            {titleError}
          </span>
        )}
      </FormField>
      <FormField label={t('tasks.fieldNotes')} name="notes" error={error}>
        <textarea rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
      </FormField>
      <div className="form-row">
        <FormField label={t('tasks.fieldDueDate')} name="due_date" error={error}>
          <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
        </FormField>
        <FormField label={t('tasks.fieldDueTime')} name="due_time" error={error}>
          <input
            type="time"
            value={dueTime}
            disabled={!dueDate}
            onChange={(e) => setDueTime(e.target.value)}
          />
        </FormField>
      </div>
      <div className="form-row">
        <FormField label={t('tasks.fieldPriority')} name="priority" error={error}>
          <select
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value) as Priority)}
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {priorityLabel(p)}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label={t('tasks.fieldList')} name="list_id" error={error}>
          <select value={listId} onChange={(e) => setListId(Number(e.target.value))}>
            {lists.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
        </FormField>
      </div>
      <FormField label={t('tags.pick')} name="tag_ids" error={error}>
        <TagPicker value={tagIds} onChange={setTagIds} />
      </FormField>
      <FormActions saving={saving} onCancel={onDone} />
    </form>
  );
}

export function FormActions({ saving, onCancel }: { saving: boolean; onCancel: () => void }) {
  return (
    <div className="dialog__actions">
      <button type="button" onClick={onCancel}>
        {t('common.cancel')}
      </button>
      <button type="submit" className="button--primary" disabled={saving}>
        {t('common.save')}
      </button>
    </div>
  );
}
