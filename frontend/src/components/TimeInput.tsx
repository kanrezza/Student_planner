import { useState, type KeyboardEvent } from 'react';
import { t } from '../i18n/vi';
import { cx } from '../ui/cx';

/**
 * Đọc giờ gõ tay: "23:30", "23h30", "23g30", "23.30", "2330", "930", "9", "9h" → "HH:MM".
 * Rỗng → "" (không có giờ); sai (ví dụ "25:00", "9:75", chữ) → null.
 */
export function parseTimeText(text: string): string | null {
  const s = text.trim().toLowerCase();
  if (s === '') return '';
  let hour: string;
  let minute = '00';
  const compact = /^(\d{3,4})$/.exec(s);
  const split = /^(\d{1,2})(?:\s*[:h.g]\s*(\d{1,2})?)?$/.exec(s);
  if (compact) {
    hour = compact[1].slice(0, -2);
    minute = compact[1].slice(-2);
  } else if (split) {
    hour = split[1];
    minute = (split[2] ?? '0').padStart(2, '0');
  } else return null;
  if (Number(hour) > 23 || Number(minute) > 59) return null;
  return `${hour.padStart(2, '0')}:${minute}`;
}

/**
 * Ô nhập giờ 24 giờ "HH:MM" tự đọc chữ gõ vào, thay cho `<input type="time">` (ô gốc của WebKit theo
 * giờ 12/24 của hệ thống và chỉ báo giá trị khi đủ mọi đoạn nên "gõ 23:30" có thể không lưu được).
 * `onChange` nhận "HH:MM", "" (trống) hoặc "" khi chữ chưa hợp lệ; `onBlur` nhận giá trị hợp lệ vừa
 * gõ, hoặc giá trị cũ `value` nếu chữ sai (không bao giờ gửi chuỗi sai lên API). Enter = rời ô.
 */
export function TimeInput({
  value,
  onChange,
  onBlur,
  label,
  disabled,
  invalid,
  className,
}: {
  value: string;
  onChange: (time: string) => void;
  onBlur?: (time: string) => void;
  label: string;
  disabled?: boolean;
  invalid?: boolean;
  className?: string;
}) {
  const [text, setText] = useState(value);
  const [bad, setBad] = useState(false);

  // Đồng bộ khi giá trị bên ngoài đổi (không phải do chính ô này vừa gõ).
  const typed = parseTimeText(text);
  if ((typed ?? '') !== value && !(bad && value === '')) {
    setText(value);
    setBad(false);
  }

  function type(next: string) {
    setText(next);
    const parsed = parseTimeText(next);
    setBad(parsed === null);
    onChange(parsed ?? '');
  }

  function leave(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.nativeEvent.isComposing) e.currentTarget.blur();
  }

  return (
    <input
      type="text"
      inputMode="numeric"
      autoComplete="off"
      placeholder="HH:MM"
      aria-label={label}
      value={text}
      disabled={disabled}
      title={bad ? t('common.timeFormat') : undefined}
      onChange={(e) => type(e.target.value)}
      onKeyDown={leave}
      onBlur={(e) => {
        const parsed = parseTimeText(e.currentTarget.value);
        if (parsed !== null) setText(parsed);
        onBlur?.(parsed ?? value);
      }}
      aria-invalid={bad || invalid ? true : undefined}
      className={cx('px-2', className)}
    />
  );
}
