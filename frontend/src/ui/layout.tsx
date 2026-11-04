/** Khối bố cục dùng chung của các màn hình (feature 002 FR-033: một phong cách nhất quán). */
import type { ReactNode } from 'react';
import { cx } from './cx';

/** Màn hình có tiêu đề lớn và vùng nội dung cuộn được. */
export function Screen({
  title,
  subtitle,
  actions,
  children,
  width = 'max-w-[860px]',
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  width?: string;
}) {
  return (
    <div className="flex h-full flex-col">
      <header className="flex shrink-0 flex-wrap items-center gap-3 px-8 pb-3 pt-[calc(20px+var(--titlebar-inset))]">
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-[22px] leading-8 font-bold tracking-tight">{title}</h1>
          {subtitle && <p className="text-muted">{subtitle}</p>}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-8 pb-10">
        <div className={cx('mx-auto flex flex-col gap-5', width)}>{children}</div>
      </div>
    </div>
  );
}

/** Thẻ nội dung có tiêu đề, mô tả và nút ở góc phải. */
export function Card({
  title,
  description,
  actions,
  children,
  id,
}: {
  title?: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  children?: ReactNode;
  id?: string;
}) {
  return (
    <section id={id} className="rounded-xl border border-border bg-surface p-5">
      {(title || actions) && (
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            {title && <h2 className="text-[15px] font-semibold">{title}</h2>}
            {description && <p className="mt-0.5 text-muted">{description}</p>}
          </div>
          {actions && <div className="flex shrink-0 gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

/** Tiêu đề nhỏ bên trong thẻ. */
export function SubHeading({ children }: { children: ReactNode }) {
  return <h3 className="mb-2 mt-5 font-semibold first:mt-0">{children}</h3>;
}

/** Danh sách dạng bảng nhẹ: các dòng cách nhau bởi đường kẻ mảnh. */
export function ItemList({ children }: { children: ReactNode }) {
  return (
    <ul className="flex flex-col divide-y divide-border rounded-xl border border-border bg-surface">
      {children}
    </ul>
  );
}

export function ItemRow({
  color,
  leading,
  title,
  meta,
  actions,
}: {
  color?: string;
  leading?: ReactNode;
  title: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <li className="group flex items-center gap-3 px-4 py-2.5">
      {color && (
        <span className="h-9 w-1 shrink-0 rounded-full" style={{ backgroundColor: color }} />
      )}
      {leading}
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{title}</div>
        {meta && <div className="flex flex-wrap gap-x-3 text-[12px] text-muted">{meta}</div>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-1">{actions}</div>}
    </li>
  );
}

const NOTICE_TONES = {
  info: 'bg-accent-soft text-accent-strong',
  warning: 'bg-warning-soft text-warning',
  danger: 'bg-danger-soft text-danger',
  success: 'bg-accent-soft text-accent-strong',
};

export function Notice({
  tone = 'info',
  children,
}: {
  tone?: keyof typeof NOTICE_TONES;
  children: ReactNode;
}) {
  return (
    <div role="status" className={cx('rounded-lg px-3 py-2', NOTICE_TONES[tone])}>
      {children}
    </div>
  );
}

/** Ô đánh dấu kèm nhãn (checkbox gốc của trình duyệt, tô màu nhấn). */
export function CheckboxLine({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: ReactNode;
}) {
  return (
    <label className="my-2 flex items-center gap-2">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

/** Mã lệnh để người dùng chép. */
export function Code({ children }: { children: ReactNode }) {
  return (
    <pre className="mt-1 overflow-x-auto rounded-md bg-surface-3 px-3 py-2 font-mono text-[12px] text-text">
      {children}
    </pre>
  );
}
