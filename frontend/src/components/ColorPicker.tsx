import { t } from '../i18n/vi';
import { PALETTE, PALETTE_CODES } from '../lib/colors';

/** Chọn 1 trong 12 màu cố định của ứng dụng (FR-018, FR-042). */
export function ColorPicker({
  value,
  onChange,
}: {
  value: string;
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
