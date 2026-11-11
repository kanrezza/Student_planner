import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CanonicalNamesSettings } from '../src/features/settings/CanonicalNamesSettings';
import { mockApi } from './apiMock';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const NAMES = [
  { id: 1, name: 'Bóng đá', course_code: 'FFS701069', created_at: '2026-11-11T10:00:00+07:00' },
  {
    id: 2,
    name: 'Giao diện người máy',
    course_code: null,
    created_at: '2026-11-11T10:00:00+07:00',
  },
];

function renderIt(names: unknown) {
  const api = mockApi({ 'GET /canonical-names': names, 'DELETE /canonical-names': null });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <CanonicalNamesSettings />
    </QueryClientProvider>,
  );
  return api;
}

describe('CanonicalNamesSettings', () => {
  it('hiện tên, mã HP, ngày thêm và ghi chú', async () => {
    renderIt(NAMES);
    expect(await screen.findByText('Bóng đá')).toBeTruthy();
    expect(screen.getByText('FFS701069')).toBeTruthy();
    expect(screen.getAllByText('11/11/2026')).toHaveLength(2);
    expect(screen.getByText('Dùng để tự sửa tên môn khi nhập lịch từ ảnh.')).toBeTruthy();
  });

  it('Xoá danh sách hỏi xác nhận rồi gọi DELETE', async () => {
    const api = renderIt(NAMES);
    await screen.findByText('Bóng đá'); // chờ dữ liệu về (nút bị tắt khi danh sách rỗng)
    fireEvent.click(screen.getByRole('button', { name: 'Xoá danh sách' }));
    expect(api.calls('DELETE', '/canonical-names')).toHaveLength(0);
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Xoá danh sách' }));
    await waitFor(() => expect(api.calls('DELETE', '/canonical-names')).toHaveLength(1));
  });

  it('danh sách rỗng: nút xoá tắt', async () => {
    renderIt([]);
    expect(await screen.findByText(/Chưa có tên nào/)).toBeTruthy();
    expect(
      (screen.getByRole('button', { name: 'Xoá danh sách' }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });
});
