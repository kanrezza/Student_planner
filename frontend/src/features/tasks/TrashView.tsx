import { useState } from 'react';
import { useDeletePermanently, useEmptyTrash } from '../../api/tasks';
import type { Task } from '../../api/types';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { t } from '../../i18n/vi';
import { formatDayLong } from '../../lib/dates';
import { Button } from '../../ui/Button';
import { EmptyState } from '../../ui/EmptyState';
import { IconTrash } from '../../ui/icons';
import { useToast } from '../../ui/Toast';
import { useTaskActions } from './useTaskActions';

/**
 * Thùng rác (feature 002 US7): ngày xoá, "Còn N ngày", Khôi phục, Xoá vĩnh viễn và Dọn sạch
 * (hai thao tác sau hỏi xác nhận).
 */
export function TrashView({ tasks }: { tasks: Task[] }) {
  const { restore } = useTaskActions();
  const deleteForever = useDeletePermanently();
  const emptyTrash = useEmptyTrash();
  const toast = useToast();
  const [confirm, setConfirm] = useState<Task | 'all' | null>(null);

  if (tasks.length === 0) {
    return (
      <EmptyState
        icon={<IconTrash size={44} />}
        title={t('trash.empty')}
        description={t('trash.emptyHelp')}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-muted">{t('trash.help')}</p>
        <Button variant="danger" size="sm" onClick={() => setConfirm('all')}>
          {t('trash.emptyAll')}
        </Button>
      </div>
      <ul className="flex flex-col divide-y divide-border rounded-xl border border-border">
        {tasks.map((task) => (
          <li key={task.id} className="flex items-center gap-3 px-3 py-2.5">
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">{task.title}</p>
              <p className="truncate text-[12px] text-muted">
                {task.deleted_at && t('trash.deletedOn', { date: formatDayLong(task.deleted_at) })}
                {' · '}
                {task.trashed_from_list_name
                  ? t('trash.fromList', { name: task.trashed_from_list_name })
                  : task.list_name}
              </p>
            </div>
            <span className="shrink-0 text-[12px] text-muted tabular-nums">
              {t('trash.daysLeft', { n: task.days_left_in_trash ?? 0 })}
            </span>
            <Button size="sm" onClick={() => restore(task)}>
              {t('trash.restore')}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setConfirm(task)}>
              {t('trash.deleteForever')}
            </Button>
          </li>
        ))}
      </ul>

      <ConfirmDialog
        open={confirm !== null}
        message={
          confirm === 'all'
            ? t('trash.confirmEmpty', { n: tasks.length })
            : t('trash.confirmDeleteForever', { title: confirm?.title ?? '' })
        }
        confirmLabel={confirm === 'all' ? t('trash.emptyAll') : t('trash.deleteForever')}
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          if (confirm === 'all') {
            emptyTrash.mutate(undefined, { onSuccess: () => toast.show(t('trash.emptied')) });
          } else if (confirm) {
            deleteForever.mutate(confirm.id);
          }
          setConfirm(null);
        }}
      />
    </div>
  );
}
