import { useSaveSettings, useSettings } from '../api/settings';
import { t } from '../i18n/vi';
import { Button } from '../ui/Button';
import { Modal } from './Modal';

/** Lần đầu mở ứng dụng: đề nghị bật đồng bộ với Lịch và Lời nhắc (FR-051). Chỉ hỏi một lần. */
export function SyncPrompt() {
  const settings = useSettings();
  const save = useSaveSettings();
  if (!settings.data || settings.data.calendar_sync_prompted) return null;

  const answer = (enable: boolean) =>
    save.mutate({
      calendar_sync_prompted: true,
      ...(enable ? { calendar_sync_enabled: true } : {}),
    });

  return (
    <Modal title={t('reminders.promptTitle')} onClose={() => answer(false)}>
      <p>{t('reminders.promptBody')}</p>
      <p className="mt-2 text-muted">{t('reminders.syncHelp')}</p>
      <div className="mt-5 flex justify-end gap-2">
        <Button onClick={() => answer(false)}>{t('reminders.promptLater')}</Button>
        <Button variant="primary" onClick={() => answer(true)}>
          {t('reminders.promptEnable')}
        </Button>
      </div>
    </Modal>
  );
}
