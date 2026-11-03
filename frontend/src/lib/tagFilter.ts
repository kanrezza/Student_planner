/** Bộ lọc nhãn lưu trong tham số URL `?tags=1,2`, nên giữ nguyên khi đổi chế độ xem (FR-045). */

export function parseTagParam(value: string | null): number[] {
  if (!value) return [];
  return value
    .split(',')
    .map((part) => Number(part))
    .filter((n) => Number.isInteger(n) && n > 0);
}

export function formatTagParam(ids: number[]): string | null {
  return ids.length ? ids.join(',') : null;
}

export function toggleTag(ids: number[], id: number): number[] {
  return ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id];
}
