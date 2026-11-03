import { useState, type FormEvent } from 'react';
import { ApiError } from '../api/client';
import { useDeleteList, useLists, useSaveList } from '../api/lists';
import { useDeleteTask, useTasks } from '../api/tasks';
import type { Task, TaskList } from '../api/types';
import { ColorPicker } from '../components/ColorPicker';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { FormField } from '../components/FormField';
import { Modal } from '../components/Modal';
import { FormActions, TaskForm } from '../components/TaskForm';
import { TaskItem } from '../components/TaskItem';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';

/** Trang Công việc (US1): danh sách bên trái, công việc của danh sách đang chọn bên phải. */
export function TasksPage() {
  const lists = useLists();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showCompleted, setShowCompleted] = useState(false);
  const [editing, setEditing] = useState<Task | 'new' | null>(null);
  const [deleting, setDeleting] = useState<Task | null>(null);
  const [listForm, setListForm] = useState<TaskList | 'new' | null>(null);
  const [deletingList, setDeletingList] = useState<TaskList | null>(null);
  const deleteTask = useDeleteTask();

  const allLists = lists.data ?? [];
  const selected =
    allLists.find((l) => l.id === selectedId) ??
    allLists.find((l) => l.is_default_study) ??
    allLists[0];
  const tasks = useTasks(selected?.id ?? null, showCompleted);

  if (lists.isLoading) return <p className="muted">{t('common.loading')}</p>;

  return (
    <div className="two-columns">
      <aside className="panel">
        <h2>{t('tasks.lists')}</h2>
        <ul className="list-nav">
          {allLists.map((l) => (
            <li key={l.id}>
              <button
                type="button"
                className={`list-nav__item${l.id === selected?.id ? ' is-active' : ''}`}
                onClick={() => setSelectedId(l.id)}
              >
                <span className="dot" style={{ backgroundColor: colorHex(l.color) }} />
                <span className="list-nav__name">{l.name}</span>
                <span className="muted">{l.open_task_count}</span>
              </button>
            </li>
          ))}
        </ul>
        <button type="button" onClick={() => setListForm('new')}>
          {t('tasks.newList')}
        </button>
      </aside>

      <section className="grow">
        {selected && (
          <>
            <div className="page-header">
              <h1>{selected.name}</h1>
              <div className="row-actions">
                <button type="button" onClick={() => setListForm(selected)}>
                  {t('common.edit')}
                </button>
                <button type="button" onClick={() => setDeletingList(selected)}>
                  {t('common.delete')}
                </button>
                <button type="button" className="button--primary" onClick={() => setEditing('new')}>
                  {t('tasks.newTask')}
                </button>
              </div>
            </div>
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={showCompleted}
                onChange={(e) => setShowCompleted(e.target.checked)}
              />
              {t('tasks.showCompleted')}
            </label>
            {tasks.data?.length === 0 && <p className="muted">{t('tasks.empty')}</p>}
            <ul className="task-list">
              {tasks.data?.map((task) => (
                <TaskItem key={task.id} task={task} onEdit={setEditing} onDelete={setDeleting} />
              ))}
            </ul>
          </>
        )}
      </section>

      {editing && selected && (
        <Modal
          title={editing === 'new' ? t('tasks.createTask') : t('tasks.editTask')}
          onClose={() => setEditing(null)}
        >
          <TaskForm
            task={editing === 'new' ? undefined : editing}
            lists={allLists}
            defaultListId={selected.id}
            onDone={() => setEditing(null)}
          />
        </Modal>
      )}

      <ConfirmDialog
        open={deleting !== null}
        message={t('tasks.deleteTask', { title: deleting?.title ?? '' })}
        onCancel={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) deleteTask.mutate(deleting.id);
          setDeleting(null);
        }}
      />

      {listForm && (
        <Modal
          title={listForm === 'new' ? t('tasks.createList') : t('tasks.editList')}
          onClose={() => setListForm(null)}
        >
          <ListForm
            list={listForm === 'new' ? undefined : listForm}
            onDone={(id) => {
              setListForm(null);
              if (id) setSelectedId(id);
            }}
          />
        </Modal>
      )}

      {deletingList && (
        <DeleteListFlow
          list={deletingList}
          others={allLists.filter((l) => l.id !== deletingList.id)}
          onDone={() => {
            setDeletingList(null);
            setSelectedId(null);
          }}
          onCancel={() => setDeletingList(null)}
        />
      )}
    </div>
  );
}

function ListForm({ list, onDone }: { list?: TaskList; onDone: (id?: number) => void }) {
  const [name, setName] = useState(list?.name ?? '');
  const [color, setColor] = useState<string | null>(list?.color ?? null);
  const save = useSaveList();

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate(
      { id: list?.id, name: name.trim(), color: color ?? undefined },
      { onSuccess: (result) => onDone(result.data.id) },
    );
  }

  return (
    <form onSubmit={submit} noValidate>
      <FormField label={t('tasks.listName')} name="name" error={save.error}>
        <input autoFocus value={name} onChange={(e) => setName(e.target.value)} />
      </FormField>
      <FormField label={t('tasks.listColor')} name="color" error={save.error}>
        <ColorPicker value={color} onChange={setColor} />
      </FormField>
      <FormActions saving={save.isPending} onCancel={() => onDone()} />
    </form>
  );
}

/**
 * Xoá danh sách (FR-004, FR-027): hỏi xác nhận; nếu còn công việc (409) hoặc là danh sách "Học tập"
 * thì cho chọn chuyển công việc sang danh sách khác hoặc xoá luôn.
 */
function DeleteListFlow({
  list,
  others,
  onDone,
  onCancel,
}: {
  list: TaskList;
  others: TaskList[];
  onDone: () => void;
  onCancel: () => void;
}) {
  const remove = useDeleteList();
  const [choice, setChoice] = useState<{ taskCount: number; defaultList: boolean } | null>(null);
  const [moveTo, setMoveTo] = useState<number>(others[0]?.id ?? 0);

  function attempt() {
    remove.mutate(
      { id: list.id },
      {
        onSuccess: onDone,
        onError: (err) => {
          if (!(err instanceof ApiError)) return;
          if (err.status === 409) {
            setChoice({
              taskCount: (err.details as { task_count: number }).task_count,
              defaultList: false,
            });
          } else if (err.code === 'default_list_requires_replacement') {
            setChoice({ taskCount: 0, defaultList: true });
          }
        },
      },
    );
  }

  if (!choice) {
    return (
      <ConfirmDialog
        open
        message={t('tasks.deleteList', { name: list.name })}
        onCancel={onCancel}
        onConfirm={attempt}
      />
    );
  }

  return (
    <Modal title={t('confirm.deleteTitle')} onClose={onCancel}>
      <p>
        {choice.defaultList
          ? t('tasks.deleteListDefault', { name: list.name })
          : t('tasks.deleteListHasTasks', { name: list.name, count: choice.taskCount })}
      </p>
      <label className="field">
        <span className="field__label">{t('tasks.moveTo')}</span>
        <select value={moveTo} onChange={(e) => setMoveTo(Number(e.target.value))}>
          {others.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </select>
      </label>
      <div className="dialog__actions">
        <button type="button" onClick={onCancel}>
          {t('common.cancel')}
        </button>
        {!choice.defaultList && (
          <button
            type="button"
            className="button--danger"
            onClick={() => remove.mutate({ id: list.id, deleteTasks: true }, { onSuccess: onDone })}
          >
            {t('tasks.deleteWithTasks')}
          </button>
        )}
        <button
          type="button"
          className="button--primary"
          disabled={!moveTo}
          onClick={() => remove.mutate({ id: list.id, moveTo }, { onSuccess: onDone })}
        >
          {t('tasks.moveAndDelete')}
        </button>
      </div>
    </Modal>
  );
}
