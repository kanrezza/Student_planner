import type { ReactNode } from 'react';
import { cx } from './cx';

/**
 * Bảng bên phải (bảng chi tiết). Cửa sổ rộng: là một cột đẩy nội dung sang; cửa sổ hẹp (< 900px):
 * phủ lên khu vực chính (edge case của spec).
 */
export function SidePanel({
  label,
  children,
  className,
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <aside
      aria-label={label}
      className={cx(
        'absolute inset-y-0 right-0 z-30 flex w-[min(380px,100%)] flex-col border-l border-border',
        'bg-surface shadow-panel min-[900px]:static min-[900px]:z-auto min-[900px]:shadow-none',
        className,
      )}
    >
      {children}
    </aside>
  );
}
