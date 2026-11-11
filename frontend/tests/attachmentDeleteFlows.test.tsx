import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ExamsScreen } from '../src/features/exams/ExamsScreen';
import { BackupSettings } from '../src/features/settings/BackupSettings';
import { SemestersSettings } from '../src/features/settings/SemestersSettings';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeExam } from './fixtures';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

const clickConfirm = (name = 'Xoá') => {
  const dialog = screen.getByRole('dialog');
  fireEvent.click(
    Array.from(dialog.querySelectorAll('button')).find((b) => b.textContent === name)!,
  );
};

describe('Xoá buổi thi có file đính kèm', () => {
  it('lần đầu 409 confirm_required nên hỏi lại kèm số file, rồi xoá với confirm=true', async () => {
    const exam = makeExam({ id: 4, course_name: 'Cơ sở dữ liệu' });
    let first = true;
    const api = mockApi({
      'GET /exams': { exams: [exam] },
      'DELETE /exams/4': () => null,
    });
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string, init?: RequestInit) => {
        if (init?.method === 'DELETE' && first) {
          first = false;
          return new Response(
            JSON.stringify({
              error: {
                code: 'confirm_required',
                message: 'Xoá buổi thi sẽ xoá 2 file đính kèm',
                details: { attachment_count: 2 },
              },
            }),
            { status: 409, headers: { 'Content-Type': 'application/json' } },
          );
        }
        return api.fetchMock(url, init);
      }),
    );
    wrap(<ExamsScreen />);
    fireEvent.click(await screen.findByRole('button', { name: /Xoá/ }));
    clickConfirm();
    expect(await screen.findByText(/có 2 file đính kèm/)).toBeTruthy();
    clickConfirm();
    await waitFor(() => expect(api.calls('DELETE', '/exams/4?confirm=true')).toHaveLength(1));
  });
});

describe('Xoá học kỳ có file đính kèm', () => {
  it('hộp xác nhận nêu số môn và số file', async () => {
    const semester = {
      id: 3,
      name: 'HK1',
      start_date: '2026-09-07',
      end_date: '2026-12-20',
      is_current: true,
    };
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url: string, init?: RequestInit) => {
        if (init?.method === 'DELETE')
          return new Response(
            JSON.stringify({
              error: {
                code: 'conflict',
                message: 'x',
                details: { subject_count: 2, attachment_count: 5 },
              },
            }),
            { status: 409, headers: { 'Content-Type': 'application/json' } },
          );
        return new Response(JSON.stringify([semester]), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }),
    );
    wrap(<SemestersSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /Xoá/ }));
    clickConfirm();
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText(/2 môn/)).toBeTruthy();
    expect(within(dialog).getByText(/5 file đính kèm/)).toBeTruthy();
  });
});

describe('Cài đặt → Sao lưu: cảnh báo file đính kèm lớn', () => {
  const status = (warning: boolean) => ({
    config: {
      enabled: true,
      schedule_time: '21:00',
      destination_path: null,
      destination_display: 'iCloud',
      retention_count: 14,
      enabled_since: '2026-11-01T00:00:00+07:00',
    },
    agent_online: true,
    destination: { state: 'ok', message: null, path: null },
    last_attempt: { at: null, ok: null, size: null, error: null },
    last_success: null,
    stale: false,
    files: [],
    job: null,
    attachments_bytes: 1288490189,
    estimated_backup_bytes: 1395864371,
    attachments_warning: warning,
  });

  it('hiện cảnh báo khi vượt ngưỡng', async () => {
    mockApi({ 'GET /backup/status': status(true) });
    wrap(<BackupSettings />);
    expect(
      await screen.findByText(/File đính kèm đang chiếm 1,2 GB; mỗi bản sao lưu khoảng 1,3 GB/),
    ).toBeTruthy();
  });

  it('không cảnh báo khi chưa vượt', async () => {
    mockApi({ 'GET /backup/status': status(false) });
    wrap(<BackupSettings />);
    await screen.findByText('Lần sao lưu gần nhất');
    expect(screen.queryByText(/File đính kèm đang chiếm/)).toBeNull();
  });
});
