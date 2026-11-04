import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { cx } from './cx';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md';

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-accent-contrast hover:bg-accent-hover shadow-sm',
  secondary: 'bg-surface text-text border border-border hover:bg-surface-3',
  ghost: 'text-text hover:bg-surface-3',
  danger: 'bg-danger-soft text-danger hover:brightness-95',
};

const SIZES: Record<ButtonSize, string> = {
  sm: 'h-7 px-2.5 text-[12px] gap-1',
  md: 'h-8 px-3.5 gap-1.5',
};

export const buttonClass = (variant: ButtonVariant = 'secondary', size: ButtonSize = 'md') =>
  cx(
    'inline-flex shrink-0 items-center justify-center rounded-md font-medium whitespace-nowrap',
    'transition-colors disabled:pointer-events-none disabled:opacity-50',
    VARIANTS[variant],
    SIZES[size],
  );

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

/** Nút dùng chung: primary (hành động chính), secondary, ghost, danger. */
export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  { variant = 'secondary', size = 'md', className, type = 'button', ...rest },
  ref,
) {
  return (
    <button ref={ref} type={type} className={cx(buttonClass(variant, size), className)} {...rest} />
  );
});
