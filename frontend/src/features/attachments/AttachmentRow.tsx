import { useEffect, useRef, useState } from 'react';
import { useDeleteAttachment, useRenameAttachment, type Attachment } from '../../api/attachments';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { t } from '../../i18n/vi';
import { formatDate } from '../../lib/dates';
import { formatSize } from '../../lib/format';
import { cx } from '../../ui/cx';
import { IconAlert, IconMore } from '../../ui/icons';
import { IconButton } from '../../ui/IconButton';
import { Menu, MenuItem } from '../../ui/Menu';
import { useToast } from '../../ui/Toast';
import { KIND_COLOR, KIND_LABEL, fileKind } from './attachmentFormat';
import { downloadAttachment, openExternally } from './AttachmentPreview';

/** Một dòng file đính kèm: loại, tên, dung lượng · ngày, menu Xem/Mở, Tải về, Đổi tên, Xoá. */
export function AttachmentRow({
  attachment,
  ownerTitle,
  highlighted,
  onPreview,
}: {
  attachment: Attachment;
  ownerTitle: string;
  highlighted: boolean;
  onPreview: () => void;
}) {
  const toast = useToast();
  const rename = useRenameAttachment();
  const remove = useDeleteAttachment();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(attachment.display_name);
  const [confirming, setConfirming] = useState(false);
  const ref = useRef<HTMLLIElement>(null);
  const kind = fileKind(attachment.mime_type, attachment.display_name);

  useEffect(() => {
    if (highlighted) ref.current?.scrollIntoView?.({ block: 'nearest' });
  }, [highlighted]);

  function commitName() {
    const value = name.trim();
    setEditing(false);
    if (value && value !== attachment.display_name)
      rename.mutate(
        { id: attachment.id, display_name: value },
        { onError: (err) => toast.show(err.message, { tone: 'danger' }) },
      );
    else setName(attachment.display_name);
  }

  const primary = attachment.preview ? onPreview : () => void openExternally(attachment, toast);

  return (
    <li
      ref={ref}
      data-attachment-id={attachment.id}
      className={cx(
        'flex items-center gap-2.5 rounded-lg px-2 py-1.5',
        highlighted ? 'bg-accent-soft ring-1 ring-accent' : 'hover:bg-surface-2',
      )}
    >
      <span
        className={cx(
          'flex h-8 w-10 shrink-0 items-center justify-center rounded-md text-[11px] font-semibold',
          KIND_COLOR[kind],
        )}
      >
        {KIND_LABEL[kind]}
      </span>
      <div className="min-w-0 flex-1">
        {editing ? (
          <input
            autoFocus
            aria-label={t('attachments.renamePrompt')}
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={commitName}
            onKeyDown={(e) => {
              if (e.key === 'Enter') commitName();
              if (e.key === 'Escape') {
                setName(attachment.display_name);
                setEditing(false);
              }
            }}
            className="h-7 w-full px-1.5"
          />
        ) : (
          <button
            type="button"
            onClick={primary}
            className="block max-w-full truncate text-left font-medium hover:underline"
            title={attachment.display_name}
          >
            {attachment.display_name}
          </button>
        )}
        <p className="flex items-center gap-1 text-[12px] text-muted tabular-nums">
          {attachment.is_executable && (
            <span title={t('attachments.executableWarning')} className="text-warning">
              <IconAlert size={13} aria-label={t('attachments.executableWarning')} />
            </span>
          )}
          {formatSize(attachment.size)} · {formatDate(attachment.created_at.slice(0, 10))}
        </p>
      </div>
      <Menu
        trigger={
          <IconButton
            label={t('attachments.more', { name: attachment.display_name })}
            icon={<IconMore size={16} />}
            size="sm"
          />
        }
      >
        {attachment.preview && <MenuItem onSelect={onPreview}>{t('attachments.view')}</MenuItem>}
        {!attachment.preview && !attachment.is_executable && (
          <MenuItem onSelect={() => void openExternally(attachment, toast)}>
            {t('attachments.open')}
          </MenuItem>
        )}
        <MenuItem onSelect={() => void downloadAttachment(attachment, toast)}>
          {t('attachments.download')}
        </MenuItem>
        <MenuItem onSelect={() => setEditing(true)}>{t('attachments.rename')}</MenuItem>
        <MenuItem danger onSelect={() => setConfirming(true)}>
          {t('attachments.delete')}
        </MenuItem>
      </Menu>
      <ConfirmDialog
        open={confirming}
        title={t('attachments.deleteTitle')}
        message={t('attachments.deleteConfirm', {
          name: attachment.display_name,
          owner: ownerTitle,
        })}
        confirmLabel={t('attachments.delete')}
        onCancel={() => setConfirming(false)}
        onConfirm={() => {
          setConfirming(false);
          remove.mutate(attachment.id, {
            onError: (err) => toast.show(err.message, { tone: 'danger' }),
          });
        }}
      />
    </li>
  );
}
