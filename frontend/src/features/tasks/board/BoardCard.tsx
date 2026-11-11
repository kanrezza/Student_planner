import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Task } from '../../../api/types';
import { t } from '../../../i18n/vi';
import { colorHex } from '../../../lib/colors';
import { cx } from '../../../ui/cx';
import { IconPaperclip, IconRepeat, IconStarFilled } from '../../../ui/icons';
import { dueLabel } from '../taskFormat';
import { describeRule } from '../recurrence/describeRule';

/** Nội dung một thẻ (dùng cả khi kéo): tiêu đề, hạn chót, nhãn màu, Quan trọng, lặp, số file. */
export function CardBody({ task, today }: { task: Task; today: string }) {
  const done = task.status === 'done' || task.completed;
  const due = dueLabel(task, today);
  const overdue = task.is_overdue && !done;
  const dueToday = task.due_date === today && !done;
  return (
    <>
      <div className="flex items-start gap-1.5">
        {task.is_important && (
          <span aria-label={t('important.label')} className="mt-0.5 text-warning">
            <IconStarFilled size={13} />
          </span>
        )}
        <p
          className={cx(
            'line-clamp-2 min-w-0 flex-1 break-words font-medium',
            done && 'text-muted line-through decoration-muted/60',
          )}
        >
          {task.title}
        </p>
      </div>
      <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px]">
        {due && (
          <span
            className={cx(
              'tabular-nums',
              overdue ? 'text-danger' : dueToday ? 'text-warning' : 'text-muted',
            )}
          >
            {due}
          </span>
        )}
        {task.recurrence && (
          <span
            aria-label={t('recurrence.icon')}
            title={describeRule(task.recurrence)}
            className="text-muted"
          >
            <IconRepeat size={13} />
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
            {task.tags.length > 3 && <span className="text-muted">+{task.tags.length - 3}</span>}
          </span>
        )}
        {(task.attachment_count ?? 0) > 0 && (
          <span
            className="flex items-center gap-0.5 text-muted"
            aria-label={t('attachments.count', { count: task.attachment_count ?? 0 })}
          >
            <IconPaperclip size={13} />
            {task.attachment_count}
          </span>
        )}
      </div>
    </>
  );
}

/** Thẻ kéo thả được trong một cột; bấm mở chi tiết, Enter mở khi đang chọn. */
export function BoardCard({
  task,
  today,
  selected,
  onSelect,
  onOpen,
}: {
  task: Task;
  today: string;
  selected: boolean;
  onSelect: (id: number) => void;
  onOpen: (task: Task) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: task.id,
  });
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      data-task-id={task.id}
      {...attributes}
      {...listeners}
      onClick={() => {
        onSelect(task.id);
        onOpen(task);
      }}
      className={cx(
        'cursor-grab rounded-lg border bg-surface px-3 py-2 shadow-sm outline-none',
        selected ? 'border-accent ring-1 ring-accent' : 'border-border hover:border-border-strong',
        isDragging && 'opacity-40',
        task.status === 'done' && 'opacity-70',
      )}
    >
      <CardBody task={task} today={today} />
    </div>
  );
}
