import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  SEARCH_GROUPS,
  useSearchGroup,
  type SearchGroupName,
  type SearchItems,
  type SearchResponse,
} from '../../api/search';
import { t } from '../../i18n/vi';
import { colorHex } from '../../lib/colors';
import { formatDayLong, formatTime } from '../../lib/dates';
import { cx } from '../../ui/cx';
import { useTaskActions } from '../tasks/useTaskActions';
import { TaskRow } from '../tasks/TaskRow';
import { Highlighted } from './Highlighted';
import { SEARCH_KEY_EVENT, resultPath, type SearchKey } from './searchRoute';

type Entry = { id: string; open: () => void };

/** Một dòng kết quả không phải task: dải màu/biểu tượng, tiêu đề tô sáng, phụ đề. */
function ResultRow({
  entryId,
  active,
  leading,
  title,
  meta,
  dim,
  onOpen,
}: {
  entryId: string;
  active: boolean;
  leading: ReactNode;
  title: ReactNode;
  meta?: ReactNode;
  dim?: boolean;
  onOpen: () => void;
}) {
  return (
    <div
      role="option"
      aria-selected={active}
      data-entry={entryId}
      onClick={onOpen}
      className={cx(
        'flex min-h-9 cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-1.5',
        active ? 'bg-accent-soft' : 'hover:bg-surface-2',
        dim && 'opacity-60',
      )}
    >
      <span className="flex w-5 shrink-0 items-center justify-center">{leading}</span>
      <span className="min-w-0 flex-1 truncate">{title}</span>
      {meta && <span className="shrink-0 text-[12px] text-muted">{meta}</span>}
    </div>
  );
}

const Dot = ({ color }: { color: string }) => (
  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: colorHex(color) }} />
);

function sessionWhen(startAt: string): string {
  return `${formatTime(startAt)} ${formatDayLong(startAt)}`;
}

type SectionProps<K extends SearchGroupName> = {
  group: K;
  total: number;
  firstItems: SearchItems[K][];
  query: string;
  includeDone: boolean;
  now: Date;
  activeId: string | null;
  openTask: (id: number) => void;
  openSession: (id: number) => void;
  report: (group: SearchGroupName, entries: Entry[]) => void;
};

function GroupSection<K extends SearchGroupName>(props: SectionProps<K>) {
  const { group, total, firstItems, query, includeDone, now, activeId } = props;
  const navigate = useNavigate();
  const actions = useTaskActions();
  const [expanded, setExpanded] = useState(false);
  const more = useSearchGroup(query, includeDone, group, expanded);
  const items = (expanded && more.data ? more.data.items : firstItems) as SearchItems[K][];

  const rows = items.map((item) => {
    const id = `${group}:${(item as { id: number }).id}`;
    return { item, id };
  });
  const { report, openTask, openSession } = props;

  const entries = useMemo<Entry[]>(
    () =>
      rows.map(({ item, id }) => ({
        id,
        open: () => {
          switch (group) {
            case 'tasks':
              return openTask((item as SearchItems['tasks']).id);
            case 'sessions':
              return openSession((item as SearchItems['sessions']).id);
            case 'lists':
              return navigate(resultPath({ type: 'list', id: (item as SearchItems['lists']).id }));
            case 'tags':
              return navigate(resultPath({ type: 'tag', id: (item as SearchItems['tags']).id }));
            case 'subjects': {
              const subject = item as SearchItems['subjects'];
              return navigate(
                resultPath({ type: 'subject', id: subject.id, semesterId: subject.semester_id }),
              );
            }
            case 'exams':
              return navigate(resultPath({ type: 'exam', id: (item as SearchItems['exams']).id }));
          }
        },
      })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [items, group],
  );
  useEffect(() => report(group, entries), [group, entries, report]);

  if (total === 0) return null;

  return (
    <section aria-label={t(`search.groups.${group}`)} className="flex flex-col gap-0.5">
      <h2 className="px-2.5 pb-1 pt-3 text-[12px] font-semibold uppercase tracking-wide text-muted">
        {t(`search.groups.${group}`)} <span className="font-normal">({total})</span>
      </h2>
      {rows.map(({ item, id }) => {
        const active = activeId === id;
        const open = entries.find((entry) => entry.id === id)?.open ?? (() => undefined);
        switch (group) {
          case 'tasks': {
            const task = item as SearchItems['tasks'];
            return (
              <div key={id} data-entry={id}>
                <TaskRow
                  task={task}
                  now={now}
                  selected={active}
                  highlight={query}
                  onToggle={(row, completed) => actions.toggleComplete(row, completed)}
                  onOpen={open}
                />
                {task.snippet && (
                  <p className="-mt-1 truncate pb-1 pl-[42px] pr-3 text-[12px] text-muted">
                    <Highlighted text={task.snippet} query={query} />
                  </p>
                )}
              </div>
            );
          }
          case 'lists': {
            const list = item as SearchItems['lists'];
            return (
              <ResultRow
                key={id}
                entryId={id}
                active={active}
                leading={<span className="text-[15px] leading-none">{list.emoji ?? '📋'}</span>}
                title={<Highlighted text={list.name} query={query} />}
                meta={t('search.openTasks', { n: list.open_count })}
                onOpen={open}
              />
            );
          }
          case 'tags': {
            const tag = item as SearchItems['tags'];
            return (
              <ResultRow
                key={id}
                entryId={id}
                active={active}
                leading={<Dot color={tag.color} />}
                title={<Highlighted text={tag.name} query={query} />}
                meta={t('search.openTasks', { n: tag.open_count })}
                onOpen={open}
              />
            );
          }
          case 'subjects': {
            const subject = item as SearchItems['subjects'];
            const extra = [subject.class_code, subject.lecturer].filter(Boolean).join(' · ');
            return (
              <ResultRow
                key={id}
                entryId={id}
                active={active}
                leading={<Dot color={subject.color} />}
                title={<Highlighted text={subject.name} query={query} />}
                meta={extra && <Highlighted text={extra} query={query} />}
                onOpen={open}
              />
            );
          }
          case 'sessions': {
            const session = item as SearchItems['sessions'];
            return (
              <ResultRow
                key={id}
                entryId={id}
                active={active}
                dim={session.is_cancelled}
                leading={<Dot color={session.subject.color} />}
                title={<Highlighted text={session.subject.name} query={query} />}
                meta={
                  <>
                    {sessionWhen(session.start_at)}
                    {session.room && (
                      <>
                        {' · '}
                        <Highlighted text={session.room} query={query} />
                      </>
                    )}
                    {session.is_cancelled && ` · ${t('search.cancelled')}`}
                  </>
                }
                onOpen={open}
              />
            );
          }
          case 'exams': {
            const exam = item as SearchItems['exams'];
            return (
              <ResultRow
                key={id}
                entryId={id}
                active={active}
                leading={<span aria-hidden>📝</span>}
                title={<Highlighted text={exam.course_name} query={query} />}
                meta={
                  <>
                    {sessionWhen(exam.start_at)}
                    {exam.room && (
                      <>
                        {' · '}
                        <Highlighted text={exam.room} query={query} />
                      </>
                    )}
                  </>
                }
                onOpen={open}
              />
            );
          }
        }
      })}
      {total > items.length && !expanded && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="self-start rounded-md px-2.5 py-1 text-accent hover:bg-surface-2"
        >
          {t('search.more', { n: total - items.length })}
        </button>
      )}
    </section>
  );
}

/**
 * Kết quả tìm kiếm nhóm theo loại (feature 003 FR-039 đến FR-043). ↑/↓ chọn, ↩ mở (phím gửi từ ô
 * tìm kiếm qua sự kiện); bấm vào task mở bảng chi tiết, vào nhãn/danh sách thì lọc theo nó.
 */
export function SearchResults({
  data,
  query,
  includeDone,
  now,
  openTask,
  openSession,
}: {
  data: SearchResponse;
  query: string;
  includeDone: boolean;
  now: Date;
  openTask: (id: number) => void;
  openSession: (id: number) => void;
}) {
  const [byGroup, setByGroup] = useState<Partial<Record<SearchGroupName, Entry[]>>>({});
  const [activeId, setActiveId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const entries = useMemo(() => SEARCH_GROUPS.flatMap((group) => byGroup[group] ?? []), [byGroup]);
  const latest = useRef({ entries, activeId });
  latest.current = { entries, activeId };

  const report = useRef((group: SearchGroupName, list: Entry[]) =>
    setByGroup((current) => (current[group] === list ? current : { ...current, [group]: list })),
  ).current;

  // Có kết quả mới (hoặc dòng đang chọn biến mất) thì chọn dòng đầu tiên.
  useEffect(() => {
    setActiveId((current) =>
      entries.some((entry) => entry.id === current) ? current : (entries[0]?.id ?? null),
    );
  }, [entries]);

  useEffect(() => {
    function onKey(event: Event) {
      const key = (event as CustomEvent<SearchKey>).detail;
      const { entries: list, activeId: current } = latest.current;
      if (list.length === 0) return;
      const index = list.findIndex((entry) => entry.id === current);
      if (key === 'open') {
        (list[index] ?? list[0]).open();
        return;
      }
      const next = Math.min(Math.max(index + (key === 'down' ? 1 : -1), 0), list.length - 1);
      setActiveId(list[next].id);
    }
    window.addEventListener(SEARCH_KEY_EVENT, onKey);
    return () => window.removeEventListener(SEARCH_KEY_EVENT, onKey);
  }, []);

  useEffect(() => {
    if (!activeId) return;
    const rows = containerRef.current?.querySelectorAll<HTMLElement>('[data-entry]') ?? [];
    [...rows].find((row) => row.dataset.entry === activeId)?.scrollIntoView?.({ block: 'nearest' });
  }, [activeId]);

  return (
    <div
      ref={containerRef}
      role="listbox"
      aria-label={t('search.results')}
      className="flex flex-col"
    >
      {SEARCH_GROUPS.map((group) => (
        <GroupSection
          key={group}
          group={group}
          total={data.groups[group].total}
          firstItems={data.groups[group].items}
          query={query}
          includeDone={includeDone}
          now={now}
          activeId={activeId}
          openTask={openTask}
          openSession={openSession}
          report={report}
        />
      ))}
    </div>
  );
}
