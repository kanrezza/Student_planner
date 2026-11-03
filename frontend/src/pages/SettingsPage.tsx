import { t } from '../i18n/vi';
import { SemestersPage } from './SemestersPage';

/** Cài đặt: hiện có Học kỳ; ca học, nhãn, nhắc lịch được thêm ở các user story sau. */
export function SettingsPage() {
  return (
    <section className="narrow">
      <h1>{t('settings.title')}</h1>
      <SemestersPage />
    </section>
  );
}
