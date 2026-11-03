import { t } from '../i18n/vi';
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
    <div className="color-picker" role="radiogroup" aria-label={t('colors.pick')}>
      {PALETTE_CODES.map((code, i) => (
        <button
          key={code}
          type="button"
          role="radio"
          aria-checked={value === code}
          aria-label={t('colors.option', { n: i + 1 })}
          className={`color-picker__swatch${value === code ? ' is-selected' : ''}`}
          style={{ backgroundColor: PALETTE[code] }}
          onClick={() => onChange(code)}
        />
      ))}
    </div>
  );
}
