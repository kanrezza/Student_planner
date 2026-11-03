import { t } from '../i18n/vi';
import { SemestersPage } from './SemestersPage';
import { ShiftsPage } from './ShiftsPage';
import { TagsPage } from './TagsPage';

/** Cài đặt: học kỳ, ca học, nhãn. Nhắc lịch và đồng bộ được thêm ở User Story 7. */
export function SettingsPage() {
  return (
    <section className="narrow settings">
      <h1>{t('settings.title')}</h1>
      <SemestersPage />
      <ShiftsPage />
      <TagsPage />
    </section>
  );
}
