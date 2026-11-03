import { useEffect, useRef, type ReactNode } from 'react';
import { t } from '../i18n/vi';

/** Hộp thoại dùng thẻ <dialog> có sẵn; đóng bằng Esc hoặc nút "Đóng". */
export function Modal({
  title,
  onClose,
  children,
  wide = false,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.open) dialog.showModal?.();
    return () => dialog?.close?.();
  }, []);

  return (
    <dialog
      ref={ref}
      className={`dialog${wide ? ' dialog--wide' : ''}`}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      aria-labelledby="modal-title"
    >
      <div className="dialog__header">
        <h2 id="modal-title">{title}</h2>
        <button
          type="button"
          className="button--ghost"
          onClick={onClose}
          aria-label={t('common.close')}
        >
          ✕
        </button>
      </div>
      {children}
    </dialog>
  );
}
