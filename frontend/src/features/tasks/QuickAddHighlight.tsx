import type { QuickToken } from './quickParse';
import { t } from '../../i18n/vi';

/**
 * Lớp tô sáng nằm đè lên ô nhập: chữ trong suốt (để chữ thật của ô nhập hiện ra bên dưới), chỉ nền
 * của các cụm được hiểu hiện màu. Chỉ các cụm nhận chuột, bấm vào thì huỷ hiểu cụm đó (FR-031).
 */
export function QuickAddHighlight({
  text,
  tokens,
  scrollLeft,
  onDismiss,
}: {
  text: string;
  tokens: QuickToken[];
  scrollLeft: number;
  onDismiss: (token: QuickToken) => void;
}) {
  const live = tokens.filter((token) => !token.dismissed);
  const pieces: React.ReactNode[] = [];
  let cursor = 0;
  for (const token of live) {
    if (token.start > cursor) pieces.push(text.slice(cursor, token.start));
    pieces.push(
      <mark
        key={token.key}
        data-token-kind={token.kind}
        title={t('quickAdd.dismissHint')}
        onMouseDown={(e) => e.preventDefault()} // giữ nguyên tiêu điểm của ô nhập
        onClick={() => onDismiss(token)}
        className="pointer-events-auto cursor-pointer rounded-[4px] bg-accent/20 text-transparent"
      >
        {text.slice(token.start, token.end)}
      </mark>,
    );
    cursor = token.end;
  }
  pieces.push(text.slice(cursor));
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-0 flex items-center overflow-hidden whitespace-pre text-[13px] text-transparent"
    >
      <div style={{ transform: `translateX(${-scrollLeft}px)` }}>{pieces}</div>
    </div>
  );
}
