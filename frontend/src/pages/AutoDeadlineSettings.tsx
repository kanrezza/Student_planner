import { useState } from 'react';
import { useSaveSettings, useSettings } from '../api/settings';
import { t } from '../i18n/vi';

/** Cài đặt → Tự tạo deadline (US10, FR-048): mốc giờ tối, giờ deadline Chủ Nhật, môn ngoại lệ. */
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
    <section className="panel">
      <h2>{t('autoDeadline.title')}</h2>
      <p className="muted">{t('autoDeadline.help')}</p>
      <div className="form-row">
        <label className="field">
          <span className="field__label">{t('autoDeadline.eveningFrom')}</span>
          <input
            type="time"
            value={s.auto_deadline_evening_from}
            onChange={(e) =>
              e.target.value && save.mutate({ auto_deadline_evening_from: e.target.value })
            }
          />
        </label>
        <label className="field">
          <span className="field__label">{t('autoDeadline.dueTime')}</span>
          <input
            type="time"
            value={s.auto_deadline_due_time}
            onChange={(e) =>
              e.target.value && save.mutate({ auto_deadline_due_time: e.target.value })
            }
          />
        </label>
      </div>
      <span className="field__label">{t('autoDeadline.excluded')}</span>
      <div className="tag-chips">
        {keywords.map((k) => (
          <span key={k} className="tag-chip">
            {k}
            <button
              type="button"
              className="button--ghost"
              aria-label={t('autoDeadline.remove', { keyword: k })}
              onClick={() =>
                save.mutate({ auto_deadline_excluded_keywords: keywords.filter((x) => x !== k) })
              }
            >
              ✕
            </button>
          </span>
        ))}
      </div>
      <div className="row-actions" style={{ marginTop: '0.5rem' }}>
        <input
          placeholder={t('autoDeadline.keywordPlaceholder')}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
        />
        <button type="button" onClick={addKeyword}>
          {t('autoDeadline.add')}
        </button>
      </div>
      {save.error && <p className="field__error">{save.error.message}</p>}
    </section>
  );
}
