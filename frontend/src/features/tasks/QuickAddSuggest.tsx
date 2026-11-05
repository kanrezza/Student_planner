import { foldKey } from '../../lib/foldVi';
import { t } from '../../i18n/vi';

export type SuggestionItem = { id: number; label: string; color?: string; emoji?: string | null };

/** "#gap" ở cuối câu (trước con trỏ) → gợi ý nhãn; "~ca" → gợi ý danh sách. */
export function findSuggestionQuery(
  text: string,
  caret: number,
): { mark: '#' | '~'; query: string; start: number } | null {
  const before = text.slice(0, caret);
  const match = /(?:^|[\s(])([#~])([^\s#~*!,;:()]*)$/.exec(before);
  if (!match) return null;
  return { mark: match[1] as '#' | '~', query: match[2], start: caret - match[2].length - 1 };
}

export function filterSuggestions(items: SuggestionItem[], query: string): SuggestionItem[] {
  const key = foldKey(query);
  return items.filter((item) => foldKey(item.label).includes(key)).slice(0, 6);
}

/** Danh sách gợi ý nhãn/danh sách ngay dưới ô nhập (↑/↓, Enter/Tab chọn, Esc đóng — FR-034). */
export function QuickAddSuggest({
  mark,
  items,
  active,
  onPick,
}: {
  mark: '#' | '~';
  items: SuggestionItem[];
  active: number;
  onPick: (item: SuggestionItem) => void;
}) {
  return (
    <ul
      role="listbox"
      aria-label={mark === '#' ? t('quickAdd.suggestTags') : t('quickAdd.suggestLists')}
      className="absolute left-0 top-full z-20 mt-1 w-full min-w-[220px] overflow-hidden rounded-lg border border-border bg-surface py-1 shadow-lg"
    >
      {items.map((item, index) => (
        <li
          key={item.id}
          role="option"
          aria-selected={index === active}
          onMouseDown={(e) => {
            e.preventDefault();
            onPick(item);
          }}
          className={`flex cursor-pointer items-center gap-2 px-3 py-1.5 ${index === active ? 'bg-surface-3' : 'hover:bg-surface-2'}`}
        >
          {mark === '#' ? (
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
          ) : (
            <span>{item.emoji ?? '📋'}</span>
          )}
          <span>{item.label}</span>
        </li>
      ))}
    </ul>
  );
}
