import { useRef, useState } from 'react';
import { isoToVnDate, parseVnDate } from '../lib/dates';
import { t } from '../i18n/vi';
import { cx } from '../ui/cx';

/**
 * Ô nhập ngày kiểu Việt Nam: hiển thị và gõ "DD/MM/YYYY", nhưng `value`/`onChange` luôn là
 * "YYYY-MM-DD" (định dạng API). Có nút mở lịch chọn ngày. Gõ chưa đủ/sai → báo lỗi tại chỗ
 * và `onChange('')`, không bao giờ gửi chuỗi sai lên API.
 */
export function DateInput({
  value,
  onChange,
  onBlur,
  label,
  className,
  invalid,
  title,
  uncertain,
}: {
  value: string | null | undefined;
  onChange: (iso: string) => void;
  onBlur?: () => void;
  label?: string;
  className?: string;
  invalid?: boolean;
  title?: string;
  uncertain?: boolean;
}) {
  const iso = value ?? '';
  const [text, setText] = useState(isoToVnDate(iso));
  const [bad, setBad] = useState(false);
  const picker = useRef<HTMLInputElement>(null);

  // Đồng bộ khi giá trị bên ngoài đổi (không phải do chính ô này vừa gõ).
  const typedIso = parseVnDate(text) ?? '';
  if (typedIso !== iso && !(bad && iso === '')) {
    setText(isoToVnDate(iso));
    setBad(false);
  }

  function type(next: string) {
    setText(next);
    if (next.trim() === '') {
      setBad(false);
      onChange('');
      return;
    }
    const parsed = parseVnDate(next);
    setBad(parsed === null);
    onChange(parsed ?? '');
  }

  function openPicker() {
    const el = picker.current;
    if (!el) return;
    try {
      el.showPicker();
    } catch {
      el.focus();
    }
  }

  return (
    <span className={cx('relative inline-flex min-w-0 items-center', className)}>
      <input
        type="text"
        inputMode="numeric"
        autoComplete="off"
        placeholder="DD/MM/YYYY"
        aria-label={label}
        title={title}
        data-uncertain={uncertain ? 'true' : undefined}
        value={text}
        onChange={(e) => type(e.target.value)}
        onBlur={() => {
          if (!bad && typedIso) setText(isoToVnDate(typedIso));
          onBlur?.();
        }}
        aria-invalid={bad || invalid ? true : undefined}
        className={cx('w-full min-w-0 pr-8', uncertain && 'border-warning bg-warning-soft')}
      />
      <button
        type="button"
        tabIndex={-1}
        aria-label={t('common.pickDate')}
        onClick={openPicker}
        className="absolute right-1 text-muted hover:text-text"
      >
        📅
      </button>
      <input
        ref={picker}
        type="date"
        tabIndex={-1}
        aria-hidden="true"
        value={iso}
        onChange={(e) => type(isoToVnDate(e.target.value))}
        className="pointer-events-none absolute right-0 h-0 w-0 opacity-0"
      />
      {bad && (
        <span role="alert" className="absolute left-0 top-full text-[11px] text-danger">
          {t('common.dateFormat')}
        </span>
      )}
    </span>
  );
}
