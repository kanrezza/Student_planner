/**
 * Trạng thái giao diện lưu trong `localStorage` (data-model "Trạng thái giao diện"): chế độ lịch,
 * cột bên của Lịch, nhóm đã thu gọn. Mọi lần đọc/ghi bọc try/catch (chế độ riêng tư, bị chặn…).
 */
import { useCallback, useState } from 'react';

const PREFIX = 'lichhoc.';

export function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(PREFIX + key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

export function writeStored<T>(key: string, value: T): void {
  try {
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    // Không lưu được thì thôi — chỉ là tiện ích giao diện.
  }
}

export function useStoredState<T>(key: string, fallback: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => readStored(key, fallback));
  const [currentKey, setCurrentKey] = useState(key);
  if (currentKey !== key) {
    // Đổi khoá (ví dụ sang view khác) → đọc lại giá trị của khoá mới.
    setCurrentKey(key);
    setValue(readStored(key, fallback));
  }
  const update = useCallback(
    (next: T) => {
      setValue(next);
      writeStored(key, next);
    },
    [key],
  );
  return [value, update];
}
