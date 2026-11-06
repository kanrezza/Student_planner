/** Tô sáng chữ khớp từ khoá không phân biệt dấu/hoa thường (spec FR-039, research R15). */
import { foldVi, originalEnd } from '../../lib/foldVi';

export type Range = [start: number, end: number];

/** Các khoảng [start, end) trong `text` khớp một từ bất kỳ của `query`; khoảng chồng nhau được gộp. */
export function highlightRanges(text: string, query: string): Range[] {
  const words = foldVi(query).folded.split(/\s+/).filter(Boolean);
  if (words.length === 0) return [];
  const { folded, map } = foldVi(text);
  const found: Range[] = [];
  for (const word of words) {
    for (let at = folded.indexOf(word); at >= 0; at = folded.indexOf(word, at + word.length)) {
      found.push([map[at], originalEnd(text, map, at + word.length)]);
    }
  }
  found.sort((a, b) => a[0] - b[0] || b[1] - a[1]);
  const merged: Range[] = [];
  for (const range of found) {
    const last = merged[merged.length - 1];
    // Chồng nhau hoặc chỉ cách nhau khoảng trắng ("nộp" + "bài") thì tô liền một khối.
    if (last && (range[0] <= last[1] || /^\s*$/.test(text.slice(last[1], range[0])))) {
      last[1] = Math.max(last[1], range[1]);
    } else merged.push([...range]);
  }
  return merged;
}
