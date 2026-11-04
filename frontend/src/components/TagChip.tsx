import { cx } from '../ui/cx';

/** Chip nhãn bấm được: chọn thì tô màu của nhãn (chữ trắng đủ tương phản, xem lib/colors). */
export function TagChip({
  name,
  color,
  selected,
  order,
  onClick,
}: {
  name: string;
  color: string;
  selected: boolean;
  order?: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={cx(
        'inline-flex h-6 items-center gap-1 rounded-full border px-2.5 text-[12px] font-medium',
        selected ? 'text-white' : 'bg-surface text-text hover:bg-surface-3',
      )}
      style={selected ? { backgroundColor: color, borderColor: color } : { borderColor: color }}
    >
      {!selected && <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} />}
      {order !== undefined && (
        <span className="rounded-full bg-white/25 px-1 text-[10px] leading-4">{order}</span>
      )}
      {name}
    </button>
  );
}
