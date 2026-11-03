import { useCompleteTask } from '../api/tasks';
import type { Task } from '../api/types';
import { t } from '../i18n/vi';
import { colorHex } from '../lib/colors';
import { formatDue, priorityLabel } from '../lib/format';
import { SessionLink } from './SessionLink';

/** Một dòng công việc: checkbox hoàn thành, tiêu đề, hạn, ưu tiên (FR-003, FR-006). */
export function TaskItem({
  task,
  showList = false,
  onEdit,
  onDelete,
}: {
  task: Task;
  showList?: boolean;
  onEdit?: (task: Task) => void;
  onDelete?: (task: Task) => void;
}) {
  const complete = useCompleteTask();
  return (
    <li className={`task-item${task.completed ? ' is-done' : ''}`}>
      <span className="color-bar" style={{ backgroundColor: colorHex(task.display_color) }} />
      <input
        type="checkbox"
        checked={task.completed}
        disabled={complete.isPending}
        aria-label={task.completed ? t('tasks.markUndone') : t('tasks.markDone')}
        onChange={() => complete.mutate({ id: task.id, completed: !task.completed })}
      />
      <div className="task-item__body">
        <div className="task-item__title">{task.title}</div>
        <div className="task-item__meta">
          <span className={task.is_overdue ? 'text-danger' : undefined}>{formatDue(task)}</span>
          <span className={`badge badge--p${task.priority}`}>{priorityLabel(task.priority)}</span>
          {task.is_overdue && <span className="badge badge--danger">{t('tasks.overdue')}</span>}
          {task.is_auto && <span className="badge">{t('tasks.auto')}</span>}
          {task.is_auto && task.source_session_id && (
            <SessionLink sessionId={task.source_session_id} />
          )}
          {showList && <span className="muted">{task.list_name}</span>}
        </div>
        {task.notes && <div className="task-item__notes">{task.notes}</div>}
      </div>
      {(onEdit || onDelete) && (
        <div className="row-actions">
          {onEdit && (
            <button type="button" onClick={() => onEdit(task)}>
              {t('common.edit')}
            </button>
          )}
          {onDelete && (
            <button type="button" onClick={() => onDelete(task)}>
              {t('common.delete')}
            </button>
          )}
        </div>
      )}
    </li>
  );
}
