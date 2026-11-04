import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cx } from './cx';
import { Tooltip } from './Tooltip';

type Props = Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> & {
  /** Chú thích tiếng Việt, dùng cho trình đọc màn hình và tooltip (bắt buộc). */
  label: string;
  icon: ReactNode;
  active?: boolean;
  size?: 'sm' | 'md' | 'lg';
  tooltip?: boolean;
  tooltipSide?: 'top' | 'right' | 'bottom' | 'left';
};

const SIZES = { sm: 'h-6 w-6', md: 'h-7 w-7', lg: 'h-9 w-9' };

/** Nút chỉ có biểu tượng, luôn có chú thích tiếng Việt. */
export const IconButton = forwardRef<HTMLButtonElement, Props>(function IconButton(
  {
    label,
    icon,
    active = false,
    size = 'md',
    tooltip = true,
    tooltipSide = 'bottom',
    className,
    type = 'button',
    ...rest
  },
  ref,
) {
  const button = (
    <button
      ref={ref}
      type={type}
      aria-label={label}
      className={cx(
        'inline-flex shrink-0 items-center justify-center rounded-md text-muted transition-colors',
        'hover:bg-surface-3 hover:text-text disabled:opacity-40',
        active && 'bg-accent-soft text-accent-strong hover:bg-accent-soft hover:text-accent-strong',
        SIZES[size],
        className,
      )}
      {...rest}
    >
      {icon}
    </button>
  );
  return tooltip ? (
    <Tooltip content={label} side={tooltipSide}>
      {button}
    </Tooltip>
  ) : (
    button
  );
});
