import { t } from '../i18n/vi';

export function PlaceholderPage({ titleKey }: { titleKey: string }) {
  return (
    <section>
      <h1>{t(titleKey)}</h1>
      <p className="muted">{t('common.comingSoon')}</p>
    </section>
  );
}
