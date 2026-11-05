import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { BackupJob, BackupStatus } from '../src/api/backup';
import { RESTORING_EVENT } from '../src/api/client';
import { BackupSettings } from '../src/features/settings/BackupSettings';
import { RestoreOverlay } from '../src/features/settings/RestoreOverlay';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';

const FILE = {
  name: 'LichHoc-2026-11-04-2100-tu-dong.lhbackup',
  path: '/Sao lưu/LichHoc-2026-11-04-2100-tu-dong.lhbackup',
  kind: 'tu-dong' as const,
  created_at: '2026-11-04T21:00:00+07:00',
  size: 2516582,
  location: 'local' as const,
};

const restoreJob = (over: Partial<BackupJob> = {}): BackupJob => ({
  id: 9,
  kind: 'restore',
  source_path: FILE.path,
  state: 'running',
  step: 'restoring',
  message: null,
  created_at: '2026-11-06T09:00:00+07:00',
  finished_at: null,
  ...over,
});

function status(job: BackupJob | null = null): BackupStatus {
  return {
    config: {
      enabled: true,
      schedule_time: '21:00',
      destination_path: null,
      destination_display: 'iCloud Drive › Lịch Học Cá Nhân › Sao lưu',
      retention_count: 14,
    },
    agent_online: true,
    destination: { state: 'ok', message: null, path: '/Sao lưu' },
    last_attempt: { at: null, ok: null, size: null, error: null },
    last_success: null,
    stale: false,
    files: [FILE],
    job,
  };
}

function renderApp(initial: BackupStatus, routes: Record<string, unknown> = {}) {
  const api = mockApi({ 'GET /backup/status': initial, ...routes });
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <BackupSettings />
        <RestoreOverlay />
      </ToastProvider>
    </QueryClientProvider>,
  );
  return { api, qc };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Khôi phục (US2)', () => {
  it('bấm "Khôi phục" mở hộp xác nhận đúng nội dung; Huỷ không tạo việc', async () => {
    const { api } = renderApp(status());
    fireEvent.click(await screen.findByRole('button', { name: 'Khôi phục' }));
    expect(
      screen.getByText(
        'Khôi phục dữ liệu về lúc 21:00 Thứ Tư, 04/11/2026? Dữ liệu hiện tại sẽ được sao lưu trước rồi bị thay thế.',
      ),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Huỷ' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(api.calls('POST', '/backup/jobs')).toHaveLength(0);
  });

  it('xác nhận tạo việc restore với source_path', async () => {
    const { api } = renderApp(status());
    fireEvent.click(await screen.findByRole('button', { name: 'Khôi phục' }));
    const confirm = screen.getAllByRole('button', { name: 'Khôi phục' }).at(-1)!;
    fireEvent.click(confirm);
    await waitFor(() => expect(api.calls('POST', '/backup/jobs')).toHaveLength(1));
    const body = JSON.parse(api.calls('POST', '/backup/jobs')[0][1]?.body as string);
    expect(body).toEqual({ kind: 'restore', source_path: FILE.path });
  });

  it('việc khôi phục đang chạy hiện lớp phủ kèm bước hiện tại', async () => {
    renderApp(status(restoreJob({ step: 'pre_backup' })));
    const overlay = await screen.findByRole('alertdialog');
    expect(overlay.textContent).toContain('Đang sao lưu dữ liệu hiện tại…');
  });

  it('API trả 503 "restoring" cũng hiện lớp phủ rồi tự gỡ khi hết khôi phục', async () => {
    const { qc } = renderApp(status());
    await screen.findByRole('button', { name: 'Sao lưu ngay' });
    // Lúc bị chặn, trạng thái vẫn báo việc khôi phục đang chạy.
    mockApi({ 'GET /backup/status': status(restoreJob()) });
    act(() => {
      window.dispatchEvent(new Event(RESTORING_EVENT));
    });
    await screen.findByRole('alertdialog');
    // Khôi phục xong, không còn việc nào đang chạy.
    mockApi({ 'GET /backup/status': status(restoreJob({ state: 'done' })) });
    await act(async () => {
      await qc.invalidateQueries();
    });
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
  });

  it('khôi phục xong: thông báo kết quả và làm mới toàn bộ dữ liệu', async () => {
    let current = status(restoreJob());
    const { qc } = renderApp(current);
    vi.spyOn(qc, 'invalidateQueries');
    await screen.findByRole('alertdialog');
    current = status(
      restoreJob({ state: 'done', message: 'Đã khôi phục dữ liệu về 21:00 04/11/2026' }),
    );
    mockApi({ 'GET /backup/status': current });
    await act(async () => {
      await qc.invalidateQueries();
    });
    await waitFor(() =>
      expect(screen.getByText('Đã khôi phục dữ liệu về 21:00 04/11/2026')).toBeTruthy(),
    );
    expect(screen.queryByRole('alertdialog')).toBeNull();
  });
});
