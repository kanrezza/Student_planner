import { cx } from './cx';

/** Công tắc bật/tắt (role="switch"). */
export function Switch({
  checked,
  onChange,
  label,
  disabled = false,
  id,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  disabled?: boolean;
  id?: string;
}) {
  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cx(
        'relative inline-flex h-[18px] w-8 shrink-0 items-center rounded-full transition-colors',
        'disabled:opacity-50',
        checked ? 'bg-accent' : 'bg-border-strong',
      )}
    >
      <span
        className={cx(
          'inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform',
          checked ? 'translate-x-[15px]' : 'translate-x-[2px]',
        )}
      />
    </button>
  );
}
