/** Gửi file đính kèm bằng XMLHttpRequest để có tiến trình (feature 005, research R5). */
import { ApiError } from '../../api/client';
import type { Attachment, Owner } from '../../api/attachments';
import { t } from '../../i18n/vi';

export const MIB = 1024 * 1024;

/** Kiểm tra trước khi gửi: vượt giới hạn mỗi file → thông báo nêu giới hạn và chỗ đổi. */
export function checkFileSize(file: { size: number }, maxMb: number): string | null {
  return file.size > maxMb * MIB ? t('attachments.tooBig', { limit: maxMb }) : null;
}

export type UploadHandle = { promise: Promise<Attachment>; cancel: () => void };

export function uploadFile(
  owner: Owner,
  file: File,
  onProgress: (fraction: number) => void,
): UploadHandle {
  const request = new XMLHttpRequest();
  const promise = new Promise<Attachment>((resolve, reject) => {
    request.open('POST', '/api/attachments');
    request.upload.onprogress = (event) => {
      if (event.lengthComputable && event.total > 0) onProgress(event.loaded / event.total);
    };
    request.onerror = () => reject(new ApiError(0, 'network_error', t('errors.network')));
    request.onabort = () => reject(new ApiError(0, 'aborted', t('attachments.cancelled')));
    request.onload = () => {
      let body: {
        attachments?: Attachment[];
        errors?: { code: string; message: string }[];
        error?: { code?: string; message?: string };
      } = {};
      try {
        body = JSON.parse(request.responseText);
      } catch {
        // phản hồi không phải JSON (ví dụ nginx 413 dạng HTML)
      }
      const created = body.attachments?.[0];
      if (request.status >= 200 && request.status < 300 && created) {
        resolve(created);
        return;
      }
      const error = body.errors?.[0] ?? body.error;
      const message =
        error?.message ??
        (request.status === 413 ? t('attachments.tooBigServer') : t('attachments.failed'));
      reject(new ApiError(request.status, error?.code ?? 'upload_failed', message));
    };
    const form = new FormData();
    form.append('owner_type', owner.type);
    form.append('owner_id', String(owner.id));
    form.append('file', file, file.name);
    request.send(form);
  });
  return { promise, cancel: () => request.abort() };
}

/** File lấy từ sự kiện thả: bỏ thư mục (báo riêng) — `webkitGetAsEntry` có ở Chrome và WebKit. */
export function filesFromDrop(data: DataTransfer): { files: File[]; folders: string[] } {
  const files: File[] = [];
  const folders: string[] = [];
  const items = Array.from(data.items ?? []);
  if (items.length) {
    for (const item of items) {
      if (item.kind !== 'file') continue;
      const entry = (
        item as DataTransferItem & {
          webkitGetAsEntry?: () => { isDirectory: boolean; name: string } | null;
        }
      ).webkitGetAsEntry?.();
      const file = item.getAsFile();
      if (entry?.isDirectory) folders.push(entry.name);
      else if (file) files.push(file);
    }
    return { files, folders };
  }
  return { files: Array.from(data.files ?? []), folders };
}
