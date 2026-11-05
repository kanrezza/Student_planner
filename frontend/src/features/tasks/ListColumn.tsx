import { useState, type ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useLists } from '../../api/lists';
import { useTags } from '../../api/tags';
import { useTaskCounts, type SmartView, type TaskView } from '../../api/tasks';
import type { TaskList } from '../../api/types';
import { useNow } from '../../app/useNow';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { cx } from '../../ui/cx';
import { IconButton } from '../../ui/IconButton';
import {
  IconCheckCircle,
  IconInbox,
  IconList,
  IconMore,
  IconPlus,
  IconSunrise,
  IconTrash,
  IconWeek,
} from '../../ui/icons';
import { Menu, MenuItem } from '../../ui/Menu';
import { SearchBox } from '../search/SearchBox';
import { DeleteListDialog, ListDialog } from './ListDialog';
import { sameView, taskPath } from './viewRoutes';

/**
 * Cột danh sách của mục Công việc (feature 002 FR-008): danh sách thông minh có số đếm, danh sách
 * của người dùng (emoji, số đếm, menu ⋯), nhãn, rồi Đã hoàn thành và Thùng rác ở cuối.
 */
export function ListColumn({ current }: { current: TaskView | null }) {
  const counts = useTaskCounts().data;
  const lists = useLists().data ?? [];
  const tags = useTags().data ?? [];
  const navigate = useNavigate();
  const [editing, setEditing] = useState<TaskList | 'new' | null>(null);
  const [deleting, setDeleting] = useState<TaskList | null>(null);

  const smart = (view: SmartView, icon: ReactNode, count?: number) => (
    <Item
      key={view}
      to={taskPath({ kind: 'smart', view })}
      icon={icon}
      label={t(`smart.${view}`)}
      count={count}
    />
  );

  return (
    <nav
      aria-label={t('listColumn.label')}
      className="flex h-full w-[232px] shrink-0 flex-col border-r border-border bg-surface-2"
    >
      <div className="pt-[calc(12px+var(--titlebar-inset))]">
        <SearchBox />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3 pt-1">
        <div className="flex flex-col gap-px">
          {smart('today', <TodayIcon />, counts?.today)}
          {smart('tomorrow', <IconSunrise size={17} />, counts?.tomorrow)}
          {smart('next7', <IconWeek size={17} />, counts?.next7)}
          {smart('all', <IconInbox size={17} />, counts?.all)}
        </div>

        <SectionTitle
          title={t('smart.lists')}
          action={
            <IconButton
              label={t('listColumn.newList')}
              icon={<IconPlus size={14} />}
              size="sm"
              onClick={() => setEditing('new')}
            />
          }
        />
        <div className="flex flex-col gap-px">
          {lists.map((list) => (
            <Item
              key={list.id}
              to={taskPath({ kind: 'list', id: list.id })}
              icon={
                list.emoji ? (
                  <span className="text-[15px] leading-none">{list.emoji}</span>
                ) : (
                  <IconList size={17} style={{ color: colorHex(list.color) }} />
                )
              }
              label={list.name}
              count={counts?.lists[String(list.id)] ?? 0}
              menu={
                <Menu
                  trigger={
                    <button
                      type="button"
                      aria-label={t('listColumn.options', { name: list.name })}
                      className="flex h-5 w-5 items-center justify-center rounded text-muted opacity-0 hover:bg-surface-3 hover:text-text focus:opacity-100 group-hover:opacity-100 data-[state=open]:opacity-100"
                    >
                      <IconMore size={14} />
                    </button>
                  }
                >
                  <MenuItem onSelect={() => setEditing(list)}>{t('listColumn.edit')}</MenuItem>
                  <MenuItem danger onSelect={() => setDeleting(list)}>
                    {t('listColumn.delete')}
                  </MenuItem>
                </Menu>
              }
            />
          ))}
        </div>

        {tags.length > 0 && (
          <>
            <SectionTitle title={t('smart.tags')} />
            <div className="flex flex-col gap-px">
              {tags.map((tag) => (
                <Item
                  key={tag.id}
                  to={taskPath({ kind: 'tag', id: tag.id })}
                  icon={
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: colorHex(tag.color) }}
                    />
                  }
                  label={tag.name}
                />
              ))}
            </div>
          </>
        )}
      </div>

      <div className="flex flex-col gap-px border-t border-border px-2 py-2">
        {smart('completed', <IconCheckCircle size={17} />)}
        {smart('trash', <IconTrash size={17} />)}
      </div>

      {editing && (
        <ListDialog
          list={editing === 'new' ? undefined : editing}
          onDone={(saved) => {
            setEditing(null);
            if (saved && editing === 'new') navigate(taskPath({ kind: 'list', id: saved.id }));
          }}
        />
      )}
      {deleting && (
        <DeleteListDialog
          list={deleting}
          others={lists.filter((l) => l.id !== deleting.id)}
          onCancel={() => setDeleting(null)}
          onDone={() => {
            if (current && sameView(current, { kind: 'list', id: deleting.id })) {
              navigate(taskPath({ kind: 'smart', view: 'today' }));
            }
            setDeleting(null);
          }}
        />
      )}
    </nav>
  );
}

function Item({
  to,
  icon,
  label,
  count,
  menu,
}: {
  to: string;
  icon: ReactNode;
  label: string;
  count?: number;
  menu?: ReactNode;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cx(
          'group flex h-8 items-center gap-2.5 rounded-lg px-2 text-text',
          isActive ? 'bg-surface-3 font-medium' : 'hover:bg-surface-3/70',
        )
      }
    >
      <span className="flex w-5 shrink-0 items-center justify-center text-muted">{icon}</span>
      <span className="min-w-0 flex-1 truncate">{label}</span>
      {menu}
      {count !== undefined && count > 0 && (
        <span className="min-w-4 text-right text-[12px] text-muted tabular-nums">{count}</span>
      )}
    </NavLink>
  );
}

function SectionTitle({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="mt-4 mb-1 flex h-6 items-center justify-between pl-2 pr-1">
      <span className="text-[11px] font-semibold uppercase tracking-wide text-muted">{title}</span>
      {action}
    </div>
  );
}

/** Biểu tượng Hôm nay: tờ lịch nhỏ có số ngày hôm nay. */
function TodayIcon() {
  const { today } = useNow();
  return (
    <span className="relative flex h-[17px] w-[17px] items-end justify-center rounded-[4px] border-[1.5px] border-current pb-px text-[9px] font-bold leading-none text-accent">
      <span className="absolute inset-x-0 top-0 h-[3px] bg-current" />
      {Number(today.slice(8, 10))}
    </span>
  );
}
