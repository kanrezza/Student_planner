/**
 * API toàn cục cho app macOS (desktop-shell §4): menu "Cài đặt…" và "Phím tắt" gọi qua `eval`.
 * Trong trình duyệt đối tượng vẫn được đăng ký nhưng không ai gọi.
 */
import { useEffect } from 'react';

export type DesktopBridge = {
  navigate(path: string): void;
  showShortcuts(): void;
};

declare global {
  interface Window {
    lichhoc?: DesktopBridge;
  }
}

export function useDesktopBridge(bridge: DesktopBridge): void {
  const { navigate, showShortcuts } = bridge;
  useEffect(() => {
    window.lichhoc = { navigate, showShortcuts };
    return () => {
      delete window.lichhoc;
    };
  }, [navigate, showShortcuts]);
}

/** Đang chạy trong app macOS (Tauri đặt user agent có `LichHocDesktop`). */
export function isDesktopApp(): boolean {
  return typeof navigator !== 'undefined' && navigator.userAgent.includes('LichHocDesktop');
}

type TauriInternals = { invoke(command: string, args?: Record<string, unknown>): Promise<unknown> };

function tauriInvoke<T>(command: string, args?: Record<string, unknown>): Promise<T | null> {
  const internals = (window as unknown as { __TAURI_INTERNALS__?: TauriInternals })
    .__TAURI_INTERNALS__;
  if (!isDesktopApp() || !internals) return Promise.resolve(null);
  return internals.invoke(command, args) as Promise<T | null>;
}

/** Hộp chọn thư mục của macOS; null nếu huỷ hoặc không chạy trong app macOS. */
export const pickBackupFolder = () => tauriInvoke<string>('pick_backup_folder');

/** Hộp chọn file `.lhbackup` của macOS; null nếu huỷ hoặc không chạy trong app macOS. */
export const pickBackupFile = () => tauriInvoke<string>('pick_backup_file');

/** Hiện thư mục hoặc file sao lưu trong Finder. */
export const revealInFinder = (path: string) => tauriInvoke<void>('reveal_in_finder', { path });
