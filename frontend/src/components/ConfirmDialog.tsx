import { t } from '../i18n/vi';
import { Button } from '../ui/Button';
import { Dialog } from '../ui/Dialog';

type Props = {
  open: boolean;
  title?: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Hộp thoại xác nhận (FR-027 của feature 001; với task chỉ còn dùng cho "Xoá vĩnh viễn"). */
export function ConfirmDialog({
  open,
  title = t('confirm.deleteTitle'),
  message,
  confirmLabel = t('confirm.delete'),
  onConfirm,
  onCancel,
}: Props) {
  return (
    <Dialog
      open={open}
      onOpenChange={(next) => !next && onCancel()}
      title={title}
      size="sm"
      footer={
        <>
          <Button onClick={onCancel}>{t('confirm.cancel')}</Button>
          <Button variant="danger" onClick={onConfirm} autoFocus>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-text">{message}</p>
    </Dialog>
  );
}
