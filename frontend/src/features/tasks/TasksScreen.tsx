import { useEffect, useState, type ReactNode } from 'react';
import { Navigate, useLocation, useSearchParams } from 'react-router-dom';
import { useLists } from '../../api/lists';
import { useTags } from '../../api/tags';
import type { TaskView } from '../../api/tasks';
import { TASKS_HOME } from '../../app/navigation';
import { isTypingTarget, useHotkeys } from '../../app/useHotkeys';
import { t } from '../../i18n/vi';
import { cx } from '../../ui/cx';
import { IconButton } from '../../ui/IconButton';
import { IconSidebar } from '../../ui/icons';
import { SearchScreen } from '../search/SearchScreen';
import { SEARCH_PATH } from '../search/searchRoute';
import { ListColumn } from './ListColumn';
import { SmartListView } from './SmartListView';
import { TaskDetailPanel } from './TaskDetailPanel';
import { parseTaskPath, smartTitle, taskPath } from './viewRoutes';

/**
 * Màn hình Công việc 3 cột (feature 002 US2): cột danh sách, khu vực chính, bảng chi tiết (mở theo
 * `?task=:id`). Cửa sổ < 700px: cột danh sách thu gọn, mở lại bằng nút; < 900px: bảng chi tiết phủ
 * lên khu vực chính. Đường dẫn `/cong-viec/tim-kiem` (feature 003) dùng cùng khung nhưng khu vực
 * chính là kết quả tìm kiếm; cột danh sách được giữ nguyên để ô tìm kiếm không mất tiêu điểm khi gõ.
 */
export function TasksScreen() {
  const { pathname } = useLocation();
  const isSearch = pathname === SEARCH_PATH;
  const view = isSearch ? null : parseTaskPath(pathname);
  if (!isSearch && !view) return <Navigate to={TASKS_HOME} replace />;
  return <TasksFrame view={view} />;
}

function TasksFrame({ view }: { view: TaskView | null }) {
  const [listOpen, setListOpen] = useState(false);
  const headerStart = (
    <IconButton
      className="min-[700px]:hidden"
      label={listOpen ? t('listColumn.hide') : t('listColumn.show')}
      icon={<IconSidebar size={18} />}
      onClick={() => setListOpen(!listOpen)}
    />
  );

  return (
    <div className="relative flex h-full">
      <div
        className={cx(
          'h-full min-[700px]:block',
          listOpen ? 'absolute inset-y-0 left-0 z-30 block shadow-panel' : 'hidden',
        )}
      >
        <ListColumn current={view} />
      </div>
      {listOpen && (
        <div
          className="absolute inset-0 z-20 bg-overlay min-[700px]:hidden"
          onClick={() => setListOpen(false)}
        />
      )}
      {view ? (
        <TasksPane
          key={taskPath(view)}
          view={view}
          listOpen={listOpen}
          closeList={() => setListOpen(false)}
          headerStart={headerStart}
        />
      ) : (
        <SearchScreen headerStart={headerStart} />
      )}
    </div>
  );
}

function TasksPane({
  view,
  listOpen,
  closeList,
  headerStart,
}: {
  view: TaskView;
  listOpen: boolean;
  closeList: () => void;
  headerStart: ReactNode;
}) {
  const [params, setParams] = useSearchParams();
  const openId = Number(params.get('task')) || null;
  const [selectedId, setSelectedId] = useState<number | null>(openId);
  const title = useViewTitle(view);

  useEffect(() => {
    if (openId !== null) setSelectedId(openId);
  }, [openId]);

  function openTask(id: number | null) {
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (id === null) next.delete('task');
        else next.set('task', String(id));
        return next;
      },
      { replace: id === null },
    );
  }

  /** Esc: (hộp thoại tự đóng trước) → đóng bảng chi tiết → bỏ chọn ô nhập. */
  useHotkeys([
    {
      key: 'Escape',
      handler: (event) => {
        if (openId !== null) {
          // Rời ô đang sửa trước để trường đó kịp được lưu.
          if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
          openTask(null);
          return;
        }
        if (isTypingTarget(event.target) && event.target instanceof HTMLElement) {
          event.target.blur();
          return;
        }
        if (listOpen) {
          closeList();
          return;
        }
        return false;
      },
    },
  ]);

  return (
    <div className="relative flex min-w-0 flex-1">
      <SmartListView
        view={view}
        title={title}
        headerStart={headerStart}
        selectedId={selectedId}
        onSelect={setSelectedId}
        openId={openId}
        onOpen={(task) => {
          setSelectedId(task.id);
          openTask(task.id);
        }}
      />
      {openId !== null && <TaskDetailPanel taskId={openId} onClose={() => openTask(null)} />}
    </div>
  );
}

function useViewTitle(view: TaskView): string {
  const lists = useLists();
  const tags = useTags();
  if (view.kind === 'smart') return smartTitle(view.view);
  if (view.kind === 'list') {
    const list = lists.data?.find((l) => l.id === view.id);
    if (!list) return lists.isLoading ? '' : t('smart.notFound');
    return list.emoji ? `${list.emoji} ${list.name}` : list.name;
  }
  const tag = tags.data?.find((item) => item.id === view.id);
  return tag ? `# ${tag.name}` : tags.isLoading ? '' : t('smart.notFound');
}
