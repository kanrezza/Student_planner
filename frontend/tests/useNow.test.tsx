import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NowProvider, msUntilNextDay, useNow } from '../src/app/useNow';

function ShowToday() {
  return <span data-testid="today">{useNow().today}</span>;
}

function setup() {
  const qc = new QueryClient();
  const invalidate = vi.spyOn(qc, 'invalidateQueries').mockResolvedValue();
  const view = render(
    <QueryClientProvider client={qc}>
      <NowProvider>
        <ShowToday />
      </NowProvider>
    </QueryClientProvider>,
  );
  const refreshedKeys = () => invalidate.mock.calls.map(([arg]) => arg?.queryKey?.join('/'));
  return { invalidate, refreshedKeys, ...view };
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe('useNow', () => {
  it('sang ngày mới lúc 00:00 thì đổi `today` và làm mới dữ liệu đúng một lần', () => {
    vi.setSystemTime(new Date('2026-11-09T23:59:30+07:00'));
    const { refreshedKeys } = setup();
    expect(screen.getByTestId('today').textContent).toBe('2026-11-09');

    act(() => {
      vi.advanceTimersByTime(31_000);
    });
    expect(screen.getByTestId('today').textContent).toBe('2026-11-10');
    expect(refreshedKeys()).toEqual(['tasks', 'today', 'calendar']);

    act(() => {
      vi.advanceTimersByTime(5 * 60_000); // các lần tick mỗi phút sau đó không làm mới thêm
    });
    expect(refreshedKeys()).toEqual(['tasks', 'today', 'calendar']);
  });

  it('focus lại cửa sổ sau khi máy ngủ qua nửa đêm thì cập nhật ngay', () => {
    vi.setSystemTime(new Date('2026-11-09T22:00:00+07:00'));
    const { refreshedKeys } = setup();

    act(() => {
      window.dispatchEvent(new Event('focus')); // cùng ngày → không làm mới
    });
    expect(refreshedKeys()).toEqual([]);

    vi.setSystemTime(new Date('2026-11-10T07:15:00+07:00')); // máy ngủ, timer chưa kịp chạy
    act(() => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(screen.getByTestId('today').textContent).toBe('2026-11-10');
    expect(refreshedKeys()).toEqual(['tasks', 'today', 'calendar']);
  });

  it('gỡ timer và listener khi unmount', () => {
    vi.setSystemTime(new Date('2026-11-09T23:59:30+07:00'));
    const { refreshedKeys, unmount } = setup();
    unmount();
    act(() => {
      vi.advanceTimersByTime(120_000);
      window.dispatchEvent(new Event('focus'));
    });
    expect(refreshedKeys()).toEqual([]);
    expect(vi.getTimerCount()).toBe(0);
  });

  it('msUntilNextDay tính tới 00:00 giờ Việt Nam', () => {
    expect(msUntilNextDay(new Date('2026-11-09T23:59:00+07:00'))).toBe(60_000 + 50);
    expect(msUntilNextDay(new Date('2026-11-09T16:59:00Z'))).toBe(60_000 + 50); // 23:59 VN
  });
});
