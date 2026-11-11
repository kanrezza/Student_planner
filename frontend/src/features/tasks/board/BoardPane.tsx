import type { ReactNode } from 'react';
import type { BoardFilters } from '../../../api/board';
import { NO_FILTERS } from '../../../api/board';
import type { TaskView } from '../../../api/tasks';
import type { Task } from '../../../api/types';
import { useNow } from '../../../app/useNow';
import { QuickAdd } from '../QuickAdd';
import { hasQuickAdd } from '../quickAddDefaults';
import { BoardView } from './BoardView';

/** Bộ lọc suy ra từ view đang xem: danh sách/nhãn của cột bên trái thu hẹp bảng. */
export function viewFilters(view: TaskView, stored: BoardFilters = NO_FILTERS): BoardFilters {
  if (view.kind === 'list') return { ...stored, list_ids: [view.id] };
  if (view.kind === 'tag') return { ...stored, tag_ids: [view.id] };
  return stored;
}

/** Khu vực chính khi chọn dạng Bảng: tiêu đề, công tắc dạng xem, ô thêm nhanh và bảng. */
export function BoardPane({
  view,
  title,
  headerStart,
  headerEnd,
  selectedId,
  onSelect,
  onOpen,
}: {
  view: TaskView;
  title: string;
  headerStart?: ReactNode;
  headerEnd?: ReactNode;
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onOpen: (task: Task) => void;
}) {
  const { today } = useNow();
  return (
    <div className="flex h-full min-w-0 flex-1 flex-col">
      <header className="flex shrink-0 items-center gap-2 px-8 pb-3 pt-[calc(20px+var(--titlebar-inset))]">
        {headerStart}
        <h1 className="min-w-0 flex-1 truncate text-[22px] leading-8 font-bold tracking-tight">
          {title}
        </h1>
        {headerEnd}
      </header>
      {hasQuickAdd(view) && (
        <div className="shrink-0 px-8 pb-3">
          <QuickAdd view={view} today={today} />
        </div>
      )}
      <BoardView
        filters={viewFilters(view)}
        selectedId={selectedId}
        onSelect={onSelect}
        onOpen={onOpen}
      />
    </div>
  );
}
