import { foldVi, originalEnd } from '../../../lib/foldVi';
import { finalizeHour } from './clock';
import { RULES } from './lexicon';
import type {
  DateValue,
  Daypart,
  QuickParseContext,
  QuickToken,
  TokenKind,
  TokenValue,
} from './types';

type Candidate = Omit<QuickToken, 'dismissed' | 'key'>;

const SLOT: Partial<Record<TokenKind, string>> = {
  date: 'date',
  time: 'time',
  daypart: 'time',
  recurrence: 'recurrence',
  list: 'list',
  priority: 'priority',
};

/** Các "ô" mà một cụm chiếm: giờ đi liền ngày ("sáng mai 9h") chiếm cả ô giờ lẫn ô ngày. */
function slotsOf(candidate: Candidate): string[] {
  const own = SLOT[candidate.kind];
  if (!own) return [];
  const { value } = candidate;
  return value.type === 'clock' && value.date ? [own, 'date'] : [own];
}

// Từ ghép chứa "sáng/tối/chiều": không phải buổi trong ngày ("tối ưu", "sáng tạo", "chiều chuộng"…).
const COMPOUND_AFTER: Record<Daypart, string[]> = {
  sang: ['tao', 'kien', 'suot', 'che', 'lap', 'tac', 'gia', 'ngoi', 'loang', 'sua'],
  toi: ['uu', 'gian', 'da', 'thieu', 'cao', 'mat', 'tan', 'om'],
  chieu: ['chuong', 'cao', 'dai', 'rong', 'sau', 'theo', 'y', 'long'],
  trua: [],
  dem: [],
};
const COMPOUND_BEFORE: Partial<Record<Daypart, string[]>> = { sang: ['anh'] }; // "ánh sáng"

// "mai" đứng sau các từ gọi người là tên riêng ("chị Mai"), không phải ngày mai.
const PERSON_WORDS = new Set([
  'chi',
  'anh',
  'em',
  'co',
  'thay',
  'ban',
  'ba',
  'ong',
  'chu',
  'bac',
  'di',
  'cau',
]);

const firstWord = (text: string) => /^\s*([a-z0-9]+)/.exec(foldVi(text).folded)?.[1] ?? '';
const lastWord = (text: string) => /([a-z0-9]+)\s*$/.exec(foldVi(text).folded)?.[1] ?? '';

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
      if (value?.type === 'rel' && isPersonName(m[0], original, text, map[fStart])) continue;
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

/** "mai" đứng một mình là tên người khi theo sau chị/anh/em/cô/thầy… hoặc viết hoa "Mai" giữa câu. */
function isPersonName(foldedMatch: string, original: string, text: string, start: number): boolean {
  if (!/^mai$/.test(foldedMatch)) return false; // "ngày mai" luôn là ngày
  if (original === 'Mai' && text.slice(0, start).trim() !== '') return true;
  return PERSON_WORDS.has(lastWord(text.slice(0, start)));
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

const isDateValue = (value: TokenValue): value is DateValue =>
  value.type === 'rel' ||
  value.type === 'weekday' ||
  value.type === 'nextMonday' ||
  value.type === 'calendar';

const isTimeLike = (candidate: Candidate) =>
  isDateValue(candidate.value) ||
  candidate.value.type === 'clock' ||
  candidate.value.type === 'daypart';

/** "tối ưu", "sáng tạo", "chiều chuộng"…: buổi nằm trong từ ghép thì không phải giờ giấc. */
function isCompoundWord(candidate: Candidate, text: string): boolean {
  if (candidate.value.type !== 'daypart') return false;
  const { daypart } = candidate.value;
  return (
    COMPOUND_AFTER[daypart].includes(firstWord(text.slice(candidate.end))) ||
    (COMPOUND_BEFORE[daypart]?.includes(lastWord(text.slice(0, candidate.start))) ?? false)
  );
}

/**
 * Gộp buổi với giờ/ngày đứng sát nhau: "9 giờ tối", "sáng 9h", "sáng mai", "chiều thứ 6",
 * "CN chiều", "sáng mai 9h". Buổi đứng riêng (không kèm giờ hay ngày) không được hiểu, trừ "tối nay".
 * Gộp ra giờ không hợp lệ ("12h sáng") thì bỏ cả cụm, giữ nguyên là chữ.
 */
function mergeRun(run: Candidate[], text: string): Candidate[] {
  const part = run.find((c) => c.value.type === 'daypart');
  if (!part || part.value.type !== 'daypart') return run;
  const dateToken = run.find((c) => isDateValue(c.value));
  const clockToken = run.find((c) => c.value.type === 'clock' && c.value.daypart === null);
  const others = run.filter((c) => c.value.type !== 'daypart');
  if (!dateToken && !clockToken) return part.value.today ? [part, ...others] : others;

  const members = [part, dateToken, clockToken].filter((c): c is Candidate => c !== undefined);
  const start = Math.min(...members.map((c) => c.start));
  const end = Math.max(...members.map((c) => c.end));
  const date = dateToken && isDateValue(dateToken.value) ? dateToken.value : undefined;
  const { daypart, today } = part.value;
  if (clockToken && clockToken.value.type === 'clock') {
    const { hour, minute } = clockToken.value;
    if (finalizeHour(hour, daypart) === null) return []; // ví dụ "12h sáng"
    const value: TokenValue = { type: 'clock', hour, minute, daypart, alsoToday: today, date };
    return [{ kind: 'time', start, end, text: text.slice(start, end), value }];
  }
  if (!date) return [part];
  const value: TokenValue = { type: 'dateDaypart', date, daypart };
  return [{ kind: 'date', start, end, text: text.slice(start, end), value }];
}

function mergeDayparts(tokens: Candidate[], text: string): Candidate[] {
  const kept = tokens.filter((token) => !isCompoundWord(token, text));
  const merged: Candidate[] = [];
  let index = 0;
  while (index < kept.length) {
    const run = [kept[index]];
    while (
      isTimeLike(run[run.length - 1]) &&
      index + 1 < kept.length &&
      isTimeLike(kept[index + 1]) &&
      /^\s*$/.test(text.slice(run[run.length - 1].end, kept[index + 1].start))
    ) {
      index += 1;
      run.push(kept[index]);
    }
    index += 1;
    merged.push(...mergeRun(run, text));
  }
  return merged;
}

/** Các cụm được hiểu trong câu, theo thứ tự xuất hiện (gồm cả cụm đã bị người dùng huỷ hiểu). */
export function tokenize(text: string, ctx: QuickParseContext): QuickToken[] {
  const merged = mergeDayparts(selectNonOverlapping(candidates(text, ctx)), text);
  const usedSlots = new Set<string>();
  const tokens: QuickToken[] = [];
  for (const candidate of merged) {
    const key = `${candidate.kind}:${candidate.start}:${candidate.text}`;
    const dismissed = ctx.dismissed.has(key);
    const slots = slotsOf(candidate);
    if (!dismissed && slots.length) {
      if (slots.some((slot) => usedSlots.has(slot))) continue; // mỗi loại chỉ hiểu cụm đầu tiên (FR-028)
      slots.forEach((slot) => usedSlots.add(slot));
    }
    tokens.push({ ...candidate, dismissed, key });
  }
  return tokens;
}
