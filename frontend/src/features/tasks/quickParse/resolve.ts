/** Từ các cụm được hiểu → giá trị cụ thể của task (contracts/quick-add-grammar.md, FR-028). */
import { addDays, formatDate, formatTime, isoWeekday, toIsoDate } from '../../../lib/dates';
import { DEFAULT_DAYPART_TIME, finalizeHour, pad2 } from './clock';
import { foldVi } from '../../../lib/foldVi';
import type {
  QuickFields,
  QuickParseContext,
  QuickToken,
  RecurrenceRule,
  RecurrenceSpec,
  TokenValue,
} from './types';

type ClockValue = Extract<TokenValue, { type: 'clock' }>;

type Resolved = { fields: QuickFields; dueInPast: boolean; rangeError: boolean };

function lastDayOfMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

const isoDate = (year: number, month: number, day: number) => `${year}-${pad2(month)}-${pad2(day)}`;

/** Ngày thứ `day` của tháng (tháng thiếu ngày thì lấy ngày cuối tháng, FR-018). */
function monthDate(year: number, month: number, day: number): string {
  return isoDate(year, month, Math.min(day, lastDayOfMonth(year, month)));
}

function resolveClock(value: ClockValue): { time: string; dayShift: number } | null {
  const done = finalizeHour(value.hour, value.daypart);
  return done
    ? { time: `${pad2(done.hour)}:${pad2(value.minute)}`, dayShift: done.dayShift }
    : null;
}

/** Ngày của cụm ngày; `time` dùng để biết "thứ hôm nay" đã qua giờ chưa. */
function dateOf(
  value: TokenValue,
  today: string,
  nowTime: string,
  time: string | null,
): string | null {
  const todayWeekday = isoWeekday(today);
  switch (value.type) {
    case 'rel':
      return addDays(today, value.days);
    case 'nextMonday':
      return addDays(today, 8 - todayWeekday);
    case 'weekday': {
      if (value.nextWeek) return addDays(addDays(today, 8 - todayWeekday), value.weekday - 1);
      let delta = (value.weekday - todayWeekday + 7) % 7;
      if (delta === 0 && time !== null && time <= nowTime) delta = 7; // hôm nay mà giờ đã qua
      return addDays(today, delta);
    }
    case 'calendar': {
      if (value.year !== null) return isoDate(value.year, value.month, value.day);
      // Không năm: năm nay, hoặc năm gần nhất sau đó nếu ngày này đã qua (29/2 chờ tới năm nhuận).
      const thisYear = Number(today.slice(0, 4));
      for (let year = thisYear; year <= thisYear + 8; year += 1) {
        if (value.day > lastDayOfMonth(year, value.month)) continue;
        const candidate = isoDate(year, value.month, value.day);
        if (candidate >= today) return candidate;
      }
      return null;
    }
    default:
      return null;
  }
}

/**
 * Ngày đầu tiên khớp quy tắc, từ `base` trở đi (không sinh ngày đã qua). Giờ đã qua chỉ có nghĩa khi
 * `base` là hôm nay.
 */
function firstDateOfRecurrence(
  spec: RecurrenceSpec,
  base: string,
  today: string,
  nowTime: string,
  time: string | null,
): string {
  const passedToday = base === today && time !== null && time <= nowTime;
  if (spec.freq === 'weekly') {
    const days = spec.weekdays?.length ? spec.weekdays : [isoWeekday(base)];
    for (let offset = passedToday ? 1 : 0; offset <= 7; offset += 1) {
      if (days.includes(isoWeekday(addDays(base, offset)))) return addDays(base, offset);
    }
  }
  if (spec.freq === 'monthly') {
    const [year, month, day] = base.split('-').map(Number);
    const wanted = spec.month_day ?? day;
    const thisMonth = monthDate(year, month, wanted);
    if (thisMonth > base || (thisMonth === base && !passedToday)) return thisMonth;
    return month === 12 ? monthDate(year + 1, 1, wanted) : monthDate(year, month + 1, wanted);
  }
  return passedToday ? addDays(base, 1) : base; // hằng ngày / mỗi N ngày
}

/** Ngày bắt đầu của khoảng: "6/11" không năm tính cùng năm với ngày kết thúc (FR-028a). */
function rangeStart(
  from: TokenValue,
  to: string,
  today: string,
  nowTime: string,
  time: string | null,
): string | null {
  if (from.type === 'calendar' && from.year === null) {
    const year = Number(to.slice(0, 4));
    if (from.day <= lastDayOfMonth(year, from.month)) {
      const sameYear = isoDate(year, from.month, from.day);
      if (sameYear <= to && sameYear < today) return sameYear; // đã qua nhưng không sau B
    }
  }
  return dateOf(from, today, nowTime, time);
}

function finishRecurrence(
  spec: RecurrenceSpec,
  dueDate: string | undefined,
  endDate: string | null,
): RecurrenceRule {
  const rule: RecurrenceRule = {
    ...spec,
    end: endDate ? { kind: 'on_date', date: endDate } : { kind: 'never' },
  };
  if (spec.freq === 'weekly' && !spec.weekdays?.length) {
    rule.weekdays = [dueDate ? isoWeekday(dueDate) : 0].filter(Boolean);
  }
  if (spec.freq === 'monthly' && spec.month_day === undefined && dueDate) {
    rule.month_day = Number(dueDate.slice(8));
  }
  return rule;
}

export function resolve(tokens: QuickToken[], ctx: QuickParseContext): Resolved {
  const today = toIsoDate(ctx.now);
  const nowTime = formatTime(ctx.now.toISOString());
  const live = tokens.filter((token) => !token.dismissed);
  const fields: QuickFields = { tag_ids: [], tag_names: [] };
  const seenNames = new Set<string>();

  let dateValue: TokenValue | null = null;
  let time: string | null = null;
  let daypartTime: string | null = null; // giờ mặc định của buổi, chỉ dùng khi không có giờ cụ thể
  let dayShift = 0;
  let alsoToday = false;
  let spec: RecurrenceSpec | null = null;
  let range: Extract<TokenValue, { type: 'range' }> | null = null;

  for (const { value } of live) {
    switch (value.type) {
      case 'rel':
      case 'weekday':
      case 'nextMonday':
      case 'calendar':
        dateValue = value;
        break;
      case 'clock': {
        const done = resolveClock(value);
        if (done) {
          ({ time, dayShift } = done);
          alsoToday = value.alsoToday;
        }
        if (value.date) dateValue = value.date;
        break;
      }
      case 'daypart':
        daypartTime = DEFAULT_DAYPART_TIME[value.daypart];
        alsoToday = value.today;
        break;
      case 'dateDaypart':
        dateValue = value.date;
        daypartTime = DEFAULT_DAYPART_TIME[value.daypart];
        break;
      case 'tag':
        if (value.tagId !== null) {
          if (!fields.tag_ids.includes(value.tagId)) fields.tag_ids.push(value.tagId);
        } else if (!seenNames.has(foldVi(value.name).folded)) {
          seenNames.add(foldVi(value.name).folded);
          fields.tag_names.push(value.name);
        }
        break;
      case 'list':
        fields.list_id = value.listId;
        break;
      case 'important':
        fields.is_important = true;
        break;
      case 'priority':
        fields.priority = value.priority;
        break;
      case 'recurrence':
        spec = value.spec;
        break;
      case 'range':
        range = value;
        break;
    }
  }

  time ??= daypartTime;

  // Khoảng ngày "từ A đến B" (FR-028a).
  let dueDate: string | undefined;
  let endDate: string | null = null;
  let rangeError = false;
  let rangeDone = false;
  if (range) {
    const to = dateOf(range.to, today, nowTime, time);
    const from = range.from && to ? rangeStart(range.from, to, today, nowTime, time) : null;
    if (!to || (range.from && (!from || from > to))) {
      rangeError = true;
    } else if (spec) {
      const base = from && from > today ? from : today;
      const first = firstDateOfRecurrence(spec, base, today, nowTime, time);
      if (first > to) rangeError = true;
      else {
        dueDate = first;
        endDate = to;
        rangeDone = true;
      }
    } else {
      dueDate = to;
      if (from) fields.notes = `Bắt đầu: ${formatDate(from)}`;
      rangeDone = true;
    }
  }
  if (rangeDone) {
    // đã có hạn từ khoảng ngày
  } else if (dateValue) {
    dueDate = dateOf(dateValue, today, nowTime, time) ?? undefined;
  } else if (alsoToday) {
    dueDate = today;
  } else if (spec) {
    dueDate = firstDateOfRecurrence(spec, today, today, nowTime, time);
  } else if (time !== null) {
    dueDate = ctx.viewDefaultDate ?? (time > nowTime ? today : addDays(today, 1));
  }
  if (dueDate && dayShift) dueDate = addDays(dueDate, dayShift);

  if (dueDate) fields.due_date = dueDate;
  if (dueDate && time !== null) fields.due_time = time;
  if (spec) fields.recurrence = finishRecurrence(spec, dueDate, endDate);

  const dueInPast = dueDate
    ? dueDate < today || (dueDate === today && time !== null && time < nowTime)
    : false;
  return { fields, dueInPast, rangeError };
}
