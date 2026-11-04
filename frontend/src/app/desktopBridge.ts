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
