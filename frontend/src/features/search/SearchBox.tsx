import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { TASKS_HOME } from '../../app/navigation';
import { useShell } from '../../app/shell';
import { t } from '../../i18n/vi';
import { IconClose, IconSearch } from '../../ui/icons';
import {
  SEARCH_KEY_EVENT,
  SEARCH_PATH,
  rememberReturnPath,
  returnPath,
  searchUrl,
  type SearchKey,
} from './searchRoute';

/**
 * Ô tìm kiếm ở đầu cột danh sách (feature 003 FR-036): gõ là kết quả hiện ngay ở khu vực chính;
 * ⌘F đưa con trỏ vào đây; Esc xoá từ khoá và quay lại màn hình trước lúc tìm; ↑/↓/↩ chọn và mở kết quả.
 */
export function SearchBox() {
  const { pathname, search, state } = useLocation();
  const navigate = useNavigate();
  const { registerSearch } = useShell();
  const inputRef = useRef<HTMLInputElement>(null);
  const onSearchRoute = pathname === SEARCH_PATH;
  const params = new URLSearchParams(search);
  const urlQuery = onSearchRoute ? (params.get('q') ?? '') : '';
  const includeDone = params.get('done') === '1';
  const [value, setValue] = useState(urlQuery);

  useEffect(() => registerSearch(() => inputRef.current?.focus()), [registerSearch]);
  // Rời màn hình tìm kiếm bằng cách khác (bấm một danh sách) thì xoá chữ trong ô.
  useEffect(() => {
    if (!onSearchRoute) setValue('');
  }, [onSearchRoute]);
  // Mở lại đường dẫn có sẵn từ khoá (nút Quay lại của trình duyệt…) thì ô theo URL.
  useEffect(() => {
    if (onSearchRoute)
      setValue((current) => (current.trim() === urlQuery.trim() ? current : urlQuery));
  }, [onSearchRoute, urlQuery]);

  function change(next: string) {
    setValue(next);
    if (next.trim() === '') {
      if (onSearchRoute) navigate(returnPath(TASKS_HOME), { replace: true });
      return;
    }
    if (!onSearchRoute) rememberReturnPath(`${pathname}${search}`);
    navigate(searchUrl(next, includeDone), { replace: onSearchRoute, state });
  }

  function clearAndLeave() {
    setValue('');
    if (onSearchRoute) navigate(returnPath(TASKS_HOME), { replace: true });
    inputRef.current?.blur();
  }

  function sendKey(key: SearchKey) {
    window.dispatchEvent(new CustomEvent<SearchKey>(SEARCH_KEY_EVENT, { detail: key }));
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.nativeEvent.isComposing) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      clearAndLeave();
    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      sendKey(e.key === 'ArrowDown' ? 'down' : 'up');
    } else if (e.key === 'Enter' && value.trim() !== '') {
      e.preventDefault();
      sendKey('open');
    }
  }

  return (
    <div className="relative px-2 pb-2">
      <IconSearch
        size={15}
        className="pointer-events-none absolute left-4 top-1/2 -mt-1 -translate-y-1/2 text-muted"
      />
      <input
        ref={inputRef}
        type="search"
        value={value}
        placeholder={t('search.placeholder')}
        aria-label={t('search.label')}
        onChange={(e) => change(e.target.value)}
        onKeyDown={onKeyDown}
        className="h-8 w-full rounded-lg border-0 bg-surface-3 pl-8 pr-7 text-[13px] [&::-webkit-search-cancel-button]:hidden"
      />
      {value !== '' && (
        <button
          type="button"
          aria-label={t('search.clear')}
          onClick={clearAndLeave}
          className="absolute right-4 top-1/2 -mt-1 -translate-y-1/2 text-muted hover:text-text"
        >
          <IconClose size={13} />
        </button>
      )}
    </div>
  );
}
