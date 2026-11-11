import { useRef, useState } from 'react';
import { useAttachments, type Owner } from '../../api/attachments';
import { t } from '../../i18n/vi';
import { Button } from '../../ui/Button';
import { cx } from '../../ui/cx';
import { AttachmentPreview } from './AttachmentPreview';
import { AttachmentRow } from './AttachmentRow';
import { useAttachmentPaste, useAttachmentUpload, useDropZone } from './useAttachmentDrop';

/**
 * Mục "File đính kèm" dùng chung cho task, môn học, buổi học, buổi thi (feature 005, FR-016, FR-030):
 * vùng thả, "Thêm file", ⌘V, danh sách kèm tiến trình/lỗi, xem trước, tô sáng khi mở từ ⌘F.
 */
export function AttachmentsSection({ owner, ownerTitle }: { owner: Owner; ownerTitle: string }) {
  const query = useAttachments(owner);
  const upload = useAttachmentUpload(owner);
  const [previewIndex, setPreviewIndex] = useState<number | null>(null);
  // `?attachment=<id>` do kết quả ⌘F đưa tới (BrowserRouter nên đọc thẳng từ địa chỉ).
  const highlightId = Number(new URLSearchParams(window.location.search).get('attachment')) || null;
  const input = useRef<HTMLInputElement>(null);
  const zone = useDropZone(upload.addFiles);
  useAttachmentPaste(upload.pasteFromClipboard);
  const items = Array.isArray(query.data) ? query.data : [];

  return (
    <section
      aria-label={t('attachments.title')}
      {...zone.props}
      className={cx(
        'relative mt-5 rounded-lg border border-dashed p-3',
        zone.dragging ? 'border-accent bg-accent-soft' : 'border-border',
      )}
    >
      <div className="mb-2 flex items-center gap-2">
        <h3 className="text-[13px] font-semibold">
          {t('attachments.title')}
          {items.length > 0 && <span className="ml-1 text-muted">· {items.length}</span>}
        </h3>
        <Button size="sm" className="ml-auto" onClick={() => input.current?.click()}>
          {t('attachments.add')}
        </Button>
        <input
          ref={input}
          type="file"
          multiple
          hidden
          data-testid="attachment-input"
          onChange={(e) => {
            upload.addFiles(Array.from(e.target.files ?? []));
            e.target.value = '';
          }}
        />
      </div>
      {zone.dragging && (
        <p className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-accent-soft/90 font-medium text-accent-strong">
          {t('attachments.dropOverlay', { owner: ownerTitle })}
        </p>
      )}
      {upload.items.length > 0 && (
        <ul className="mb-1 flex flex-col gap-1">
          {upload.items.map((item) => (
            <li key={item.key} className="rounded-lg bg-surface-2 px-2 py-1.5 text-[13px]">
              <div className="flex items-center gap-2">
                <span className="min-w-0 flex-1 truncate">{item.name}</span>
                {item.error ? (
                  <Button size="sm" variant="ghost" onClick={() => upload.remove(item.key)}>
                    {t('attachments.dismiss')}
                  </Button>
                ) : (
                  <Button size="sm" variant="ghost" onClick={() => item.handle?.cancel()}>
                    {t('attachments.cancel')}
                  </Button>
                )}
              </div>
              {item.error ? (
                <p role="alert" className="text-[12px] text-danger">
                  {item.error}
                </p>
              ) : (
                <div
                  role="progressbar"
                  aria-valuenow={Math.round(item.progress * 100)}
                  aria-label={t('attachments.uploading', {
                    percent: Math.round(item.progress * 100),
                  })}
                  className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-3"
                >
                  <div
                    className="h-full bg-accent"
                    style={{ width: `${Math.round(item.progress * 100)}%` }}
                  />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      {items.length === 0 && upload.items.length === 0 ? (
        <p className="py-2 text-[12px] text-muted">{t('attachments.empty')}</p>
      ) : (
        <ul className="flex flex-col">
          {items.map((attachment, index) => (
            <AttachmentRow
              key={attachment.id}
              attachment={attachment}
              ownerTitle={ownerTitle}
              highlighted={attachment.id === highlightId}
              onPreview={() => setPreviewIndex(index)}
            />
          ))}
        </ul>
      )}
      <AttachmentPreview
        items={items}
        index={previewIndex}
        onIndex={setPreviewIndex}
        onClose={() => setPreviewIndex(null)}
      />
    </section>
  );
}
