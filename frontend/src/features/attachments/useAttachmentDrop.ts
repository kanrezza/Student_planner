import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState, type DragEvent } from 'react';
import { attachmentsKey, type Owner } from '../../api/attachments';
import { useSettings } from '../../api/settings';
import { invalidateAll } from '../../api/keys';
import { clipboardFilePaths, isDesktopApp, uploadPaths } from '../../app/desktopBridge';
import { isTypingTarget } from '../../app/useHotkeys';
import { t } from '../../i18n/vi';
import { checkFileSize, filesFromDrop, uploadFile, type UploadHandle } from './upload';

export type UploadItem = {
  key: number;
  name: string;
  progress: number;
  error: string | null;
  handle: UploadHandle | null;
};

/**
 * Gắn file vào một nơi bằng kéo thả, chọn file và ⌘V (feature 005, FR-016). Mỗi file một yêu cầu riêng
 * để có tiến trình và lỗi riêng. Trả danh sách đang tải/lỗi và các hàm thao tác.
 */
export function useAttachmentUpload(owner: Owner) {
  const qc = useQueryClient();
  const maxMb = useSettings().data?.attachment_max_mb ?? 50;
  const [items, setItems] = useState<UploadItem[]>([]);
  const nextKey = useRef(1);

  const patch = useCallback((key: number, change: Partial<UploadItem>) => {
    setItems((current) =>
      current.map((item) => (item.key === key ? { ...item, ...change } : item)),
    );
  }, []);
  const remove = useCallback((key: number) => {
    setItems((current) => current.filter((item) => item.key !== key));
  }, []);

  const refresh = useCallback(() => {
    void qc.invalidateQueries({ queryKey: attachmentsKey(owner) });
    invalidateAll(qc);
  }, [qc, owner]);

  const addFiles = useCallback(
    (files: File[], folders: string[] = []) => {
      const rejected: UploadItem[] = folders.map((name) => ({
        key: nextKey.current++,
        name,
        progress: 0,
        error: t('attachments.folder'),
        handle: null,
      }));
      const started: UploadItem[] = [];
      for (const file of files) {
        const key = nextKey.current++;
        const tooBig = checkFileSize(file, maxMb);
        if (tooBig) {
          rejected.push({ key, name: file.name, progress: 0, error: tooBig, handle: null });
          continue;
        }
        const handle = uploadFile(owner, file, (fraction) => patch(key, { progress: fraction }));
        started.push({ key, name: file.name, progress: 0, error: null, handle });
        handle.promise.then(
          () => {
            remove(key);
            refresh();
          },
          (error: Error) => {
            if (error.message === t('attachments.cancelled')) remove(key);
            else patch(key, { error: error.message, handle: null });
          },
        );
      }
      if (rejected.length || started.length)
        setItems((current) => [...current, ...rejected, ...started]);
    },
    [maxMb, owner, patch, refresh, remove],
  );

  /** Dán: file/ảnh trong clipboard; trong app macOS còn đọc file chép từ Finder. */
  const pasteFromClipboard = useCallback(
    async (data: DataTransfer | null): Promise<boolean> => {
      const files = Array.from(data?.files ?? []);
      if (files.length) {
        addFiles(files);
        return true;
      }
      if (!isDesktopApp()) return false;
      const paths = (await clipboardFilePaths()) ?? [];
      if (!paths.length) return false;
      const result = await uploadPaths(owner.type, owner.id, paths);
      for (const error of result?.errors ?? [])
        setItems((current) => [
          ...current,
          {
            key: nextKey.current++,
            name: error.name,
            progress: 0,
            error: error.message,
            handle: null,
          },
        ]);
      refresh();
      return true;
    },
    [addFiles, owner, refresh],
  );

  return { items, addFiles, remove, pasteFromClipboard, maxMb };
}

/** Vùng thả: gắn các handler kéo thả vào phần tử; `dragging` bật lớp phủ. */
export function useDropZone(onFiles: (files: File[], folders: string[]) => void) {
  const [dragging, setDragging] = useState(false);
  const depth = useRef(0);
  return {
    dragging,
    props: {
      onDragEnter: (event: DragEvent) => {
        if (!Array.from(event.dataTransfer.types).includes('Files')) return;
        event.preventDefault();
        depth.current += 1;
        setDragging(true);
      },
      onDragOver: (event: DragEvent) => {
        if (Array.from(event.dataTransfer.types).includes('Files')) event.preventDefault();
      },
      onDragLeave: () => {
        depth.current = Math.max(0, depth.current - 1);
        if (depth.current === 0) setDragging(false);
      },
      onDrop: (event: DragEvent) => {
        event.preventDefault();
        depth.current = 0;
        setDragging(false);
        const { files, folders } = filesFromDrop(event.dataTransfer);
        onFiles(files, folders);
      },
    },
  };
}

/** ⌘V khi mục File đính kèm đang hiện và không gõ trong ô chữ (hoặc clipboard không có chữ). */
export function useAttachmentPaste(onPaste: (data: DataTransfer | null) => Promise<boolean>) {
  const latest = useRef(onPaste);
  latest.current = onPaste;
  useEffect(() => {
    function handler(event: ClipboardEvent) {
      if (event.defaultPrevented) return;
      const typing = isTypingTarget(event.target);
      const hasText = Boolean(event.clipboardData?.getData('text/plain'));
      if (typing && hasText) return;
      const hasFiles = (event.clipboardData?.files?.length ?? 0) > 0;
      if (!hasFiles && (typing || !isDesktopApp())) return;
      if (hasFiles) event.preventDefault();
      void latest.current(event.clipboardData).then((handled) => {
        if (handled && !hasFiles) event.preventDefault();
      });
    }
    document.addEventListener('paste', handler);
    return () => document.removeEventListener('paste', handler);
  }, []);
}
