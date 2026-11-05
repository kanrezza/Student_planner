import { useCallback } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { ConnectionBanner } from './ConnectionBanner';
import { useDesktopBridge } from './desktopBridge';
import { IconRail } from './IconRail';
import { SECTIONS, TASKS_HOME, sectionTarget } from './navigation';
import { RestoreOverlay } from '../features/settings/RestoreOverlay';
import { ShortcutsDialog } from './ShortcutsDialog';
import { useShell } from './shell';
import { useHotkeys } from './useHotkeys';

/** Khung chung (feature 002 T016): thanh biểu tượng + nội dung theo route + phím tắt toàn cục. */
export function AppShell() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { setShortcutsOpen, focusQuickAdd, focusSearch } = useShell();

  const showShortcuts = useCallback(() => setShortcutsOpen(true), [setShortcutsOpen]);
  const go = useCallback((path: string) => navigate(path), [navigate]);
  useDesktopBridge({ navigate: go, showShortcuts });

  /** ⌘N: về Công việc (giữ view nếu đang ở đó) rồi đặt con trỏ vào ô "Thêm công việc". */
  function newTask() {
    const inTasks = pathname.startsWith('/cong-viec');
    const noQuickAdd = /\/cong-viec\/(da-hoan-thanh|thung-rac)/.test(pathname);
    if (inTasks && !noQuickAdd && focusQuickAdd()) return;
    navigate(inTasks && !noQuickAdd ? pathname : TASKS_HOME);
    // Ô thêm nhanh đăng ký sau khi màn hình mới render.
    window.setTimeout(() => focusQuickAdd(), 0);
  }

  /** ⌘F: về Công việc rồi đặt con trỏ vào ô tìm kiếm ở cột danh sách (feature 003 FR-036). */
  function startSearch() {
    if (pathname.startsWith('/cong-viec') && focusSearch()) return;
    if (!pathname.startsWith('/cong-viec')) navigate(TASKS_HOME);
    window.setTimeout(() => focusSearch(), 0); // ô tìm kiếm đăng ký sau khi màn hình mới render
  }

  useHotkeys([
    { key: 'f', meta: true, handler: startSearch },
    { key: 'n', meta: true, handler: newTask },
    { key: ',', meta: true, handler: () => navigate('/cai-dat') },
    { key: '/', meta: true, handler: showShortcuts },
    ...SECTIONS.map((section) => ({
      key: section.digit,
      meta: true,
      handler: () => navigate(sectionTarget(section)),
    })),
  ]);

  return (
    <div className="flex h-full overflow-hidden">
      <IconRail />
      <div className="flex min-w-0 flex-1 flex-col">
        <ConnectionBanner />
        <main className="min-h-0 flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
      <ShortcutsDialog />
      <RestoreOverlay />
    </div>
  );
}
