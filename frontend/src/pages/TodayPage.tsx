import { t } from '../i18n/vi';
import { formatDayLong, toIsoDate } from '../lib/dates';

/** Khung trang "Hôm nay" (FR-019, FR-020); nội dung được làm ở User Story 3. */
export function TodayPage() {
  const today = toIsoDate(new Date());
  return (
    <section>
      <h1>{t('today.title', { date: formatDayLong(today) })}</h1>
      <p className="muted">{t('common.comingSoon')}</p>
    </section>
  );
}
