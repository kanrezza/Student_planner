import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { t } from '../i18n/vi';
import { cx } from './cx';
import { IconClose } from './icons';

/** Thông báo nhỏ ở cuối màn hình, tự ẩn sau 5 giây, có thể kèm nút "Hoàn tác" (FR-029, FR-030). */
export const TOAST_DURATION_MS = 5000;

export type ToastAction = { label: string; onClick: () => void };
export type ToastOptions = { action?: ToastAction; tone?: 'neutral' | 'warning' | 'danger' };
type ToastItem = ToastOptions & { id: number; message: string };

type ToastApi = {
  show: (message: string, options?: ToastOptions) => number;
  dismiss: (id: number) => void;
};

const ToastContext = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => {
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const show = useCallback((message: string, options: ToastOptions = {}) => {
    const id = nextId.current++;
    // Tối đa 3 thông báo cùng lúc; cái cũ nhất bị thay.
    setItems((current) => [...current.slice(-2), { id, message, ...options }]);
    return id;
  }, []);

  const api = useMemo(() => ({ show, dismiss }), [show, dismiss]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-5 z-[60] flex flex-col items-center gap-2 px-4"
        aria-live="polite"
      >
        {items.map((item) => (
          <ToastView key={item.id} item={item} onDismiss={() => dismiss(item.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastView({ item, onDismiss }: { item: ToastItem; onDismiss: () => void }) {
  useEffect(() => {
    const timer = window.setTimeout(onDismiss, TOAST_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      role="status"
      className={cx(
        'pointer-events-auto flex max-w-[560px] items-center gap-3 rounded-lg px-3.5 py-2 shadow-pop',
        'bg-text text-bg',
      )}
    >
      {item.tone === 'warning' && <span aria-hidden>⚠️</span>}
      {item.tone === 'danger' && <span aria-hidden>⛔</span>}
      <span className="min-w-0 flex-1">{item.message}</span>
      {item.action && (
        <button
          type="button"
          className="rounded-md px-2 py-0.5 font-semibold text-bg underline-offset-2 hover:underline"
          onClick={() => {
            item.action?.onClick();
            onDismiss();
          }}
        >
          {item.action.label}
        </button>
      )}
      <button
        type="button"
        aria-label={t('common.close')}
        className="rounded p-0.5 opacity-70 hover:opacity-100"
        onClick={onDismiss}
      >
        <IconClose size={14} />
      </button>
    </div>
  );
}

const NOOP_API: ToastApi = { show: () => 0, dismiss: () => {} };

/** Dùng ngoài `ToastProvider` (ví dụ trong test đơn lẻ) thì không làm gì. */
export function useToast(): ToastApi {
  return useContext(ToastContext) ?? NOOP_API;
}
