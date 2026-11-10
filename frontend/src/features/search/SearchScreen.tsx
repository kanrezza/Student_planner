import { useQuery } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { apiFetch } from '../../api/client';
import { useSearch } from '../../api/search';
import type { ClassSession } from '../../api/types';
import { SessionDetail } from '../../components/SessionDetail';
import { useNow } from '../../app/useNow';
import { useHotkeys } from '../../app/useHotkeys';
import { t } from '../../i18n/vi';
import { Switch } from '../../ui/Switch';
import { TaskDetailPanel } from '../tasks/TaskDetailPanel';
import { SearchResults } from './SearchResults';
import { searchUrl } from './searchRoute';

/** Buổi học mở ngay trên trang kết quả (lấy theo id rồi hiện chi tiết như từ Lịch). */
function SessionOpener({ id, onClose }: { id: number; onClose: () => void }) {
  const session = useQuery({
    queryKey: ['session', id],
    queryFn: async () => (await apiFetch<ClassSession>(`/sessions/${id}`)).data,
  });
  return session.data ? <SessionDetail session={session.data} onClose={onClose} /> : null;
}

/**
 * Khu vực chính của đường dẫn `/cong-viec/tim-kiem?q=…` (feature 003 US5): tiêu đề, công tắc
 * "Gồm cả đã hoàn thành" (lưu trên URL), kết quả nhóm theo loại và bảng chi tiết task (`?task=`).
 */
export function SearchScreen({ headerStart }: { headerStart?: ReactNode }) {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const { state } = useLocation();
  const query = params.get('q') ?? '';
  const includeDone = params.get('done') === '1';
  const openId = Number(params.get('task')) || null;
  const [sessionId, setSessionId] = useState<number | null>(null);
  const { now } = useNow();
  const search = useSearch(query, includeDone);
  const data = search.data;
  const typed = query.trim() !== '';
  const noResults =
    data !== undefined && Object.values(data.groups).every((group) => group.total === 0);

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

  /** Esc đóng bảng chi tiết task (hộp thoại và ô tìm kiếm tự xử lý Esc của chúng trước). */
  useHotkeys([
    {
      key: 'Escape',
      enabled: openId !== null,
      handler: () => {
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        openTask(null);
      },
    },
  ]);

  return (
    <div className="relative flex min-w-0 flex-1">
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex shrink-0 items-center gap-3 px-6 pb-2 pt-[calc(20px+var(--titlebar-inset))]">
          {headerStart}
          <h1 className="min-w-0 flex-1 truncate text-[22px] font-bold leading-8 tracking-tight">
            {typed ? t('search.title', { q: query.trim() }) : t('search.label')}
          </h1>
          <label className="flex items-center gap-2 text-[12px] text-muted">
            <Switch
              label={t('search.includeDone')}
              checked={includeDone}
              onChange={(on) => navigate(searchUrl(query, on), { replace: true, state })}
            />
            {t('search.includeDone')}
          </label>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-10">
          {!typed && <p className="px-2 text-muted">{t('search.hint')}</p>}
          {typed && !data && <p className="px-2 text-muted">{t('search.loading')}</p>}
          {typed && noResults && (
            <p className="px-2 text-muted">{t('search.empty', { q: query.trim() })}</p>
          )}
          {typed && data && !noResults && (
            <SearchResults
              data={data}
              query={query}
              includeDone={includeDone}
              now={now}
              openTask={openTask}
              openSession={setSessionId}
            />
          )}
        </div>
      </div>
      {openId !== null && <TaskDetailPanel taskId={openId} onClose={() => openTask(null)} />}
      {sessionId !== null && <SessionOpener id={sessionId} onClose={() => setSessionId(null)} />}
    </div>
  );
}
