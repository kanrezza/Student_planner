/** Hiển thị loại file đính kèm (feature 005): nhãn ngắn theo MIME/phần mở rộng. */

export type FileKind = 'pdf' | 'image' | 'word' | 'powerpoint' | 'excel' | 'archive' | 'other';

export function fileKind(mimeType: string, name: string): FileKind {
  const extension = name.includes('.') ? name.split('.').pop()!.toLowerCase() : '';
  if (mimeType === 'application/pdf' || extension === 'pdf') return 'pdf';
  if (mimeType.startsWith('image/')) return 'image';
  if (['doc', 'docx', 'pages', 'rtf', 'odt'].includes(extension)) return 'word';
  if (['ppt', 'pptx', 'key', 'odp'].includes(extension)) return 'powerpoint';
  if (['xls', 'xlsx', 'csv', 'numbers', 'ods'].includes(extension)) return 'excel';
  if (['zip', 'rar', '7z', 'gz', 'tar'].includes(extension)) return 'archive';
  return 'other';
}

export const KIND_LABEL: Record<FileKind, string> = {
  pdf: 'PDF',
  image: 'Ảnh',
  word: 'Word',
  powerpoint: 'Slide',
  excel: 'Bảng',
  archive: 'Nén',
  other: 'File',
};

export const KIND_COLOR: Record<FileKind, string> = {
  pdf: 'bg-danger-soft text-danger',
  image: 'bg-accent-soft text-accent-strong',
  word: 'bg-accent-soft text-accent-strong',
  powerpoint: 'bg-warning-soft text-warning',
  excel: 'bg-success-soft text-success',
  archive: 'bg-surface-3 text-muted',
  other: 'bg-surface-3 text-muted',
};
