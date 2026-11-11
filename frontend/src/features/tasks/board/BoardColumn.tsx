import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import type { ReactNode } from 'react';
import type { Task, TaskStatus } from '../../../api/types';
import { t } from '../../../i18n/vi';
import { cx } from '../../../ui/cx';
import { BoardCard } from './BoardCard';

/** Một cột của bảng: tiêu đề + số thẻ, danh sách thẻ sắp được, vùng thả khi cột rỗng. */
export function BoardColumn({
  status,
  tasks,
  today,
  selectedId,
  onSelect,
  onOpen,
  footer,
}: {
  status: TaskStatus;
  tasks: Task[];
  today: string;
  selectedId: number | null;
  onSelect: (id: number) => void;
  onOpen: (task: Task) => void;
  footer?: ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const name = t(`board.columns.${status}`);
  return (
    <section
      aria-label={t('board.columnLabel', { name, count: tasks.length })}
      data-status={status}
      className="flex min-h-0 min-w-[240px] flex-1 flex-col rounded-xl bg-surface-2"
    >
      <h2 className="flex shrink-0 items-baseline gap-2 px-3 pb-1 pt-3 text-[13px] font-semibold">
        {name}
        <span className="font-normal text-muted tabular-nums">{tasks.length}</span>
      </h2>
      <div
        ref={setNodeRef}
        className={cx(
          'flex min-h-[80px] flex-1 flex-col gap-2 overflow-y-auto px-2 pb-2 pt-1',
          isOver && 'bg-accent-soft/40',
        )}
      >
        <SortableContext
          items={tasks.map((task) => task.id)}
          strategy={verticalListSortingStrategy}
        >
          {tasks.map((task) => (
            <BoardCard
              key={task.id}
              task={task}
              today={today}
              selected={task.id === selectedId}
              onSelect={onSelect}
              onOpen={onOpen}
            />
          ))}
        </SortableContext>
        {tasks.length === 0 && (
          <p className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-[12px] text-muted">
            {t('board.dropHere')}
          </p>
        )}
      </div>
      {footer && <div className="shrink-0 px-3 pb-2">{footer}</div>}
    </section>
  );
}
