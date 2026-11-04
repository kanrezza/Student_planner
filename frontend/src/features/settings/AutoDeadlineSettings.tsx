import { useState } from 'react';
import { useSaveSettings, useSettings } from '../../api/settings';
import { t } from '../../i18n/vi';
import { Button } from '../../ui/Button';
import { IconButton } from '../../ui/IconButton';
import { IconClose } from '../../ui/icons';
import { Card, SubHeading } from '../../ui/layout';

/**
 * Cài đặt → Tự tạo deadline (US10, FR-048, FR-071): mốc giờ tối, giờ deadline Chủ Nhật, nhắc tối
 * hôm trước hạn, môn ngoại lệ.
 */
export function AutoDeadlineSettings() {
  const settings = useSettings();
  const save = useSaveSettings();
  const [keyword, setKeyword] = useState('');
  const s = settings.data;
  if (!s) return null;

  const keywords = s.auto_deadline_excluded_keywords;
  function addKeyword() {
    const value = keyword.trim();
    if (!value) return;
    save.mutate({ auto_deadline_excluded_keywords: [...keywords, value] });
    setKeyword('');
  }

  return (
    <Card title={t('autoDeadline.title')} description={t('autoDeadline.help')}>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1">
          <span className="text-[12px] font-medium text-muted">
            {t('autoDeadline.eveningFrom')}
          </span>
          <input
            type="time"
            value={s.auto_deadline_evening_from}
            onChange={(e) =>
              e.target.value && save.mutate({ auto_deadline_evening_from: e.target.value })
            }
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[12px] font-medium text-muted">{t('autoDeadline.dueTime')}</span>
          <input
            type="time"
            value={s.auto_deadline_due_time}
            onChange={(e) =>
              e.target.value && save.mutate({ auto_deadline_due_time: e.target.value })
            }
          />
        </label>
      </div>
      <EveReminderField
        value={s.auto_deadline_eve_reminder_time}
        onChange={(v) => save.mutate({ auto_deadline_eve_reminder_time: v })}
      />
      <SubHeading>{t('autoDeadline.excluded')}</SubHeading>
      <div className="flex flex-wrap gap-1.5">
        {keywords.map((k) => (
          <span
            key={k}
            className="inline-flex h-7 items-center gap-1 rounded-full bg-surface-3 pl-3 pr-1 text-[12px] font-medium"
          >
            {k}
            <IconButton
              size="sm"
              tooltip={false}
              icon={<IconClose size={12} />}
              label={t('autoDeadline.remove', { keyword: k })}
              onClick={() =>
                save.mutate({ auto_deadline_excluded_keywords: keywords.filter((x) => x !== k) })
              }
            />
          </span>
        ))}
      </div>
      <div className="mt-3 flex items-center gap-2">
        <input
          placeholder={t('autoDeadline.keywordPlaceholder')}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
          className="w-56"
        />
        <Button onClick={addKeyword}>{t('autoDeadline.add')}</Button>
      </div>
      {save.error && <p className="mt-2 text-danger">{save.error.message}</p>}
    </Card>
  );
}

const DEFAULT_EVE_TIME = '20:00';

/** Nhắc tối hôm trước hạn cho task tự tạo (FR-071): bật/tắt và giờ nhắc. */
export function EveReminderField({
  value,
  onChange,
}: {
  value: string | null;
  onChange: (value: string | null) => void;
}) {
  return (
    <div className="mt-3 flex flex-wrap items-end gap-4">
      <label className="flex h-8 items-center gap-2">
        <input
          type="checkbox"
          checked={value !== null}
          onChange={(e) => onChange(e.target.checked ? DEFAULT_EVE_TIME : null)}
        />
        {t('autoDeadline.eveReminder')}
      </label>
      {value !== null && (
        <label className="flex w-40 flex-col gap-1">
          <span className="text-[12px] font-medium text-muted">
            {t('autoDeadline.eveReminderTime')}
          </span>
          <input
            type="time"
            value={value}
            onChange={(e) => e.target.value && onChange(e.target.value)}
          />
        </label>
      )}
    </div>
  );
}
