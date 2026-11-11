import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PeriodsTable } from '../src/features/settings/PeriodsTable';
import { mockApi } from './apiMock';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const PERIODS = [
  { number: 1, start_time: '06:45', end_time: '07:35', is_manual: false, shift_id: 1 },
  { number: 2, start_time: '07:31', end_time: '08:21', is_manual: true, shift_id: 1 },
  { number: 16, start_time: '21:05', end_time: '21:20', is_manual: false, shift_id: null },
];
const SHIFTS = [{ id: 1, name: 'Ca 1', start_time: '06:45', end_time: '09:25', position: 1 }];

function renderTable(extra: Record<string, unknown> = {}) {
  const api = mockApi({
    'GET /periods': PERIODS,
    'GET /shifts': SHIFTS,
    'PUT /periods/2': { ...PERIODS[1], start_time: '07:40' },
    'POST /periods/2/reset': PERIODS[1],
    ...extra,
  });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <PeriodsTable />
    </QueryClientProvider>,
  );
  return api;
}

describe('PeriodsTable', () => {
  it('hiện các tiết, dấu "đã chỉnh" và ca của tiết', async () => {
    renderTable();
    expect(await screen.findByLabelText('Giờ bắt đầu 1')).toBeTruthy();
    expect(screen.getByText('đã chỉnh')).toBeTruthy();
    expect(screen.getAllByText('Ca 1').length).toBeGreaterThan(0);
    expect(screen.getByText('Dùng để đổi tiết trong file PDF sang giờ.')).toBeTruthy();
  });

  it('sửa giờ gọi PUT /periods/{số}', async () => {
    const api = renderTable();
    const start = await screen.findByLabelText('Giờ bắt đầu 1');
    fireEvent.change(start, { target: { value: '06:50' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Lưu' })[0]);
    await waitFor(() => expect(api.calls('PUT', '/periods/1')).toHaveLength(1));
    expect(JSON.parse(String(api.calls('PUT', '/periods/1')[0][1]?.body))).toEqual({
      start_time: '06:50',
      end_time: '07:35',
    });
  });

  it('"Về mặc định" gọi reset', async () => {
    const api = renderTable();
    fireEvent.click(await screen.findByRole('button', { name: 'Về mặc định 2' }));
    await waitFor(() => expect(api.calls('POST', '/periods/2/reset')).toHaveLength(1));
  });

  it('giờ kết thúc trước giờ bắt đầu: hiện lỗi của máy chủ', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string, init?: RequestInit) => {
        if (init?.method === 'PUT')
          return new Response(
            JSON.stringify({
              error: {
                code: 'validation_error',
                message: 'Dữ liệu chưa hợp lệ',
                fields: { end_time: 'Giờ kết thúc phải sau giờ bắt đầu' },
              },
            }),
            { status: 400, headers: { 'Content-Type': 'application/json' } },
          );
        const body = url.includes('shifts') ? SHIFTS : PERIODS;
        return new Response(JSON.stringify(body), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }),
    );
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <PeriodsTable />
      </QueryClientProvider>,
    );
    const end = await screen.findByLabelText('Giờ kết thúc 1');
    fireEvent.change(end, { target: { value: '06:00' } });
    fireEvent.click(screen.getAllByRole('button', { name: 'Lưu' })[0]);
    expect(await screen.findByText('Giờ kết thúc phải sau giờ bắt đầu')).toBeTruthy();
  });
});
