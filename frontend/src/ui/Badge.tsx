import type { ReactNode } from 'react';
import { cx } from './cx';

const TONES = {
  neutral: 'bg-surface-3 text-muted',
  accent: 'bg-accent-soft text-accent-strong',
  danger: 'bg-danger-soft text-danger',
  warning: 'bg-warning-soft text-warning',
};

export function Badge({
  tone = 'neutral',
  children,
  className,
}: {
  tone?: keyof typeof TONES;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 rounded-full px-2 py-px text-[11px] font-medium leading-4',
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
