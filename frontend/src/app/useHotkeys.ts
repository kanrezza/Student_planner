import { useEffect, useRef } from 'react';

/**
 * Đăng ký phím tắt theo contracts/ui-shortcuts.md (⌘ = `metaKey`).
 * - Phím một ký tự (không có ⌘) bị bỏ qua khi đang gõ trong ô nhập.
 * - Phím có ⌘ và Esc luôn chạy.
 * - Sự kiện đã được xử lý (`defaultPrevented`, ví dụ Esc đóng hộp thoại Radix) thì bỏ qua.
 */
export type Hotkey = {
  /** Giá trị `KeyboardEvent.key`: 'n', '1', ',', '/', 'Enter', 'Escape', 'Backspace', 'ArrowUp'… */
  key: string;
  meta?: boolean;
  /** Trả `false` để không chặn hành vi mặc định của trình duyệt. */
  handler: (event: KeyboardEvent) => void | false;
  enabled?: boolean;
};

export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return (
    tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable === true
  );
}

function matches(binding: Hotkey, event: KeyboardEvent): boolean {
  if (Boolean(binding.meta) !== event.metaKey) return false;
  if (event.ctrlKey || event.altKey) return false;
  return binding.key.length === 1
    ? binding.key.toLowerCase() === event.key.toLowerCase()
    : binding.key === event.key;
}

export function useHotkeys(bindings: Hotkey[]): void {
  const latest = useRef(bindings);
  latest.current = bindings;

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.defaultPrevented || event.isComposing) return;
      const typing = isTypingTarget(event.target);
      for (const binding of latest.current) {
        if (binding.enabled === false || !matches(binding, event)) continue;
        if (typing && !binding.meta && binding.key !== 'Escape') continue;
        const result = binding.handler(event);
        if (result !== false) event.preventDefault();
        return;
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);
}
