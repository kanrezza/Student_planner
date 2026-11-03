import { t } from '../i18n/vi';

/** Công tắc "Quan trọng" (FR-067): một lần bấm để bật/tắt. */
export function ImportantToggle({
  value,
  onChange,
}: {
  value: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <button
      type="button"
      className={`important-toggle${value ? ' is-on' : ''}`}
      aria-pressed={value}
      onClick={() => onChange(!value)}
    >
      {value ? '★' : '☆'} {t('important.label')}
    </button>
  );
}

export type ImportanceChoice = 'inherit' | 'yes' | 'no';

export function overrideToChoice(value: boolean | null): ImportanceChoice {
  return value === null ? 'inherit' : value ? 'yes' : 'no';
}

export function choiceToOverride(choice: ImportanceChoice): boolean | null {
  return choice === 'inherit' ? null : choice === 'yes';
}

/** Mức quan trọng riêng của một buổi học: theo môn / quan trọng / không quan trọng. */
export function ImportanceSelect({
  value,
  onChange,
  subjectImportant,
}: {
  value: ImportanceChoice;
  onChange: (value: ImportanceChoice) => void;
  subjectImportant: boolean;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value as ImportanceChoice)}>
      <option value="inherit">
        {t('important.inherit', {
          value: subjectImportant ? t('important.yes') : t('important.no'),
        })}
      </option>
      <option value="yes">{t('important.yes')}</option>
      <option value="no">{t('important.no')}</option>
    </select>
  );
}
