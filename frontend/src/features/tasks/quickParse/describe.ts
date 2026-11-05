import { WEEKDAYS_VN } from '../../../lib/dates';
import { t } from '../../../i18n/vi';
import type { RecurrenceRule } from './types';

/** "hằng ngày", "mỗi 3 ngày", "hằng tuần vào Thứ Hai, Thứ Năm", "hằng tháng vào ngày 5". */
export function describeRecurrence(rule: RecurrenceRule): string {
  switch (rule.freq) {
    case 'daily':
      return t('quickAdd.repeatDaily');
    case 'every_n_days':
      return t('quickAdd.repeatEveryDays', { n: rule.interval_days ?? 0 });
    case 'weekly':
      return t('quickAdd.repeatWeekly', {
        days: (rule.weekdays ?? []).map((day) => WEEKDAYS_VN[day - 1]).join(', '),
      });
    case 'monthly':
      return t('quickAdd.repeatMonthly', { day: rule.month_day ?? 0 });
  }
}
