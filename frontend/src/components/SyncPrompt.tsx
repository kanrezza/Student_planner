import { useSaveSettings, useSettings } from '../api/settings';
import { t } from '../i18n/vi';
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
      <p className="muted">{t('reminders.syncHelp')}</p>
      <div className="dialog__actions">
        <button type="button" onClick={() => answer(false)}>
          {t('reminders.promptLater')}
        </button>
        <button type="button" className="button--primary" onClick={() => answer(true)}>
          {t('reminders.promptEnable')}
        </button>
      </div>
    </Modal>
  );
}
