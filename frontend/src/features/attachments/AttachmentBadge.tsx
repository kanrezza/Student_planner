import { t } from '../../i18n/vi';
import { IconPaperclip } from '../../ui/icons';

/** Kẹp giấy + số file đính kèm (ẩn khi chưa có file). */
export function AttachmentBadge({ count }: { count?: number }) {
  if (!count) return null;
  return (
    <span
      className="inline-flex items-center gap-0.5 text-muted"
      aria-label={t('attachments.count', { count })}
    >
      <IconPaperclip size={13} />
      {count}
    </span>
  );
}
