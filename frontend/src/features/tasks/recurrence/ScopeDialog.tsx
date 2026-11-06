import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
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
  const [kind, setKind] = useState<ScopeKind | null>(null);
  const resolver = useRef<((scope: Scope | null) => void) | null>(null);

  const ask = useCallback<Ask>((next) => {
    resolver.current?.(null);
    setKind(next);
    return new Promise<Scope | null>((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  const finish = useCallback((scope: Scope | null) => {
    resolver.current?.(scope);
    resolver.current = null;
    setKind(null);
  }, []);

  const value = useMemo(() => ask, [ask]);
  return (
    <ScopeContext.Provider value={value}>
      {children}
      <ScopeDialog
        kind={kind ?? 'edit'}
        open={kind !== null}
        onChoose={finish}
        onCancel={() => finish(null)}
      />
    </ScopeContext.Provider>
  );
}
