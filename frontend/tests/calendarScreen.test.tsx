import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CalendarScreen } from '../src/features/calendar/CalendarScreen';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';

let location = '';
function LocationProbe() {
  const loc = useLocation();
  location = loc.pathname + loc.search;
  return null;
}

function renderAt(path: string) {
  mockApi({
    'GET /calendar': { sessions: [], tasks: [] },
    'GET /lists': [
      {
        id: 1,
        name: 'Học tập',
        color: 'c01',
        is_default_study: true,
        open_task_count: 0,
        emoji: null,
      },
    ],
  });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter initialEntries={[path]}>
          <LocationProbe />
          <Routes>
            <Route path="/lich" element={<CalendarScreen />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

const press = (key: string) => act(() => void fireEvent.keyDown(window, { key }));
const param = (name: string) => new URLSearchParams(location.split('?')[1]).get(name);

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe('CalendarScreen — đầu trang và phím tắt (T065, T069)', () => {
  it('tiêu đề theo tuần đang xem; → sang tuần vắt hai tháng; ← quay lại', () => {
    renderAt('/lich?che-do=tuan&ngay=2026-11-25');
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Tháng 11, 2026');
    press('ArrowRight');
    expect(param('ngay')).toBe('2026-12-02');
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Tháng 11 – Tháng 12, 2026');
    press('ArrowLeft');
    expect(param('ngay')).toBe('2026-11-25');
  });

  it('D/W/M đổi chế độ và nhớ chế độ gần nhất', () => {
    renderAt('/lich?ngay=2026-11-25');
    press('m');
    expect(param('che-do')).toBe('thang');
    expect(screen.getByRole('button', { name: 'Chế độ xem' }).textContent).toContain('Tháng');
    expect(window.localStorage.getItem('lichhoc.calendar.mode')).toBe('"thang"');
    press('d');
    expect(param('che-do')).toBe('ngay');
  });

  it('nút "+" mở chế độ tạo mới với ngày đang chọn', async () => {
    renderAt('/lich?che-do=tuan&ngay=2026-11-25');
    fireEvent.click(screen.getByRole('button', { name: 'Thêm công việc vào ngày đang chọn' }));
    expect(param('task')).toBe('new');
    expect(param('due')).toBe('2026-11-25');
    expect(await screen.findByText('Thứ Tư, 25/11')).toBeTruthy();
  });

  it('ẩn/hiện cột bên và nhớ trong localStorage', () => {
    renderAt('/lich?che-do=tuan&ngay=2026-11-25');
    expect(screen.getByRole('complementary', { name: 'Lịch tháng và bộ lọc' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Ẩn cột bên' }));
    expect(screen.queryByRole('complementary', { name: 'Lịch tháng và bộ lọc' })).toBeNull();
    expect(window.localStorage.getItem('lichhoc.calendar.sidebar')).toBe('false');
  });

  it('bấm ngày trong lịch tháng nhỏ → lịch chuyển tới ngày đó', () => {
    renderAt('/lich?che-do=tuan&ngay=2026-11-25');
    fireEvent.click(screen.getByRole('button', { name: 'Thứ Tư, 02/12/2026' }));
    expect(param('ngay')).toBe('2026-12-02');
  });
});
