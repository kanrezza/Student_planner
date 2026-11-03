import { useEffect, useRef } from 'react';
import { t } from '../i18n/vi';

type Props = {
  open: boolean;
  title?: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Hộp thoại xác nhận trước mọi thao tác xoá (FR-027). Dùng thẻ <dialog> có sẵn của trình duyệt. */
export function ConfirmDialog({
  open,
  title = t('confirm.deleteTitle'),
  message,
  confirmLabel = t('confirm.delete'),
  onConfirm,
  onCancel,
}: Props) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal?.();
    if (!open && dialog.open) dialog.close?.();
  }, [open]);

  return (
    <dialog ref={ref} className="dialog" onCancel={onCancel} aria-labelledby="confirm-title">
      <h2 id="confirm-title">{title}</h2>
      <p>{message}</p>
      <div className="dialog__actions">
        <button type="button" onClick={onCancel}>
          {t('confirm.cancel')}
        </button>
        <button type="button" className="button--danger" onClick={onConfirm}>
          {confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
