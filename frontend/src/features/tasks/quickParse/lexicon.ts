/**
 * Bảng mẫu nhận diện (contracts/quick-add-grammar.md). Mọi mẫu viết trên chuỗi ĐÃ GẬP (không dấu,
 * chữ thường) nên "thứ sáu", "Thu 6", "THỨ 6" cùng khớp. Cụm chỉ được hiểu khi đứng thành từ riêng
 * (FR-029): trước/sau không dính chữ hoặc số.
 */
import type { Daypart, RecurrenceSpec, TokenKind, TokenValue } from './types';

export type Rule = {
  kind: TokenKind;
  re: RegExp;
  /** Trả null để bỏ qua kết quả khớp (ví dụ ngày không có thật). `original` là chữ gốc đã NFC. */
  build: (m: RegExpExecArray, original: string) => TokenValue | null;
  /** Chỉ dùng khi bật hiểu cụm lặp. */
  recurrenceOnly?: boolean;
};

// Chữ/số đứng liền trước hoặc sau thì không tính là từ riêng.
const L = '(?<![a-z0-9])';
const R = '(?![a-z0-9])';
// Với số, thêm "/" và ":" để không cắt giữa ngày hoặc giờ khác.
const NL = '(?<![a-z0-9:/.])';

// "thu 2".."thu 7", "thu hai".."thu bay", "t2".."t7", "chu nhat", "cn".
const WD = '(?:thu\\s*(?:hai|ba|tu|bon|nam|sau|bay|[2-7])|t[2-7]|chu\\s*nhat|cn)';
// Các thứ sau thứ đầu có thể chỉ viết số: "thứ 2, 4, 6", "thứ 3 và 5".
const WD_NEXT = `(?:${WD}|[2-7](?!\\d))`;
const WD_LIST = `${WD}(?:\\s*,\\s*${WD_NEXT}|\\s+va\\s+${WD_NEXT})*`;

const WORD_TO_WEEKDAY: Record<string, number> = {
  hai: 1,
  ba: 2,
  tu: 3,
  bon: 3,
  nam: 4,
  sau: 5,
  bay: 6,
};

/** "thu 6" → 5 … "cn" → 7 (1 = Thứ Hai … 7 = Chủ Nhật). */
export function weekdayOf(folded: string): number {
  const text = folded.replace(/\s+/g, '');
  if (text === 'cn' || text === 'chunhat') return 7;
  const tNumber = /^t([2-7])$/.exec(text);
  if (tNumber) return Number(tNumber[1]) - 1;
  const word = text.replace(/^thu/, '');
  return /^[2-7]$/.test(word) ? Number(word) - 1 : WORD_TO_WEEKDAY[word];
}

function weekdaysIn(folded: string): number[] {
  const list = folded.replace(/^(?:hang|moi)\s+/, '').replace(/\s+(?:hang|moi)\s+tuan$/, '');
  const found = list
    .split(/\s*,\s*|\s+va\s+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => (/^[2-7]$/.test(part) ? Number(part) - 1 : weekdayOf(part)));
  return [...new Set(found)].filter((day) => day >= 1 && day <= 7);
}

/** "thứ tự" (trình tự) không phải "thứ tư" (Thứ Tư); chỉ phân biệt được khi còn dấu. */
const looksLikeOrder = (original: string) => /thứ\s*tự/i.test(original);

function validDate(day: number, month: number, year: number): boolean {
  const date = new Date(Date.UTC(year, month - 1, day));
  return (
    date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day
  );
}

function clock(hour: number, minute: number): TokenValue | null {
  if (hour > 23 || minute > 59) return null;
  return { type: 'clock', hour, minute, daypart: null, alsoToday: false };
}

const DAYPARTS: Record<string, Daypart> = {
  sang: 'sang',
  trua: 'trua',
  chieu: 'chieu',
  toi: 'toi',
  dem: 'dem',
};

const recurrence = (spec: RecurrenceSpec): TokenValue => ({ type: 'recurrence', spec });

export const RULES: Rule[] = [
  // ---- Ngày ----
  {
    kind: 'date',
    re: new RegExp(`${L}(?:hom\\s+nay|hnay)${R}`, 'g'),
    build: () => ({ type: 'rel', days: 0 }),
  },
  {
    kind: 'date',
    re: new RegExp(`${L}(?:ngay\\s+)?mai${R}`, 'g'),
    build: () => ({ type: 'rel', days: 1 }),
  },
  {
    // "mốt" (ngày kia) trùng "một" khi bỏ dấu: chỉ nhận khi có dấu ố, hoặc đi sau chữ "ngày".
    kind: 'date',
    re: new RegExp(`${L}(ngay\\s+)?mot${R}`, 'g'),
    build: (m, original) => {
      if (/ộ/.test(original)) return null;
      return m[1] || /ố/.test(original) ? { type: 'rel', days: 2 } : null;
    },
  },
  {
    kind: 'date',
    re: new RegExp(`${L}ngay\\s+kia${R}`, 'g'),
    build: () => ({ type: 'rel', days: 2 }),
  },
  {
    kind: 'date',
    re: new RegExp(`${L}(${WD})(?:\\s+tuan\\s+(sau|toi))?${R}`, 'g'),
    build: (m, original) =>
      looksLikeOrder(original)
        ? null
        : { type: 'weekday', weekday: weekdayOf(m[1]), nextWeek: Boolean(m[2]) },
  },
  {
    kind: 'date',
    re: new RegExp(`${L}tuan\\s+(?:sau|toi)${R}`, 'g'),
    build: () => ({ type: 'nextMonday' }),
  },
  {
    kind: 'date',
    re: /(?<![\d/])(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?(?![\d/])/g,
    build: (m) => {
      const day = Number(m[1]);
      const month = Number(m[2]);
      const year = m[3] ? Number(m[3]) : null;
      if (month < 1 || month > 12 || day < 1) return null;
      // Không năm: kiểm tra với một năm nhuận để "29/2" vẫn hợp lệ (năm thật chọn sau).
      return validDate(day, month, year ?? 2096) ? { type: 'calendar', day, month, year } : null;
    },
  },

  // ---- Giờ ----
  {
    kind: 'time',
    re: new RegExp(`${NL}(\\d{1,2}):(\\d{2})(?![\\d:])`, 'g'),
    build: (m) => clock(Number(m[1]), Number(m[2])),
  },
  {
    kind: 'time',
    re: new RegExp(`${NL}(\\d{1,2})\\s*gio(?:\\s*(\\d{1,2})(?:\\s*phut)?)?${R}`, 'g'),
    build: (m) => clock(Number(m[1]), m[2] ? Number(m[2]) : 0),
  },
  {
    kind: 'time',
    re: new RegExp(`${NL}(\\d{1,2})[hg](\\d{2})?${R}`, 'g'),
    build: (m) => clock(Number(m[1]), m[2] ? Number(m[2]) : 0),
  },
  {
    kind: 'time',
    re: new RegExp(`${NL}(\\d{1,2})\\s*(?:h|g|gio)?\\s*ruoi${R}`, 'g'),
    build: (m) => clock(Number(m[1]), 30),
  },
  {
    kind: 'daypart',
    re: new RegExp(`${L}(sang|trua|chieu|toi|dem)(\\s+nay)?${R}`, 'g'),
    build: (m) => ({ type: 'daypart', daypart: DAYPARTS[m[1]], today: Boolean(m[2]) }),
  },

  // ---- Quan trọng, ưu tiên ----
  { kind: 'important', re: /(?<!\S)\*(?!\S)/g, build: () => ({ type: 'important' }) },
  {
    kind: 'important',
    re: new RegExp(`${L}quan\\s+trong${R}`, 'g'),
    build: () => ({ type: 'important' }),
  },
  {
    // Ưu tiên theo nhãn của app: 1 = Cao, 2 = Trung bình, 3 = Thấp.
    kind: 'priority',
    re: new RegExp(`(?<!\\S)!(cao|tb|thap)${R}`, 'g'),
    build: (m) => ({ type: 'priority', priority: m[1] === 'cao' ? 1 : m[1] === 'tb' ? 2 : 3 }),
  },

  // ---- Lặp lại ----
  {
    kind: 'recurrence',
    recurrenceOnly: true,
    re: new RegExp(`${L}(?:hang|moi)\\s+ngay${R}`, 'g'),
    build: () => recurrence({ freq: 'daily' }),
  },
  {
    kind: 'recurrence',
    recurrenceOnly: true,
    re: new RegExp(`${L}moi\\s+(\\d{1,3})\\s+ngay${R}`, 'g'),
    build: (m) => {
      const n = Number(m[1]);
      if (n < 1 || n > 365) return null;
      return recurrence(n === 1 ? { freq: 'daily' } : { freq: 'every_n_days', interval_days: n });
    },
  },
  {
    kind: 'recurrence',
    recurrenceOnly: true,
    re: new RegExp(`${L}(?:hang|moi)\\s+tuan${R}`, 'g'),
    build: () => recurrence({ freq: 'weekly' }),
  },
  {
    kind: 'recurrence',
    recurrenceOnly: true,
    re: new RegExp(`${L}${WD_LIST}\\s+(?:hang|moi)\\s+tuan${R}`, 'g'),
    build: (m) => recurrence({ freq: 'weekly', weekdays: weekdaysIn(m[0]) }),
  },
  {
    kind: 'recurrence',
    recurrenceOnly: true,
    re: new RegExp(`${L}moi\\s+${WD_LIST}${R}`, 'g'),
    build: (m) => recurrence({ freq: 'weekly', weekdays: weekdaysIn(m[0]) }),
  },
  {
    kind: 'recurrence',
    recurrenceOnly: true,
    re: new RegExp(`${L}(?:hang|moi)\\s+thang${R}`, 'g'),
    build: () => recurrence({ freq: 'monthly' }),
  },
  {
    kind: 'recurrence',
    recurrenceOnly: true,
    re: new RegExp(`${L}ngay\\s+(\\d{1,2})\\s+(?:hang|moi)\\s+thang${R}`, 'g'),
    build: (m) => {
      const day = Number(m[1]);
      return day >= 1 && day <= 31 ? recurrence({ freq: 'monthly', month_day: day }) : null;
    },
  },

  // ---- Nhãn, danh sách (tên một từ; tên nhiều từ do tokenize xử lý theo danh sách có sẵn) ----
  {
    kind: 'tag',
    re: /(?<![^\s(])#[^\s#~*!,;:()]+/g,
    build: () => ({ type: 'tag', tagId: null, name: '' }),
  },
  { kind: 'list', re: /(?<![^\s(])~[^\s#~*!,;:()]+/g, build: () => ({ type: 'list', listId: -1 }) },
];
