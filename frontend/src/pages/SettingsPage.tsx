import { t } from '../i18n/vi';
import { AutoDeadlineSettings } from './AutoDeadlineSettings';
import { ReminderSettings } from './ReminderSettings';
import { SemestersPage } from './SemestersPage';
import { ShiftsPage } from './ShiftsPage';
import { TagsPage } from './TagsPage';

/** Cài đặt: nhắc lịch và đồng bộ, học kỳ, ca học, nhãn, tự tạo deadline. */
export function SettingsPage() {
  return (
    <section className="narrow settings">
      <h1>{t('settings.title')}</h1>
      <ReminderSettings />
      <SemestersPage />
      <ShiftsPage />
      <TagsPage />
      <AutoDeadlineSettings />
    </section>
  );
}
