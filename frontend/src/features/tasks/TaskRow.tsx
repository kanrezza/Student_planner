import { forwardRef } from 'react';
import type { Task } from '../../api/types';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { toIsoDate } from '../../lib/dates';
import { Checkbox } from '../../ui/Checkbox';
import { cx } from '../../ui/cx';
import { IconClock, IconRepeat, IconStarFilled } from '../../ui/icons';
import { isOverdue } from './groupTasks';
import { dueLabel, workLabel } from './taskFormat';

/**
 * Một dòng task (feature 002 FR-011): checkbox, ★, tiêu đề, chấm màu nhãn, biểu tượng Tự tạo,
 * khung giờ làm và giờ/ngày hạn canh phải (đỏ khi quá hạn).
 */
export const TaskRow = forwardRef<
  HTMLDivElement,
  {
    task: Task;
    now: Date;
    selected?: boolean;
    onToggle: (task: Task, completed: boolean) => void;
    onOpen: (task: Task) => void;
    onSelect?: (task: Task) => void;
  }
>(function TaskRow({ task, now, selected = false, onToggle, onOpen, onSelect }, ref) {
  const today = toIsoDate(now);
  const overdue = isOverdue(task, now);
  const due = dueLabel(task, today);
  const work = workLabel(task);
  return (
    <div
      ref={ref}
      role="option"
      aria-selected={selected}
      data-task-id={task.id}
      tabIndex={-1}
      onClick={() => {
        onSelect?.(task);
        onOpen(task);
      }}
      className={cx(
        'group flex min-h-9 items-center gap-2.5 rounded-lg px-2.5 py-1.5 outline-none',
        selected ? 'bg-accent-soft' : 'hover:bg-surface-2',
      )}
    >
      <Checkbox
        checked={task.completed}
        priority={task.priority}
        label={task.completed ? t('tasks.markUndone') : t('tasks.markDone')}
        onChange={(checked) => onToggle(task, checked)}
      />
      {task.is_important && (
        <span aria-label={t('important.label')} className="text-warning">
          <IconStarFilled size={14} />
        </span>
      )}
      <span
        className={cx(
          'min-w-0 flex-1 truncate',
          task.completed && 'text-muted line-through decoration-muted/60',
        )}
      >
        {task.title}
      </span>
      {task.is_auto && (
        <span aria-label={t('tasks.auto')} title={t('tasks.auto')} className="text-muted">
          <IconRepeat size={14} />
        </span>
      )}
      {task.tags.length > 0 && (
        <span
          aria-label={`${t('tags.title')}: ${task.tags.map((tag) => tag.name).join(', ')}`}
          className="flex items-center gap-0.5"
        >
          {task.tags.slice(0, 3).map((tag) => (
            <span
              key={tag.id}
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: colorHex(tag.color) }}
            />
          ))}
        </span>
      )}
      {work && (
        <span className="flex shrink-0 items-center gap-1 text-[12px] text-muted tabular-nums">
          <IconClock size={13} />
          {work}
        </span>
      )}
      {due && (
        <span
          className={cx(
            'shrink-0 text-[12px] tabular-nums',
            overdue ? 'text-danger' : task.completed ? 'text-muted' : 'text-accent',
          )}
        >
          {due}
        </span>
      )}
    </div>
  );
});
