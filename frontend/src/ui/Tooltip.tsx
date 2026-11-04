import * as RadixTooltip from '@radix-ui/react-tooltip';
import type { ReactNode } from 'react';

/** Chú thích khi rê chuột (FR-007). Tự có Provider nên dùng được ở bất cứ đâu. */
export function Tooltip({
  content,
  children,
  side = 'bottom',
}: {
  content: ReactNode;
  children: ReactNode;
  side?: 'top' | 'right' | 'bottom' | 'left';
}) {
  return (
    <RadixTooltip.Provider delayDuration={450} skipDelayDuration={200}>
      <RadixTooltip.Root>
        <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
        <RadixTooltip.Portal>
          <RadixTooltip.Content
            side={side}
            sideOffset={6}
            className="z-50 max-w-xs rounded-md bg-text px-2 py-1 text-[12px] leading-4 text-bg shadow-pop"
          >
            {content}
          </RadixTooltip.Content>
        </RadixTooltip.Portal>
      </RadixTooltip.Root>
    </RadixTooltip.Provider>
  );
}
