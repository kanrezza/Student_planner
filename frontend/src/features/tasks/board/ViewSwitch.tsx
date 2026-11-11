import { t } from '../../../i18n/vi';
import { cx } from '../../../ui/cx';

export type TasksViewMode = 'list' | 'board';

/** Nút phân đoạn "Danh sách | Bảng" ở đầu trang Công việc (feature 005, FR-007). */
export function ViewSwitch({
  mode,
  onChange,
}: {
  mode: TasksViewMode;
  onChange: (mode: TasksViewMode) => void;
}) {
  return (
    <div
      role="group"
      aria-label={t('board.viewSwitch')}
      className="flex shrink-0 rounded-lg border border-border bg-surface-2 p-0.5"
    >
      {(['list', 'board'] as const).map((value) => (
        <button
          key={value}
          type="button"
          aria-pressed={mode === value}
          onClick={() => onChange(value)}
          className={cx(
            'rounded-md px-3 py-1 text-[13px] font-medium',
            mode === value ? 'bg-surface shadow-sm' : 'text-muted hover:text-text',
          )}
        >
          {t(value === 'list' ? 'board.viewList' : 'board.viewBoard')}
        </button>
      ))}
    </div>
  );
}
