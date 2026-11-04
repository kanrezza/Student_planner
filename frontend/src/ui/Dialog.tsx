import * as RadixDialog from '@radix-ui/react-dialog';
import type { ReactNode } from 'react';
import { t } from '../i18n/vi';
import { cx } from './cx';
import { IconClose } from './icons';

/**
 * Hộp thoại giữa màn hình (Radix Dialog): khoá focus, đóng bằng Esc hoặc bấm ra ngoài.
 * Thay cho thẻ <dialog> của feature 001.
 */
export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  size = 'md',
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
}) {
  const width = { sm: 'max-w-[400px]', md: 'max-w-[520px]', lg: 'max-w-[760px]' }[size];
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-40 bg-overlay" />
        <RadixDialog.Content
          className={cx(
            'fixed left-1/2 top-[12vh] z-50 flex max-h-[76vh] w-[calc(100vw-32px)] -translate-x-1/2',
            'flex-col rounded-xl border border-border bg-surface shadow-pop focus:outline-none',
            width,
          )}
        >
          <div className="flex items-start justify-between gap-4 px-5 pt-4">
            <RadixDialog.Title className="text-[15px] font-semibold">{title}</RadixDialog.Title>
            <RadixDialog.Close
              aria-label={t('common.close')}
              className="-mr-1.5 -mt-0.5 rounded-md p-1 text-muted hover:bg-surface-3 hover:text-text"
            >
              <IconClose size={16} />
            </RadixDialog.Close>
          </div>
          {description ? (
            <RadixDialog.Description className="px-5 pt-1 text-muted">
              {description}
            </RadixDialog.Description>
          ) : (
            <RadixDialog.Description className="sr-only">{title}</RadixDialog.Description>
          )}
          <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-5 pt-3">{children}</div>
          {footer && (
            <div className="flex justify-end gap-2 border-t border-border px-5 py-3">{footer}</div>
          )}
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}

/** Hàng nút cuối form trong hộp thoại. */
export function DialogActions({ children }: { children: ReactNode }) {
  return <div className="mt-5 flex justify-end gap-2">{children}</div>;
}
