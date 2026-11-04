import { t } from '../i18n/vi';
import { cx } from '../ui/cx';
import { PALETTE, PALETTE_CODES } from '../lib/colors';

/** Chọn 1 trong 12 màu cố định (FR-018, FR-042). `value = null` nghĩa là để ứng dụng tự chọn. */
export function ColorPicker({
  value,
  onChange,
}: {
  value: string | null;
  onChange: (code: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5" role="radiogroup" aria-label={t('colors.pick')}>
      {PALETTE_CODES.map((code, i) => (
        <button
          key={code}
          type="button"
          role="radio"
          aria-checked={value === code}
          aria-label={t('colors.option', { n: i + 1 })}
          className={cx(
            'h-6 w-6 rounded-full ring-offset-2 ring-offset-surface transition-shadow',
            value === code ? 'ring-2 ring-text' : 'hover:ring-2 hover:ring-border-strong',
          )}
          style={{ backgroundColor: PALETTE[code] }}
          onClick={() => onChange(code)}
        />
      ))}
    </div>
  );
}
