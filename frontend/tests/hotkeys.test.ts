import { cleanup, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useHotkeys, type Hotkey } from '../src/app/useHotkeys';

afterEach(() => {
  cleanup();
  document.body.innerHTML = '';
});

function press(key: string, init: KeyboardEventInit = {}, target: EventTarget = document.body) {
  const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true, ...init });
  target.dispatchEvent(event);
  return event;
}

function setup(bindings: Hotkey[]) {
  return renderHook(() => useHotkeys(bindings));
}

describe('useHotkeys', () => {
  it('chạy phím một ký tự và phím có ⌘', () => {
    const onT = vi.fn();
    const onNew = vi.fn();
    setup([
      { key: 't', handler: onT },
      { key: 'n', meta: true, handler: onNew },
    ]);
    const event = press('T');
    expect(onT).toHaveBeenCalledTimes(1);
    expect(event.defaultPrevented).toBe(true);
    press('n', { metaKey: true });
    expect(onNew).toHaveBeenCalledTimes(1);
    press('n'); // thiếu ⌘
    expect(onNew).toHaveBeenCalledTimes(1);
  });

  it('bỏ qua phím một ký tự khi đang gõ, ⌘N và Esc vẫn chạy', () => {
    const onT = vi.fn();
    const onNew = vi.fn();
    const onEsc = vi.fn();
    setup([
      { key: 't', handler: onT },
      { key: 'ArrowDown', handler: onT },
      { key: 'n', meta: true, handler: onNew },
      { key: 'Escape', handler: onEsc },
    ]);
    const input = document.createElement('input');
    const area = document.createElement('textarea');
    document.body.append(input, area);
    press('t', {}, input);
    press('ArrowDown', {}, area);
    expect(onT).not.toHaveBeenCalled();
    press('n', { metaKey: true }, input);
    press('Escape', {}, input);
    expect(onNew).toHaveBeenCalledTimes(1);
    expect(onEsc).toHaveBeenCalledTimes(1);
  });

  it('bỏ qua sự kiện đã được xử lý và phím bị tắt', () => {
    const onEsc = vi.fn();
    const onD = vi.fn();
    setup([
      { key: 'Escape', handler: onEsc },
      { key: 'd', handler: onD, enabled: false },
    ]);
    const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true });
    event.preventDefault();
    window.dispatchEvent(event);
    press('d');
    expect(onEsc).not.toHaveBeenCalled();
    expect(onD).not.toHaveBeenCalled();
  });

  it('gỡ đăng ký khi unmount', () => {
    const onT = vi.fn();
    const { unmount } = setup([{ key: 't', handler: onT }]);
    unmount();
    press('t');
    expect(onT).not.toHaveBeenCalled();
  });
});
