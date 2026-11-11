import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AttachmentsSettings, ownerPath } from '../src/features/settings/AttachmentsSettings';
import { SETTINGS_SECTIONS } from '../src/features/settings/SettingsScreen';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const big = (id: number, name: string, size: number, type: string, ownerId: number) => ({
  id,
  display_name: name,
  size,
  mime_type: 'application/pdf',
  preview: 'pdf',
  is_executable: false,
  created_at: '2026-11-11T20:15:00+07:00',
  owner: { type, id: ownerId, title: `Nơi ${ownerId}` },
  content_url: '',
  download_url: '',
});

const STATS = {
  total_bytes: 1288490189,
  blob_count: 3,
  attachment_count: 86,
  largest: [big(1, 'bai-giang.pdf', 52428800, 'subject', 7), big(2, 'de.pdf', 1048576, 'exam', 9)],
  max_file_mb: 50,
  backup_warn_mb: 1024,
};

function Where() {
  const l = useLocation();
  return <output data-testid="where">{l.pathname + l.search}</output>;
}

function setup(routes: Record<string, unknown> = {}) {
  const api = mockApi({
    'GET /attachments/stats': STATS,
    'GET /settings': { attachment_max_mb: 50, backup_attachments_warn_mb: 1024 },
    'PATCH /settings': { attachment_max_mb: 10 },
    ...routes,
  });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          <AttachmentsSettings />
          <Where />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  return api;
}

describe('AttachmentsSettings', () => {
  it('có trong danh sách mục cài đặt', () => {
    expect(SETTINGS_SECTIONS.some((s) => s.slug === 'file-dinh-kem')).toBe(true);
  });

  it('hiện tổng dung lượng, số file và 10 file lớn nhất', async () => {
    setup();
    expect((await screen.findByTestId('attachment-total')).textContent).toBe(
      'Tổng dung lượng: 1,2 GB · 86 file',
    );
    expect(screen.getByText('bai-giang.pdf')).toBeTruthy();
    expect(screen.getByText('50,0 MB')).toBeTruthy();
    expect(screen.getByText('Môn: Nơi 7')).toBeTruthy();
  });

  it('bấm một dòng mở nơi gắn file', async () => {
    setup();
    fireEvent.click(await screen.findByRole('button', { name: 'de.pdf' }));
    expect(screen.getByTestId('where').textContent).toBe('/lich-thi?thi=9&attachment=2');
    expect(ownerPath(STATS.largest[0] as never)).toBe('/mon-hoc?mon=7&attachment=1');
  });

  it('sửa giới hạn gọi PATCH /settings', async () => {
    const api = setup();
    const input = await screen.findByLabelText('Giới hạn mỗi file');
    fireEvent.change(input, { target: { value: '10' } });
    fireEvent.blur(input);
    await waitFor(() => expect(api.calls('PATCH', '/settings')).toHaveLength(1));
    expect(JSON.parse(String(api.calls('PATCH', '/settings')[0][1]?.body))).toEqual({
      attachment_max_mb: 10,
    });
  });

  it('lỗi ngoài khoảng hiện dưới ô', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string, init?: RequestInit) => {
        if (init?.method === 'PATCH')
          return new Response(
            JSON.stringify({
              error: {
                code: 'validation_error',
                message: 'Dữ liệu chưa hợp lệ',
                fields: { attachment_max_mb: 'Phải từ 1 đến 500' },
              },
            }),
            { status: 400, headers: { 'Content-Type': 'application/json' } },
          );
        const body = String(url).includes('stats')
          ? STATS
          : { attachment_max_mb: 50, backup_attachments_warn_mb: 1024 };
        return new Response(JSON.stringify(body), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }),
    );
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <AttachmentsSettings />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    const input = await screen.findByLabelText('Giới hạn mỗi file');
    fireEvent.change(input, { target: { value: '900' } });
    fireEvent.blur(input);
    expect((await screen.findByRole('alert')).textContent).toBe('Phải từ 1 đến 500');
  });
});
