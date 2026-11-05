import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { BackupStatus } from '../src/api/backup';
import { BackupSettings } from '../src/features/settings/BackupSettings';
import { IconRail } from '../src/app/IconRail';
import { ShellProvider } from '../src/app/shell';
import { formatSize } from '../src/lib/format';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';

const FILE = {
  name: 'LichHoc-2026-11-05-2100-tu-dong.lhbackup',
  path: '/Users/x/Sao lưu/LichHoc-2026-11-05-2100-tu-dong.lhbackup',
  kind: 'tu-dong' as const,
  created_at: '2026-11-05T21:00:00+07:00',
  size: 2516582,
  location: 'local' as const,
};

function makeStatus(overrides: Partial<BackupStatus> = {}): BackupStatus {
  return {
    config: {
      enabled: true,
      schedule_time: '21:00',
      destination_path: null,
      destination_display: 'iCloud Drive › Lịch Học Cá Nhân › Sao lưu',
      retention_count: 14,
    },
    agent_online: true,
    destination: { state: 'ok', message: null, path: '/Users/x/Sao lưu' },
    last_attempt: { at: '2026-11-05T21:00:12+07:00', ok: true, size: 2516582, error: null },
    last_success: { at: '2026-11-05T21:00:12+07:00', size: 2516582 },
    stale: false,
    files: [FILE],
    job: null,
    ...overrides,
  };
}

function renderSettings(status: BackupStatus) {
  const api = mockApi({ 'GET /backup/status': status });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <BackupSettings />
      </ToastProvider>
    </QueryClientProvider>,
  );
  return api;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Cài đặt → Sao lưu (US1)', () => {
  it('định dạng dung lượng kiểu Việt Nam', () => {
    expect(formatSize(2516582)).toBe('2,4 MB');
    expect(formatSize(512)).toBe('512 B');
    expect(formatSize(1536)).toBe('1,5 KB');
  });

  it('hiện lần sao lưu gần nhất: giờ, dung lượng, thành công', async () => {
    renderSettings(makeStatus());
    expect((await screen.findByTestId('backup-last')).textContent).toBe(
      'Lần gần nhất: 21:00 Thứ Năm, 05/11/2026 — 2,4 MB — Thành công',
    );
    expect(screen.getByTestId('backup-folder').textContent).toBe(
      'iCloud Drive › Lịch Học Cá Nhân › Sao lưu',
    );
    expect(screen.getByText('Tự động')).toBeTruthy();
  });

  it('lần gần nhất thất bại: hiện lý do và vẫn hiện lần thành công gần nhất', async () => {
    renderSettings(
      makeStatus({
        last_attempt: {
          at: '2026-11-06T21:00:00+07:00',
          ok: false,
          size: null,
          error: 'Ổ đĩa đầy',
        },
      }),
    );
    expect(await screen.findByText(/Lần gần nhất thất bại: Ổ đĩa đầy/)).toBeTruthy();
    expect(
      screen.getByText(/Lần thành công gần nhất: 21:00 Thứ Năm, 05\/11\/2026 — 2,4 MB/),
    ).toBeTruthy();
  });

  it('thư mục không có: cảnh báo nhẹ trong trang, không phải hộp thoại chặn', async () => {
    renderSettings(
      makeStatus({
        destination: {
          state: 'missing',
          message: 'Không tìm thấy thư mục sao lưu (ổ đĩa có thể đã được tháo).',
          path: null,
        },
      }),
    );
    expect(await screen.findByText(/Không tìm thấy thư mục sao lưu/)).toBeTruthy();
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('đang có việc sao lưu: nút "Sao lưu ngay" bị vô hiệu và hiện "Đang sao lưu…"', async () => {
    renderSettings(
      makeStatus({
        job: {
          id: 3,
          kind: 'backup_now',
          source_path: null,
          state: 'running',
          step: 'backup',
          message: null,
          created_at: '2026-11-05T21:00:00+07:00',
          finished_at: null,
        },
      }),
    );
    const button = await screen.findByRole('button', { name: 'Đang sao lưu…' });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });

  it('agent chưa chạy: cảnh báo và không cho bấm "Sao lưu ngay"', async () => {
    renderSettings(makeStatus({ agent_online: false }));
    expect(await screen.findByText(/chưa sao lưu được/)).toBeTruthy();
    expect(
      (screen.getByRole('button', { name: 'Sao lưu ngay' }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });

  it('ngoài app macOS: có ô nhập đường dẫn thay cho nút chọn thư mục', async () => {
    renderSettings(makeStatus());
    await screen.findByTestId('backup-last');
    expect(screen.queryByRole('button', { name: 'Chọn thư mục…' })).toBeNull();
    expect(screen.getByLabelText(/Đường dẫn thư mục/)).toBeTruthy();
  });

  it('bấm "Sao lưu ngay" tạo việc backup_now', async () => {
    const api = renderSettings(makeStatus());
    const button = await screen.findByRole('button', { name: 'Sao lưu ngay' });
    button.click();
    await waitFor(() => expect(api.calls('POST', '/backup/jobs')).toHaveLength(1));
    const body = JSON.parse(api.calls('POST', '/backup/jobs')[0][1]?.body as string);
    expect(body).toEqual({ kind: 'backup_now' });
  });
});

describe('Chấm cảnh báo trên biểu tượng Cài đặt', () => {
  function renderRail(status: BackupStatus) {
    mockApi({ 'GET /backup/status': status });
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <ShellProvider>
            <IconRail />
          </ShellProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );
  }

  it('hiện khi quá 3 ngày chưa sao lưu hoặc thư mục có vấn đề', async () => {
    renderRail(makeStatus({ stale: true }));
    expect(await screen.findByRole('img', { name: 'Sao lưu cần chú ý' })).toBeTruthy();
  });

  it('không hiện khi mọi thứ bình thường', async () => {
    renderRail(makeStatus());
    await waitFor(() => expect(screen.getByRole('link', { name: 'Cài đặt' })).toBeTruthy());
    await new Promise((r) => setTimeout(r, 30));
    expect(screen.queryByRole('img', { name: 'Sao lưu cần chú ý' })).toBeNull();
  });
});
