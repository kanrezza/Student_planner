import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { keys } from '../../api/keys';
import { useLists } from '../../api/lists';
import { useCreateTask, viewKey, type TaskView } from '../../api/tasks';
import type { Task, TaskCounts } from '../../api/types';
import { useShell } from '../../app/shell';
import { t } from '../../i18n/vi';
import { IconPlus } from '../../ui/icons';
import { useToast } from '../../ui/Toast';
import { quickAddDefaults, quickAddInput } from './quickAddDefaults';

let tempId = -1;

/** Task tạm hiện ngay trong danh sách trong lúc chờ API (cập nhật lạc quan). */
function placeholderTask(input: ReturnType<typeof quickAddInput>): Task {
  return {
    id: tempId--,
    title: input.title,
    notes: null,
    due_date: input.due_date,
    due_time: null,
    due_at: input.due_date ? `${input.due_date}T23:59:00+07:00` : null,
    priority: 2,
    list_id: input.list_id,
    list_name: '',
    completed: false,
    completed_at: null,
    is_overdue: false,
    is_auto: false,
    source_session_id: null,
    user_modified: false,
    tags: [],
    display_color: 'c11',
    reminder_minutes: null,
    reminder_at: null,
    reminder_times: [],
    is_important: false,
    work_date: null,
    work_start: null,
    work_end: null,
    deleted_at: null,
    days_left_in_trash: null,
    trashed_from_list_name: null,
  };
}

/**
 * Ô "Thêm công việc" (feature 002 US3, FR-016, FR-017): Enter là tạo với mặc định theo view,
 * ô được xoá trống và giữ con trỏ; Enter với ô trống không làm gì; Esc bỏ chọn ô.
 */
export function QuickAdd({ view, today }: { view: TaskView; today: string }) {
  const [title, setTitle] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();
  const lists = useLists();
  const create = useCreateTask();
  const toast = useToast();
  const { registerQuickAdd } = useShell();
  const studyListId = lists.data?.find((l) => l.is_default_study)?.id;

  useEffect(() => registerQuickAdd(() => inputRef.current?.focus()), [registerQuickAdd]);

  function submit() {
    if (title.trim() === '' || studyListId === undefined) return;
    const input = quickAddInput(title, quickAddDefaults(view, today, studyListId));
    const key = viewKey(view);
    qc.setQueryData<Task[]>(key, (old) => (old ? [...old, placeholderTask(input)] : old));
    qc.setQueryData<TaskCounts>(keys.taskCounts, (old) =>
      old ? { ...old, all: old.all + 1 } : old,
    );
    setTitle('');
    create.mutate(input, {
      onError: (err) => {
        toast.show(t('quickAdd.failed', { message: err.message }), { tone: 'danger' });
        setTitle((current) => current || input.title); // trả lại chữ để gõ lại không mất công
      },
    });
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    } else if (e.key === 'Escape') {
      e.preventDefault(); // không đóng bảng chi tiết cùng lúc
      inputRef.current?.blur();
    }
  }

  return (
    <label className="group flex h-10 items-center gap-2 rounded-lg bg-surface-2 px-3 text-muted transition-colors focus-within:bg-surface focus-within:ring-2 focus-within:ring-accent/30 hover:bg-surface-3">
      <IconPlus size={16} className="text-accent" />
      <input
        ref={inputRef}
        value={title}
        maxLength={300}
        aria-label={t('quickAdd.label')}
        placeholder={t('quickAdd.placeholder')}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={onKeyDown}
        className="h-full flex-1 border-0 bg-transparent px-0 text-[13px] text-text shadow-none focus:shadow-none"
      />
    </label>
  );
}
