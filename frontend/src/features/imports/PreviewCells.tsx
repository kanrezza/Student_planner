import type { PreviewField } from '../../api/imports';
import { cx } from '../../ui/cx';

/**
 * Ô sửa được của bảng xem trước. Ô chưa chắc chắn tô vàng, lý do hiện khi rê chuột (FR-030);
 * bấm vào ô (hoặc sửa) là xác nhận.
 */
export function PreviewInput({
  field,
  onChange,
  onConfirm,
  label,
  type = 'text',
  className,
}: {
  field: PreviewField<string | number | null>;
  onChange: (value: string) => void;
  onConfirm: () => void;
  label: string;
  type?: 'text' | 'date' | 'time' | 'number';
  className?: string;
}) {
  const uncertain = !field.certain;
  return (
    <input
      aria-label={label}
      type={type}
      value={field.value ?? ''}
      title={uncertain ? field.reason : undefined}
      data-uncertain={uncertain ? 'true' : undefined}
      onChange={(e) => onChange(e.target.value)}
      onFocus={() => undefined}
      onBlur={() => (uncertain && field.value ? onConfirm() : undefined)}
      className={cx(
        'h-8 w-full min-w-0 px-2',
        uncertain && 'border-warning bg-warning-soft',
        className,
      )}
    />
  );
}
