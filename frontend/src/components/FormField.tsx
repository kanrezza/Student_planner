import type { ReactNode } from 'react';
import { ApiError } from '../api/client';

type Props = {
  label: string;
  /** Tên trường theo API, ví dụ "title" hoặc "rows[2].end_time". */
  name: string;
  error?: unknown;
  children: ReactNode;
};

/** Lấy thông báo lỗi của một trường từ `ApiError.fields` (thông điệp tiếng Việt từ backend). */
export function fieldError(error: unknown, name: string): string | undefined {
  return error instanceof ApiError ? error.fields[name] : undefined;
}

export function FormField({ label, name, error, children }: Props) {
  const message = fieldError(error, name);
  return (
    <label className={`field${message ? ' field--error' : ''}`}>
      <span className="field__label">{label}</span>
      {children}
      {message && (
        <span className="field__error" role="alert">
          {message}
        </span>
      )}
    </label>
  );
}
