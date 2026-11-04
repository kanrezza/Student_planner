import type { MouseEvent } from 'react';
import { cx } from './cx';

const PRIORITY_RING: Record<number, string> = {
  1: 'border-danger',
  2: 'border-border-strong',
  3: 'border-border-strong',
};

/**
 * Ô đánh dấu hoàn thành: vuông bo góc, đã xong thì tô màu nhấn và có dấu tích.
 * Dùng `role="checkbox"` để trình đọc màn hình hiểu đúng.
 */
export function Checkbox({
  checked,
  onChange,
  label,
  disabled = false,
  priority = 2,
  className,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  disabled?: boolean;
  priority?: number;
  className?: string;
}) {
  function toggle(e: MouseEvent) {
    e.stopPropagation(); // bấm checkbox không mở bảng chi tiết
    if (!disabled) onChange(!checked);
  }
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={toggle}
      className={cx(
        'inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-[5px] border-[1.5px]',
        'transition-colors disabled:opacity-50',
        checked
          ? 'border-accent bg-accent text-accent-contrast'
          : cx('bg-surface hover:bg-accent-soft', PRIORITY_RING[priority] ?? PRIORITY_RING[2]),
        className,
      )}
    >
      {checked && (
        <svg viewBox="0 0 12 12" width="10" height="10" aria-hidden>
          <path
            d="m2.5 6.2 2.3 2.3 4.7-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </button>
  );
}
