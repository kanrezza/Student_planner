import type { ReactNode } from 'react';
import { Dialog } from '../ui/Dialog';

/** Hộp thoại có tiêu đề; giữ API của feature 001, bên trong dùng `ui/Dialog` (Radix). */
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
  return (
    <Dialog
      open
      onOpenChange={(open) => !open && onClose()}
      title={title}
      size={wide ? 'lg' : 'md'}
    >
      {children}
    </Dialog>
  );
}
