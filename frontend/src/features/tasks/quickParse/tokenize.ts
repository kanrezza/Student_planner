import { foldVi, originalEnd } from '../../../lib/foldVi';
import { finalizeHour } from './clock';
import { RULES } from './lexicon';
import type { QuickParseContext, QuickToken, TokenKind, TokenValue } from './types';

type Candidate = Omit<QuickToken, 'dismissed' | 'key'>;

const SLOT: Partial<Record<TokenKind, string>> = {
  date: 'date',
  time: 'time',
  daypart: 'time',
  recurrence: 'recurrence',
  list: 'list',
  priority: 'priority',
};

const escapeRegex = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function candidates(text: string, ctx: QuickParseContext): Candidate[] {
  const { folded, map } = foldVi(text);
  const found: Candidate[] = [];

  const add = (kind: TokenKind, fStart: number, fEnd: number, value: TokenValue | null) => {
    if (!value || fEnd <= fStart) return;
    const start = map[fStart];
    const end = originalEnd(text, map, fEnd);
    found.push({ kind, start, end, text: text.slice(start, end), value });
  };

  for (const rule of RULES) {
    if (rule.recurrenceOnly && !ctx.recurrence) continue;
    for (const m of folded.matchAll(rule.re)) {
      const fStart = m.index;
      const fEnd = fStart + m[0].length;
      const original = text.slice(map[fStart], originalEnd(text, map, fEnd)).normalize('NFC');
      let value = rule.build(m as RegExpExecArray, original);
      if (value && rule.kind === 'tag') value = tagValue(original.slice(1), ctx);
      if (value && rule.kind === 'list') value = listValue(original.slice(1), ctx);
      add(rule.kind, fStart, fEnd, value);
    }
  }

  // Tên có dấu cách chọn từ gợi ý ("#Học tập", "~Cá nhân"): khớp nguyên tên có sẵn.
  const known = [
    ...ctx.tags
      .filter((t) => t.name.includes(' '))
      .map((t) => ({ mark: '#', name: t.name, kind: 'tag' as const })),
    ...ctx.lists
      .filter((l) => l.name.includes(' '))
      .map((l) => ({ mark: '~', name: l.name, kind: 'list' as const })),
  ];
  for (const entry of known) {
    const needle = foldVi(entry.name).folded.trim().replace(/\s+/g, '\\s+');
    const re = new RegExp(`(?<![^\\s(])${escapeRegex(entry.mark)}${needle}(?![a-z0-9])`, 'g');
    for (const m of folded.matchAll(re)) {
      const original = text.slice(map[m.index], originalEnd(text, map, m.index + m[0].length));
      const value =
        entry.kind === 'tag' ? tagValue(original.slice(1), ctx) : listValue(original.slice(1), ctx);
      add(entry.kind, m.index, m.index + m[0].length, value);
    }
  }
  return found;
}

function tagValue(name: string, ctx: QuickParseContext): TokenValue | null {
  if (!name) return null;
  const key = foldVi(name).folded;
  const existing = ctx.tags.find((tag) => foldVi(tag.name).folded.trim() === key);
  return { type: 'tag', tagId: existing?.id ?? null, name: existing?.name ?? name };
}

function listValue(name: string, ctx: QuickParseContext): TokenValue | null {
  const key = foldVi(name).folded.replace(/\s+/g, ' ');
  const list = ctx.lists.find((l) => foldVi(l.name).folded.trim().replace(/\s+/g, ' ') === key);
  return list ? { type: 'list', listId: list.id } : null; // danh sách không có thì giữ là chữ
}

/** Chọn các khoảng không chồng nhau: bắt đầu sớm trước, cùng chỗ thì cụm dài hơn thắng. */
function selectNonOverlapping(all: Candidate[]): Candidate[] {
  const sorted = [...all].sort((a, b) => a.start - b.start || b.end - a.end);
  const chosen: Candidate[] = [];
  let lastEnd = -1;
  for (const candidate of sorted) {
    if (candidate.start >= lastEnd) {
      chosen.push(candidate);
      lastEnd = candidate.end;
    }
  }
  return chosen;
}

/**
 * Giờ và buổi đứng sát nhau ("9 giờ tối", "sáng 9h", "tối nay 21:00") gộp thành một cụm.
 * Gộp ra giờ không hợp lệ ("12h sáng") thì bỏ cả hai, giữ nguyên là chữ.
 */
function mergeClockAndDaypart(tokens: Candidate[], text: string): Candidate[] {
  const result: Candidate[] = [];
  for (let i = 0; i < tokens.length; i += 1) {
    const a = tokens[i];
    const b = tokens[i + 1];
    const pair =
      a && b && /^\s*$/.test(text.slice(a.end, b.start))
        ? a.value.type === 'clock' && a.value.daypart === null && b.value.type === 'daypart'
          ? { clock: a, part: b }
          : a.value.type === 'daypart' && b.value.type === 'clock' && b.value.daypart === null
            ? { clock: b, part: a }
            : null
        : null;
    if (!pair || pair.clock.value.type !== 'clock' || pair.part.value.type !== 'daypart') {
      result.push(a);
      continue;
    }
    i += 1;
    const { hour, minute } = pair.clock.value;
    const { daypart, today } = pair.part.value;
    if (finalizeHour(hour, daypart) === null) continue; // bỏ cả hai
    const start = Math.min(a.start, b.start);
    const end = Math.max(a.end, b.end);
    result.push({
      kind: 'time',
      start,
      end,
      text: text.slice(start, end),
      value: { type: 'clock', hour, minute, daypart, alsoToday: today },
    });
  }
  return result;
}

/** Các cụm được hiểu trong câu, theo thứ tự xuất hiện (gồm cả cụm đã bị người dùng huỷ hiểu). */
export function tokenize(text: string, ctx: QuickParseContext): QuickToken[] {
  const merged = mergeClockAndDaypart(selectNonOverlapping(candidates(text, ctx)), text);
  const usedSlots = new Set<string>();
  const tokens: QuickToken[] = [];
  for (const candidate of merged) {
    const key = `${candidate.kind}:${candidate.start}:${candidate.text}`;
    const dismissed = ctx.dismissed.has(key);
    const slot = SLOT[candidate.kind];
    if (!dismissed && slot) {
      if (usedSlots.has(slot)) continue; // mỗi loại chỉ hiểu cụm đầu tiên (FR-028)
      usedSlots.add(slot);
    }
    tokens.push({ ...candidate, dismissed, key });
  }
  return tokens;
}
