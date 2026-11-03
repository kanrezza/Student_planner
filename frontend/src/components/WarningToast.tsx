import type { ApiWarning } from '../api/client';
import { t } from '../i18n/vi';

/** Hiển thị cảnh báo không chặn từ API (ví dụ trùng giờ, FR-015). */
export function WarningToast({
  warnings,
  onClose,
}: {
  warnings: ApiWarning[];
  onClose: () => void;
}) {
  if (warnings.length === 0) return null;
  return (
    <div className="toast" role="status">
      <ul>
        {warnings.map((w) => (
          <li key={`${w.code}:${w.message}`}>{w.message}</li>
        ))}
      </ul>
      <button type="button" onClick={onClose}>
        {t('common.close')}
      </button>
    </div>
  );
}
