import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
  type Announcements,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable';
import { useQueryClient } from '@tanstack/react-query';
import { useMemo, useState, type ReactNode } from 'react';
import {
  boardKey,
  useBoard,
  useMoveCard,
  type BoardData,
  type BoardFilters,
  type MoveInput,
} from '../../../api/board';
import type { Task, TaskStatus } from '../../../api/types';
import { useNow } from '../../../app/useNow';
import { useStoredState } from '../../../lib/storage';
import { t } from '../../../i18n/vi';
import { Button } from '../../../ui/Button';
import { useToast } from '../../../ui/Toast';
import { CardBody } from './BoardCard';
import { BoardColumn } from './BoardColumn';
import { STATUS_ORDER, applyMove, locate, neighbours, emptyColumns } from './boardState';

/** Bảng Kanban của trang Công việc (feature 005 US1): 3 cột, kéo thả, Xong = tick, Hoàn tác. */
export function BoardView({
  filters,
  selectedId,
  onSelect,
  onOpen,
  toolbar,
}: {
  filters: BoardFilters;
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onOpen: (task: Task) => void;
  toolbar?: ReactNode;
}) {
  const { today } = useNow();
  const toast = useToast();
  const qc = useQueryClient();
  const [doneAll, setDoneAll] = useStoredState('board.doneAll', false);
  const query = useBoard(filters, doneAll);
  const move = useMoveCard();
  const [dragged, setDragged] = useState<Task | null>(null);
  const columns = query.data?.columns ?? emptyColumns();
  const key = boardKey(filters, doneAll);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const announcements: Announcements = useMemo(() => {
    const where = (id: number | string) => {
      const found = locate(columns, Number(id));
      if (!found && typeof id === 'string' && STATUS_ORDER.includes(id as TaskStatus))
        return { name: t(`board.columns.${id}`), position: 1, total: 1 };
      if (!found) return null;
      return {
        name: t(`board.columns.${found.status}`),
        position: found.index + 1,
        total: columns[found.status].length,
      };
    };
    const title = (id: number | string) =>
      Object.values(columns)
        .flat()
        .find((task) => task.id === Number(id))?.title ?? '';
    return {
      onDragStart: ({ active }) => t('board.announce.pick', { title: title(active.id) }),
      onDragOver: ({ active, over }) => {
        const w = over ? where(over.id) : null;
        return w
          ? t('board.announce.over', {
              title: title(active.id),
              column: w.name,
              position: w.position,
              total: w.total,
            })
          : undefined;
      },
      onDragEnd: ({ active, over }) => {
        const w = over ? where(over.id) : null;
        return w
          ? t('board.announce.drop', {
              title: title(active.id),
              column: w.name,
              position: w.position,
              total: w.total,
            })
          : undefined;
      },
      onDragCancel: ({ active }) => t('board.announce.cancel', { title: title(active.id) }),
    };
  }, [columns]);

  /** Gửi lên máy chủ; cập nhật lạc quan, lỗi thì hoàn lại và báo. */
  function send(input: MoveInput, optimistic: ((data: BoardData) => BoardData) | null) {
    const previous = qc.getQueryData<BoardData>(key);
    if (optimistic && previous) qc.setQueryData<BoardData>(key, optimistic(previous));
    const task = Object.values(columns)
      .flat()
      .find((item) => item.id === input.id);
    move.mutate(input, {
      onSuccess: (result) => {
        if (input.status === 'done' && task) {
          const undo = result.data.undo;
          toast.show(t('board.doneToast', { title: task.title }), {
            action: {
              label: t('board.undo'),
              onClick: () => send({ id: input.id, ...undo }, null),
            },
          });
        }
      },
      onError: (err) => {
        if (previous) qc.setQueryData(key, previous);
        toast.show(t('board.moveFailed', { message: err.message }), { tone: 'danger' });
      },
    });
  }

  function placeCard(id: number, to: TaskStatus, index: number) {
    const next = applyMove(columns, id, to, index);
    const { before_id, after_id } = neighbours(next, id);
    send({ id, status: to, before_id, after_id }, (data) => ({
      ...data,
      columns: applyMove(data.columns, id, to, index),
    }));
  }

  function onDragEnd({ active, over }: DragEndEvent) {
    setDragged(null);
    if (!over) return;
    const id = Number(active.id);
    const from = locate(columns, id);
    if (!from) return;
    const overId = over.id;
    if (typeof overId === 'string') {
      // Thả vào vùng cột (cuối cột; cột rỗng thì vị trí 0).
      const to = overId as TaskStatus;
      if (!STATUS_ORDER.includes(to)) return;
      const length = columns[to].filter((task) => task.id !== id).length;
      if (to === from.status && from.index === length) return;
      placeCard(id, to, length);
      return;
    }
    const target = locate(columns, Number(overId));
    if (!target || (target.status === from.status && target.index === from.index)) return;
    placeCard(id, target.status, target.index);
  }

  function onDragStart({ active }: DragStartEvent) {
    const task = Object.values(columns)
      .flat()
      .find((item) => item.id === Number(active.id));
    setDragged(task ?? null);
    if (task) onSelect(task.id);
  }

  const hidden = query.data?.done_hidden_count ?? 0;
  const doneFooter =
    doneAll || hidden > 0 ? (
      <Button size="sm" variant="ghost" onClick={() => setDoneAll(!doneAll)}>
        {doneAll ? t('board.onlyRecentDone') : t('board.showAllDone', { count: hidden })}
      </Button>
    ) : null;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 px-8 pb-6">
      {toolbar}
      {query.isLoading ? (
        <p className="text-muted">{t('common.loading')}</p>
      ) : query.isError ? (
        <p className="text-danger">{query.error.message}</p>
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          accessibility={{
            announcements,
            screenReaderInstructions: { draggable: t('board.announce.instructions') },
          }}
          onDragStart={onDragStart}
          onDragEnd={onDragEnd}
          onDragCancel={() => setDragged(null)}
        >
          <div
            role="group"
            aria-label={t('board.cardsLabel')}
            className="flex min-h-0 flex-1 gap-3 overflow-x-auto"
          >
            {STATUS_ORDER.map((status) => (
              <BoardColumn
                key={status}
                status={status}
                tasks={columns[status]}
                today={today}
                selectedId={selectedId}
                onSelect={onSelect}
                onOpen={onOpen}
                footer={status === 'done' ? doneFooter : null}
              />
            ))}
          </div>
          <DragOverlay>
            {dragged ? (
              <div className="rounded-lg border border-accent bg-surface px-3 py-2 shadow-panel">
                <CardBody task={dragged} today={today} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      )}
    </div>
  );
}
