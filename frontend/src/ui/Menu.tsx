import * as RadixMenu from '@radix-ui/react-dropdown-menu';
import type { ReactNode } from 'react';
import { cx } from './cx';

/** Menu thả xuống (menu ⋯, chọn chế độ lịch). */
export function Menu({
  trigger,
  children,
  align = 'end',
}: {
  trigger: ReactNode;
  children: ReactNode;
  align?: 'start' | 'center' | 'end';
}) {
  return (
    <RadixMenu.Root modal={false}>
      <RadixMenu.Trigger asChild>{trigger}</RadixMenu.Trigger>
      <RadixMenu.Portal>
        <RadixMenu.Content
          align={align}
          sideOffset={4}
          className="z-50 min-w-[180px] rounded-lg border border-border bg-surface p-1 shadow-pop"
        >
          {children}
        </RadixMenu.Content>
      </RadixMenu.Portal>
    </RadixMenu.Root>
  );
}

export function MenuItem({
  children,
  onSelect,
  danger = false,
  icon,
  checked,
}: {
  children: ReactNode;
  onSelect: () => void;
  danger?: boolean;
  icon?: ReactNode;
  checked?: boolean;
}) {
  return (
    <RadixMenu.Item
      onSelect={onSelect}
      className={cx(
        'flex h-7 cursor-default select-none items-center gap-2 rounded-md px-2 outline-none',
        'data-[highlighted]:bg-surface-3',
        danger ? 'text-danger' : 'text-text',
      )}
    >
      <span className="flex w-4 justify-center text-muted">
        {checked ? <span className="text-accent">✓</span> : icon}
      </span>
      {children}
    </RadixMenu.Item>
  );
}

export function MenuSeparator() {
  return <RadixMenu.Separator className="my-1 h-px bg-border" />;
}
