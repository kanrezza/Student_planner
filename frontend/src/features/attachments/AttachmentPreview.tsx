import { useEffect, useState } from 'react';
import type { Attachment } from '../../api/attachments';
import { isDesktopApp, openAttachmentNative, saveAttachmentNative } from '../../app/desktopBridge';
import { t } from '../../i18n/vi';
import { Button } from '../../ui/Button';
import { Dialog } from '../../ui/Dialog';
import { useToast } from '../../ui/Toast';

const ZOOM_STEP = 0.25;

/** Tải về: trong app macOS lưu vào thư mục Tải về, trên trình duyệt dùng liên kết tải xuống. */
export async function downloadAttachment(
  attachment: Attachment,
  toast: ReturnType<typeof useToast>,
): Promise<void> {
  if (isDesktopApp()) {
    try {
      const path = await saveAttachmentNative(attachment.id);
      if (path) toast.show(t('attachments.saved', { path }));
    } catch (error) {
      toast.show(String(error), { tone: 'danger' });
    }
    return;
  }
  const link = document.createElement('a');
  link.href = attachment.download_url;
  link.download = attachment.display_name;
  link.click();
}

/** "Mở": xem trước ảnh/PDF trong app (do người gọi xử lý); loại khác mở bằng ứng dụng macOS. */
export async function openExternally(
  attachment: Attachment,
  toast: ReturnType<typeof useToast>,
): Promise<void> {
  if (attachment.is_executable) {
    toast.show(t('attachments.executableWarning'), { tone: 'warning' });
    return;
  }
  if (!isDesktopApp()) {
    await downloadAttachment(attachment, toast);
    return;
  }
  try {
    await openAttachmentNative(attachment.id);
  } catch (error) {
    toast.show(String(error), { tone: 'danger' });
  }
}

/** Khung xem trước ảnh/PDF (feature 005, FR-021): +/−/1:1, "‹ ›" sang file kế, Esc đóng. */
export function AttachmentPreview({
  items,
  index,
  onIndex,
  onClose,
}: {
  items: Attachment[];
  index: number | null;
  onIndex: (index: number) => void;
  onClose: () => void;
}) {
  const toast = useToast();
  const [zoom, setZoom] = useState(1);
  const [broken, setBroken] = useState(false);
  const current = index === null ? null : (items[index] ?? null);

  useEffect(() => {
    setZoom(1);
    setBroken(false);
  }, [current?.id]);

  const previewable = items.map((item, i) => ({ item, i })).filter(({ item }) => item.preview);
  const position = previewable.findIndex(({ i }) => i === index);
  const step = (direction: 1 | -1) => {
    const target = previewable[position + direction];
    if (target) onIndex(target.i);
  };

  useEffect(() => {
    if (!current) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === 'ArrowLeft') step(-1);
      else if (event.key === 'ArrowRight') step(1);
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  return (
    <Dialog
      open={current !== null}
      onOpenChange={(open) => !open && onClose()}
      title={current?.display_name ?? ''}
      size="lg"
      footer={
        current && (
          <>
            <Button onClick={() => void downloadAttachment(current, toast)}>
              {t('attachments.download')}
            </Button>
            {isDesktopApp() && !current.is_executable && (
              <Button onClick={() => void openExternally(current, toast)}>
                {t('attachments.openExternal')}
              </Button>
            )}
          </>
        )
      }
    >
      {current && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              disabled={position <= 0}
              onClick={() => step(-1)}
              aria-label={t('attachments.prev')}
            >
              ‹
            </Button>
            <Button
              size="sm"
              disabled={position === -1 || position >= previewable.length - 1}
              onClick={() => step(1)}
              aria-label={t('attachments.next')}
            >
              ›
            </Button>
            {current.preview === 'image' && (
              <span className="ml-auto flex items-center gap-1">
                <Button
                  size="sm"
                  aria-label={t('attachments.zoomOut')}
                  onClick={() => setZoom((z) => Math.max(0.25, z - ZOOM_STEP))}
                >
                  −
                </Button>
                <Button
                  size="sm"
                  aria-label={t('attachments.zoomReset')}
                  onClick={() => setZoom(1)}
                >
                  1:1
                </Button>
                <Button
                  size="sm"
                  aria-label={t('attachments.zoomIn')}
                  onClick={() => setZoom((z) => Math.min(6, z + ZOOM_STEP))}
                >
                  +
                </Button>
              </span>
            )}
          </div>
          {broken ? (
            <p className="py-10 text-center text-muted">{t('attachments.cannotPreview')}</p>
          ) : current.preview === 'image' ? (
            <div className="max-h-[60vh] overflow-auto rounded-lg bg-surface-2 p-2">
              <img
                src={current.content_url}
                alt={current.display_name}
                onError={() => setBroken(true)}
                style={{ width: `${zoom * 100}%`, maxWidth: zoom <= 1 ? '100%' : 'none' }}
                className="mx-auto h-auto"
              />
            </div>
          ) : current.preview === 'pdf' ? (
            <iframe
              title={current.display_name}
              src={current.content_url}
              className="h-[60vh] w-full rounded-lg border border-border"
            />
          ) : (
            <p className="py-10 text-center text-muted">{t('attachments.cannotPreview')}</p>
          )}
        </div>
      )}
    </Dialog>
  );
}
