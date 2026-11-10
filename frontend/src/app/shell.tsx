/**
 * Trạng thái dùng chung của khung app: bảng phím tắt, ô "Thêm công việc" (⌘N, T042).
 */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

type ShellValue = {
  shortcutsOpen: boolean;
  setShortcutsOpen: (open: boolean) => void;
  /** Ô thêm nhanh đăng ký hàm focus của nó; trả hàm gỡ đăng ký. */
  registerQuickAdd: (focus: () => void) => () => void;
  /** Đặt con trỏ vào ô "Thêm công việc"; trả false nếu ô chưa có trên màn hình. */
  focusQuickAdd: () => boolean;
  /** Ô tìm kiếm ở cột danh sách đăng ký hàm focus của nó (⌘F). */
  registerSearch: (focus: () => void) => () => void;
  focusSearch: () => boolean;
};

const ShellContext = createContext<ShellValue | null>(null);

export function ShellProvider({ children }: { children: ReactNode }) {
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const quickAdd = useRef<(() => void) | null>(null);
  const search = useRef<(() => void) | null>(null);

  const registerQuickAdd = useCallback((focus: () => void) => {
    quickAdd.current = focus;
    return () => {
      if (quickAdd.current === focus) quickAdd.current = null;
    };
  }, []);

  const focusQuickAdd = useCallback(() => {
    if (!quickAdd.current) return false;
    quickAdd.current();
    return true;
  }, []);

  const registerSearch = useCallback((focus: () => void) => {
    search.current = focus;
    return () => {
      if (search.current === focus) search.current = null;
    };
  }, []);

  const focusSearch = useCallback(() => {
    if (!search.current) return false;
    search.current();
    return true;
  }, []);

  const value = useMemo(
    () => ({
      shortcutsOpen,
      setShortcutsOpen,
      registerQuickAdd,
      focusQuickAdd,
      registerSearch,
      focusSearch,
    }),
    [shortcutsOpen, registerQuickAdd, focusQuickAdd, registerSearch, focusSearch],
  );
  return <ShellContext.Provider value={value}>{children}</ShellContext.Provider>;
}

const FALLBACK: ShellValue = {
  shortcutsOpen: false,
  setShortcutsOpen: () => {},
  registerQuickAdd: () => () => {},
  focusQuickAdd: () => false,
  registerSearch: () => () => {},
  focusSearch: () => false,
};

export function useShell(): ShellValue {
  return useContext(ShellContext) ?? FALLBACK;
}
