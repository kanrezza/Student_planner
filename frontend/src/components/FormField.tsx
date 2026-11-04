import type { ReactNode } from 'react';
import { ApiError } from '../api/client';
import { cx } from '../ui/cx';

type Props = {
  label: string;
  /** Tên trường theo API, ví dụ "title" hoặc "rows[2].end_time". */
  name: string;
  error?: unknown;
  children: ReactNode;
  className?: string;
  /** Lỗi do giao diện tự kiểm tra (ưu tiên hơn lỗi từ API). */
  message?: string | null;
};

/** Lấy thông báo lỗi của một trường từ `ApiError.fields` (thông điệp tiếng Việt từ backend). */
export function fieldError(error: unknown, name: string): string | undefined {
  return error instanceof ApiError ? error.fields[name] : undefined;
}

/** Nhãn + ô nhập + lỗi ngay dưới ô (FR-013). */
export function FormField({ label, name, error, children, className, message }: Props) {
  const text = message ?? fieldError(error, name);
  return (
    <label className={cx('mb-3 flex min-w-0 flex-col gap-1', className)}>
      <span className="text-[12px] font-medium text-muted">{label}</span>
      {children}
      {text && (
        <span className="text-[12px] text-danger" role="alert">
          {text}
        </span>
      )}
    </label>
  );
}

/** Hàng nhiều ô nằm ngang. */
export function FormRow({ children }: { children: ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-x-3 sm:grid-flow-col sm:auto-cols-fr">{children}</div>
  );
}
