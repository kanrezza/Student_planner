import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { isTypingTarget } from '../../app/useHotkeys';
import { t } from '../../i18n/vi';
import { useToast } from '../../ui/Toast';
import { setPendingImage } from './pendingImage';

export const IMPORT_PATH = '/mon-hoc/nhap-anh';

/** Ảnh đầu tiên trong clipboard (ảnh chụp màn hình ⌘⇧⌃4, ảnh sao chép…), hoặc null. */
export function imageFromClipboard(data: DataTransfer | null | undefined): File | null {
  if (!data) return null;
  for (const item of Array.from(data.items ?? [])) {
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      const file = item.getAsFile();
      if (file) return file;
    }
  }
  return Array.from(data.files ?? []).find((f) => f.type.startsWith('image/')) ?? null;
}

/**
 * Lắng nghe ⌘V (sự kiện `paste`, chạy cả trong trình duyệt lẫn WebView của Tauri).
 * - Clipboard có ảnh → `onImage`, kể cả khi đang đứng trong ô nhập (ô chữ không nhận được ảnh),
 *   trừ khi clipboard cũng có chữ và đang gõ trong ô nhập — khi đó để dán chữ như thường.
 * - Không có ảnh và không đang gõ trong ô nhập → `onNoImage` (báo nhẹ).
 */
export function usePasteImage(onImage: (file: File) => void, onNoImage: () => void): void {
  const latest = useRef({ onImage, onNoImage });
  latest.current = { onImage, onNoImage };

  useEffect(() => {
    function onPaste(event: ClipboardEvent) {
      if (event.defaultPrevented) return;
      const typing = isTypingTarget(event.target);
      const image = imageFromClipboard(event.clipboardData);
      if (image) {
        if (typing && event.clipboardData?.getData('text/plain')) return;
        event.preventDefault();
        latest.current.onImage(image);
      } else if (!typing) {
        latest.current.onNoImage();
      }
    }
    document.addEventListener('paste', onPaste);
    return () => document.removeEventListener('paste', onPaste);
  }, []);
}

/** Dùng ở trang Môn học và Lịch thi: dán ảnh → mở màn hình Nhập từ ảnh với ảnh đó. */
export function usePasteToImport(): void {
  const navigate = useNavigate();
  const toast = useToast();
  usePasteImage(
    (file) => {
      setPendingImage(file);
      navigate(IMPORT_PATH);
    },
    () => toast.show(t('import.noClipboardImage')),
  );
}
