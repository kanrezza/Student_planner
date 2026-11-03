import type { Shift } from '../api/types';

export type ShiftRange = {
  key: string; // "1-2"
  start_shift_id: number;
  end_shift_id: number;
  label: string; // "Ca 1–2"
  start_time: string;
  end_time: string;
};

/** "Ca 1" hoặc "Ca 1–2" — giống `shift_label` ở backend. */
export function rangeLabel(first: Shift, last: Shift): string {
  if (first.id === last.id) return first.name;
  const lastName =
    first.name.startsWith('Ca ') && last.name.startsWith('Ca ') ? last.name.slice(3) : last.name;
  return `${first.name}–${lastName}`;
}

/** Mọi ca đơn và dãy ca liền nhau (ca cuối ≥ ca đầu), theo thứ tự ca (FR-039). */
export function shiftRanges(shifts: Shift[]): ShiftRange[] {
  const ordered = [...shifts].sort((a, b) => a.position - b.position);
  const ranges: ShiftRange[] = [];
  ordered.forEach((first, i) => {
    for (const last of ordered.slice(i)) {
      ranges.push({
        key: `${first.id}-${last.id}`,
        start_shift_id: first.id,
        end_shift_id: last.id,
        label: rangeLabel(first, last),
        start_time: first.start_time,
        end_time: last.end_time,
      });
    }
  });
  return ranges;
}
