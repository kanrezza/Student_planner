import { useEffect, useMemo, type ReactNode } from 'react';
import { useSmartTasks, type TaskView } from '../../api/tasks';
import type { Task } from '../../api/types';
import { useHotkeys } from '../../app/useHotkeys';
import { useNow } from '../../app/useNow';
import { t } from '../../i18n/vi';
import { EmptyState } from '../../ui/EmptyState';
import { IconChecklist } from '../../ui/icons';
import { groupCompleted, groupTasks } from './groupTasks';
import { QuickAdd } from './QuickAdd';
import { hasQuickAdd } from './quickAddDefaults';
import { TaskGroups, useCollapsedGroups, visibleTasks } from './TaskGroups';
import { TaskRow } from './TaskRow';
import { TodaySchedule } from './TodaySchedule';
import { TrashView } from './TrashView';
import { useTaskActions } from './useTaskActions';
import { viewStorageKey } from './viewRoutes';

function emptyText(view: TaskView): string {
  if (view.kind === 'list') return t('smart.emptyList');
  if (view.kind === 'tag') return t('smart.emptyTag');
  const key = {
    today: 'emptyToday',
    tomorrow: 'emptyTomorrow',
    next7: 'emptyNext7',
    all: 'emptyAll',
    completed: 'emptyCompleted',
    trash: 'emptyAll',
  }[view.view];
  return t(`smart.${key}`);
}

/**
 * Khu vực chính của mục Công việc (feature 002 FR-010 đến FR-012, FR-014, FR-016): tiêu đề lớn,
 * ô thêm nhanh, khối "Lịch hôm nay", các nhóm task; Thùng rác có giao diện riêng.
 * Phím: ↑/↓ chọn, ↩ mở chi tiết, ⌘↩ hoàn thành, ⌘⌫ chuyển vào Thùng rác.
 */
export function SmartListView({
  view,
  title,
  headerStart,
  headerEnd,
  selectedId,
  onSelect,
  onOpen,
  openId,
}: {
  view: TaskView;
  title: string;
  headerStart?: ReactNode;
  headerEnd?: ReactNode;
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onOpen: (task: Task) => void;
  openId: number | null;
}) {
  const { now, today } = useNow();
  const query = useSmartTasks(view);
  const tasks = useMemo(() => query.data ?? [], [query.data]);
  const actions = useTaskActions();
  const storageKey = viewStorageKey(view);
  const [collapsed, setCollapsed] = useCollapsedGroups(storageKey);
  const isTrash = view.kind === 'smart' && view.view === 'trash';
  const isCompleted = view.kind === 'smart' && view.view === 'completed';
  const isToday = view.kind === 'smart' && view.view === 'today';

  const groups = useMemo(
    () => (isCompleted ? groupCompleted(tasks, now) : groupTasks(tasks, now)),
    [isCompleted, tasks, now],
  );
  const ordered = useMemo(() => visibleTasks(groups, collapsed), [groups, collapsed]);
  const active = selectedId ?? openId;
  const activeTask = ordered.find((task) => task.id === active) ?? null;

  useEffect(() => {
    if (active === null) return;
    document.querySelector(`[data-task-id="${active}"]`)?.scrollIntoView?.({ block: 'nearest' });
  }, [active]);

  function move(step: number) {
    if (ordered.length === 0) return;
    const index = ordered.findIndex((task) => task.id === active);
    const next = index === -1 ? (step > 0 ? 0 : ordered.length - 1) : index + step;
    const target = ordered[Math.min(Math.max(next, 0), ordered.length - 1)];
    onSelect(target.id);
  }

  useHotkeys([
    { key: 'ArrowDown', handler: () => move(1), enabled: !isTrash },
    { key: 'ArrowUp', handler: () => move(-1), enabled: !isTrash },
    {
      key: 'Enter',
      handler: () => (activeTask ? onOpen(activeTask) : false),
      enabled: !isTrash,
    },
    {
      key: 'Enter',
      meta: true,
      handler: () => (activeTask ? actions.toggleComplete(activeTask) : false),
      enabled: !isTrash,
    },
    {
      key: 'Backspace',
      meta: true,
      handler: () => {
        if (!activeTask) return false;
        const index = ordered.indexOf(activeTask);
        const neighbour = ordered[index + 1] ?? ordered[index - 1] ?? null;
        actions.trash(activeTask, () => onSelect(neighbour?.id ?? null));
      },
      enabled: !isTrash,
    },
  ]);

  return (
    <div className="flex h-full min-w-0 flex-1 flex-col">
      <header className="flex shrink-0 items-center gap-2 px-8 pb-3 pt-[calc(20px+var(--titlebar-inset))]">
        {headerStart}
        <h1 className="min-w-0 flex-1 truncate text-[22px] leading-8 font-bold tracking-tight">
          {title}
        </h1>
        {headerEnd}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-8 pb-10">
        <div className="mx-auto flex max-w-[760px] flex-col gap-4">
          {hasQuickAdd(view) && <QuickAdd view={view} today={today} />}
          {isToday && <TodaySchedule />}
          {query.isLoading ? (
            <p className="text-muted">{t('common.loading')}</p>
          ) : query.isError ? (
            <p className="text-danger">{query.error.message}</p>
          ) : isTrash ? (
            <TrashView tasks={tasks} />
          ) : groups.length === 0 ? (
            <EmptyState
              icon={<IconChecklist size={44} />}
              title={emptyText(view)}
              description={
                isCompleted ? undefined : isToday ? t('smart.emptyTodayHelp') : t('smart.emptyHelp')
              }
            />
          ) : (
            <TaskGroups
              groups={groups}
              collapsed={collapsed}
              onCollapsedChange={setCollapsed}
              renderTask={(task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  now={now}
                  selected={task.id === active}
                  onSelect={(item) => onSelect(item.id)}
                  onOpen={onOpen}
                  onToggle={(item, completed) => actions.toggleComplete(item, completed)}
                />
              )}
            />
          )}
        </div>
      </div>
    </div>
  );
}
