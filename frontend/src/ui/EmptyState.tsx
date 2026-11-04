import type { ReactNode } from 'react';

/** Trạng thái trống: biểu tượng lớn mờ, tiêu đề, mô tả ngắn. */
export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-16 text-center">
      {icon && <div className="mb-1 text-border-strong">{icon}</div>}
      <p className="text-[15px] font-semibold text-text">{title}</p>
      {description && <p className="max-w-sm text-muted">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
