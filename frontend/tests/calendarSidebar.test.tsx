import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CalendarSidebar } from '../src/features/calendar/CalendarSidebar';
import { mockApi } from './apiMock';

function renderSidebar(onSelectDate = vi.fn()) {
  mockApi({ 'GET /tags': [{ id: 1, name: 'Nhóm', color: 'c04', system_key: null }] });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/lich']}>
        <CalendarSidebar
          selected="2026-11-18"
          range={{ start: '2026-11-16', end: '2026-11-22' }}
          today="2026-11-18"
          onSelectDate={onSelectDate}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return onSelectDate;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('CalendarSidebar (T066)', () => {
  it('lịch tháng nhỏ: tiêu đề tháng, bắt đầu Thứ Hai, tô hôm nay', () => {
    renderSidebar();
    expect(screen.getByText('Tháng 11, 2026')).toBeTruthy();
    const headers = screen.getAllByRole('columnheader').map((th) => th.textContent);
    expect(headers).toEqual(['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']);
    const today = screen.getByRole('button', { name: 'Thứ Tư, 18/11/2026' });
    expect(today.getAttribute('aria-current')).toBe('date');
    expect(
      screen.getByRole('button', { name: 'Thứ Năm, 19/11/2026' }).getAttribute('aria-current'),
    ).toBeNull();
  });

  it('bấm một ngày gọi onSelectDate đúng ngày (kể cả ngày của tháng sau)', () => {
    const onSelect = renderSidebar();
    fireEvent.click(screen.getByRole('button', { name: 'Thứ Tư, 25/11/2026' }));
    expect(onSelect).toHaveBeenCalledWith('2026-11-25');
    fireEvent.click(screen.getByRole('button', { name: 'Thứ Tư, 02/12/2026' }));
    expect(onSelect).toHaveBeenLastCalledWith('2026-12-02');
  });

  it('nút tháng sau chuyển lịch nhỏ sang tháng 12', () => {
    renderSidebar();
    fireEvent.click(screen.getByRole('button', { name: 'Tháng sau' }));
    expect(screen.getByText('Tháng 12, 2026')).toBeTruthy();
  });

  it('có bộ lọc nhãn bên dưới', async () => {
    renderSidebar();
    expect(await screen.findByRole('button', { name: /Nhóm/ })).toBeTruthy();
  });
});
