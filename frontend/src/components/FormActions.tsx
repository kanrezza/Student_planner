import { t } from '../i18n/vi';
import { Button } from '../ui/Button';

/** Hàng nút Huỷ / Lưu ở cuối form. */
export function FormActions({
  saving,
  onCancel,
  saveLabel = t('common.save'),
}: {
  saving: boolean;
  onCancel: () => void;
  saveLabel?: string;
}) {
  return (
    <div className="mt-5 flex justify-end gap-2">
      <Button onClick={onCancel}>{t('common.cancel')}</Button>
      <Button type="submit" variant="primary" disabled={saving}>
        {saveLabel}
      </Button>
    </div>
  );
}
