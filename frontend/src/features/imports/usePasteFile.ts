import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { isTypingTarget } from '../../app/useHotkeys';
import { t } from '../../i18n/vi';
import { useToast } from '../../ui/Toast';
import { setPendingFile } from './pendingFile';

export const IMPORT_PATH = '/mon-hoc/nhap-anh';

const isWanted = (type: string) => type.startsWith('image/') || type === 'application/pdf';

/** File ảnh hoặc PDF đầu tiên trong clipboard (ảnh chụp màn hình ⌘⇧⌃4, ảnh/PDF sao chép…). */
export function fileFromClipboard(data: DataTransfer | null | undefined): File | null {
  if (!data) return null;
  for (const item of Array.from(data.items ?? [])) {
    if (item.kind === 'file' && isWanted(item.type)) {
      const file = item.getAsFile();
      if (file) return file;
    }
  }
  return Array.from(data.files ?? []).find((f) => isWanted(f.type)) ?? null;
}

/**
 * Lắng nghe ⌘V (sự kiện `paste`, chạy cả trong trình duyệt lẫn WebView của Tauri).
 * - Clipboard có ảnh hoặc PDF → `onFile`, kể cả khi đang đứng trong ô nhập (ô chữ không nhận được ảnh),
 *   trừ khi clipboard cũng có chữ và đang gõ trong ô nhập — khi đó để dán chữ như thường.
 * - Không có ảnh/PDF và không đang gõ trong ô nhập → `onNoImage` (báo nhẹ).
 */
export function usePasteFile(onFile: (file: File) => void, onNoImage: () => void): void {
  const latest = useRef({ onFile, onNoImage });
  latest.current = { onFile, onNoImage };

  useEffect(() => {
    function onPaste(event: ClipboardEvent) {
      if (event.defaultPrevented) return;
      const typing = isTypingTarget(event.target);
      const pasted = fileFromClipboard(event.clipboardData);
      if (pasted) {
        if (typing && event.clipboardData?.getData('text/plain')) return;
        event.preventDefault();
        latest.current.onFile(pasted);
      } else if (!typing) {
        latest.current.onNoImage();
      }
    }
    document.addEventListener('paste', onPaste);
    return () => document.removeEventListener('paste', onPaste);
  }, []);
}

/** Dùng ở trang Môn học và Lịch thi: dán ảnh hoặc PDF → mở màn hình Nhập lịch với file đó. */
export function usePasteToImport(): void {
  const navigate = useNavigate();
  const toast = useToast();
  usePasteFile(
    (file) => {
      setPendingFile(file);
      navigate(IMPORT_PATH);
    },
    () => toast.show(t('import.noClipboardFile')),
  );
}
