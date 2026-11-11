import { useState } from 'react';
import { useCanonicalNames, useClearCanonicalNames } from '../../api/canonicalNames';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { t } from '../../i18n/vi';
import { formatDate } from '../../lib/dates';
import { Button } from '../../ui/Button';
import { Card } from '../../ui/layout';

/** Tên môn chuẩn lấy từ PDF thời khoá biểu (feature 004, FR-028, FR-029). */
export function CanonicalNamesSettings() {
  const names = useCanonicalNames();
  const clear = useClearCanonicalNames();
  const [confirming, setConfirming] = useState(false);
  const list = names.data ?? [];

  return (
    <Card
      title={t('canonical.title')}
      description={t('canonical.note')}
      actions={
        <Button disabled={list.length === 0} onClick={() => setConfirming(true)}>
          {t('canonical.clear')}
        </Button>
      }
    >
      {list.length === 0 ? (
        <p className="text-muted">{t('canonical.empty')}</p>
      ) : (
        <table className="w-full text-left">
          <thead className="text-[12px] font-medium text-muted">
            <tr>
              <th>{t('canonical.colName')}</th>
              <th>{t('canonical.colCode')}</th>
              <th>{t('canonical.colAdded')}</th>
            </tr>
          </thead>
          <tbody>
            {list.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td className="text-muted">{item.course_code ?? '—'}</td>
                <td className="tabular-nums text-muted">
                  {formatDate(item.created_at.slice(0, 10))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <ConfirmDialog
        open={confirming}
        title={t('canonical.title')}
        message={t('canonical.confirmClear', { count: list.length })}
        confirmLabel={t('canonical.clear')}
        onCancel={() => setConfirming(false)}
        onConfirm={() => {
          setConfirming(false);
          clear.mutate();
        }}
      />
    </Card>
  );
}
