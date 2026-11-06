import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
import type { Scope } from '../../../api/tasks';
import { t } from '../../../i18n/vi';
import { Button } from '../../../ui/Button';
import { Dialog } from '../../../ui/Dialog';

export type ScopeKind = 'edit' | 'delete';

type Ask = (kind: ScopeKind) => Promise<Scope | null>;

/** Ngoài `ScopeProvider` (ví dụ trong test đơn lẻ) coi như người dùng bấm Huỷ. */
const ScopeContext = createContext<Ask>(() => Promise.resolve(null));

/** Hỏi phạm vi: trả `'this'`, `'following'` hoặc `null` khi Huỷ (FR-020). */
export const useAskScope = (): Ask => useContext(ScopeContext);

/** Hộp thoại "Chỉ lần này / Lần này và các lần sau / Huỷ" cho task lặp. */
export function ScopeDialog({
  kind,
  open,
  onChoose,
  onCancel,
}: {
  kind: ScopeKind;
  open: boolean;
  onChoose: (scope: Scope) => void;
  onCancel: () => void;
}) {
  return (
    <Dialog
      open={open}
      onOpenChange={(next) => !next && onCancel()}
      title={kind === 'edit' ? t('recurrence.editTitle') : t('recurrence.deleteTitle')}
      size="sm"
      footer={
        <>
          <Button onClick={onCancel}>{t('recurrence.cancel')}</Button>
          <Button onClick={() => onChoose('this')}>{t('recurrence.onlyThis')}</Button>
          <Button variant="primary" onClick={() => onChoose('following')} autoFocus>
            {t('recurrence.thisAndFollowing')}
          </Button>
        </>
      }
    >
      <p className="text-text">
        {kind === 'edit' ? t('recurrence.editMessage') : t('recurrence.deleteMessage')}
      </p>
    </Dialog>
  );
}

export function ScopeProvider({ children }: { children: ReactNode }) {
  // Hàng đợi: nhiều lệnh lưu cùng bị 409 thì hỏi lần lượt, không huỷ lệnh trước.
  const [queue, setQueue] = useState<{ kind: ScopeKind; resolve: (scope: Scope | null) => void }[]>(
    [],
  );

  const ask = useCallback<Ask>(
    (kind) =>
      new Promise<Scope | null>((resolve) => {
        setQueue((current) => [...current, { kind, resolve }]);
      }),
    [],
  );

  const finish = useCallback((scope: Scope | null) => {
    setQueue(([first, ...rest]) => {
      first?.resolve(scope);
      return rest;
    });
  }, []);

  const first = queue[0];
  return (
    <ScopeContext.Provider value={ask}>
      {children}
      <ScopeDialog
        kind={first?.kind ?? 'edit'}
        open={first !== undefined}
        onChoose={finish}
        onCancel={() => finish(null)}
      />
    </ScopeContext.Provider>
  );
}
