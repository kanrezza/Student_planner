import type { ReactNode } from 'react';
import type { Task } from '../../api/types';
import { t } from '../../i18n/vi';
import { useStoredState } from '../../lib/storage';
import { cx } from '../../ui/cx';
import { IconChevronDown } from '../../ui/icons';
import type { TaskGroup } from './groupTasks';

/**
 * Các nhóm task (FR-010): tiêu đề đậm kèm số lượng, mũi tên thu gọn; trạng thái thu gọn được nhớ
 * theo view và nhóm.
 */
export type Collapsed = Record<string, boolean>;

/** Trạng thái thu gọn của các nhóm, nhớ theo view. */
export function useCollapsedGroups(storageKey: string) {
  return useStoredState<Collapsed>(`collapsed.${storageKey}`, {});
}

export function TaskGroups({
  groups,
  collapsed,
  onCollapsedChange,
  renderTask,
}: {
  groups: TaskGroup[];
  collapsed: Collapsed;
  onCollapsedChange: (next: Collapsed) => void;
  renderTask: (task: Task) => ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4">
      {groups.map((group) => {
        const closed = collapsed[group.key] === true;
        return (
          <section key={group.key} aria-label={group.title}>
            <button
              type="button"
              aria-expanded={!closed}
              aria-label={t(closed ? 'groups.expand' : 'groups.collapse', { name: group.title })}
              onClick={() => onCollapsedChange({ ...collapsed, [group.key]: !closed })}
              className="flex h-7 w-full items-center gap-1.5 rounded-md px-1 text-left hover:bg-surface-2"
            >
              <IconChevronDown
                size={14}
                className={cx('text-muted transition-transform', closed && '-rotate-90')}
              />
              <span
                className={cx(
                  'font-semibold',
                  group.tone === 'danger' ? 'text-danger' : 'text-text',
                )}
              >
                {group.title}
              </span>
              <span className="text-[12px] text-muted">{group.tasks.length}</span>
            </button>
            {!closed && (
              <div role="listbox" aria-label={group.title} className="mt-0.5 flex flex-col">
                {group.tasks.map((task) => renderTask(task))}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}

/** Task đang hiện (bỏ nhóm thu gọn) theo đúng thứ tự trên màn hình — dùng cho ↑/↓. */
export function visibleTasks(groups: TaskGroup[], collapsed: Collapsed): Task[] {
  return groups.filter((g) => !collapsed[g.key]).flatMap((g) => g.tasks);
}
