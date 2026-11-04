/** Thao tác thường dùng trên một task, kèm thông báo và Hoàn tác (FR-029, FR-030). */
import { useCallback } from 'react';
import { useCompleteTask, useRestoreTask, useTrashTask } from '../../api/tasks';
import type { Task } from '../../api/types';
import { t } from '../../i18n/vi';
import { useToast } from '../../ui/Toast';

export function useTaskActions() {
  const complete = useCompleteTask();
  const trashTask = useTrashTask();
  const restoreTask = useRestoreTask();
  const toast = useToast();

  const toggleComplete = useCallback(
    (task: Task, completed: boolean = !task.completed) => {
      complete.mutate(
        { id: task.id, completed },
        { onError: (err) => toast.show(err.message, { tone: 'danger' }) },
      );
    },
    [complete, toast],
  );

  const restore = useCallback(
    (task: Task, announce = true) => {
      restoreTask.mutate(task.id, {
        onSuccess: ({ warnings }) => {
          for (const warning of warnings) toast.show(warning.message, { tone: 'warning' });
          if (announce && warnings.length === 0)
            toast.show(t('trash.restored', { title: task.title }));
        },
        onError: (err) => toast.show(err.message, { tone: 'danger' }),
      });
    },
    [restoreTask, toast],
  );

  /** Chuyển vào Thùng rác ngay, không hỏi; thông báo có nút Hoàn tác trong 5 giây. */
  const trash = useCallback(
    (task: Task, onDone?: () => void) => {
      trashTask.mutate(task.id, {
        onSuccess: () => {
          onDone?.();
          toast.show(t('trash.moved', { title: task.title }), {
            action: { label: t('trash.undo'), onClick: () => restore(task, false) },
          });
        },
        onError: (err) => toast.show(err.message, { tone: 'danger' }),
      });
    },
    [trashTask, toast, restore],
  );

  return { toggleComplete, trash, restore };
}
