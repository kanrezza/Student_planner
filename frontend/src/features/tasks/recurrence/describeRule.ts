import type { RecurrenceRule } from '../../../api/types';
import { t } from '../../../i18n/vi';
import { formatDate } from '../../../lib/dates';
import { describeRecurrence } from '../quickParse/describe';

/**
 * Mô tả quy tắc lặp bằng tiếng Việt (FR-021), ví dụ
 * "Lặp hằng tuần vào Thứ Hai, Thứ Năm · đến 30/11/2026", "Lặp mỗi 3 ngày", "Lặp hằng tháng vào ngày 31 · 3 lần".
 */
export function describeRule(rule: RecurrenceRule): string {
  const base = t('recurrence.repeat', { rule: describeRecurrence(rule) });
  switch (rule.end.kind) {
    case 'on_date':
      return `${base} · ${t('recurrence.until', { date: formatDate(rule.end.date) })}`;
    case 'after_count':
      return `${base} · ${t('recurrence.times', { n: rule.end.count })}`;
    default:
      return base;
  }
}
