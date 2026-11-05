import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ExamsScreen } from '../src/features/exams/ExamsScreen';
import { TodaySchedule } from '../src/features/tasks/TodaySchedule';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeExam } from './fixtures';

function wrap(children: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>{children}</MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Lịch thi (US11)', () => {
  it('danh sách theo ngày, nhãn "Trùng giờ", "Chưa có phòng"', async () => {
    mockApi({
      'GET /exams': {
        exams: [
          makeExam({
            id: 1,
            conflicts: [
              {
                kind: 'session',
                id: 5,
                title: 'Giải tích 1',
                start_at: '2026-11-20T07:00:00+07:00',
              },
            ],
          }),
          makeExam({
            id: 2,
            course_name: 'Vật lý',
            date: '2026-11-22',
            attempt: 2,
            room: 'B1-101',
          }),
        ],
      },
      'GET /tags': [],
    });
    wrap(<ExamsScreen />);
    await screen.findByText('Cơ sở dữ liệu');
    expect(screen.getByText('Trùng giờ')).toBeTruthy();
    expect(screen.getByText('Chưa có phòng')).toBeTruthy();
    expect(screen.getByText('Lần 2')).toBeTruthy();
    expect(screen.getByText('Thứ Sáu, 20/11/2026')).toBeTruthy();
  });

  it('công tắc "Hiện buổi thi đã qua" tải lại với include_past=true', async () => {
    const api = mockApi({ 'GET /exams': { exams: [] }, 'GET /tags': [] });
    wrap(<ExamsScreen />);
    await waitFor(() => expect(api.calls('GET', '/exams?include_past=false')).toHaveLength(1));
    fireEvent.click(screen.getByRole('switch', { name: 'Hiện buổi thi đã qua' }));
    await waitFor(() => expect(api.calls('GET', '/exams?include_past=true')).toHaveLength(1));
  });

  it('xoá buổi thi phải xác nhận', async () => {
    const api = mockApi({
      'GET /exams': { exams: [makeExam({ id: 4 })] },
      'DELETE /exams/4': null,
      'GET /tags': [],
    });
    wrap(<ExamsScreen />);
    await screen.findByText('Cơ sở dữ liệu');
    fireEvent.click(screen.getByRole('button', { name: 'Xoá' }));
    expect(api.calls('DELETE', '/exams/4')).toHaveLength(0);
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Xoá' }));
    await waitFor(() => expect(api.calls('DELETE', '/exams/4')).toHaveLength(1));
  });

  it('thêm buổi thi gửi giờ, phòng trống là null và quan trọng bật sẵn', async () => {
    const api = mockApi({
      'GET /exams': { exams: [] },
      'GET /tags': [],
      'POST /exams': { exam: makeExam(), warnings: [] },
    });
    wrap(<ExamsScreen />);
    fireEvent.click(await screen.findByRole('button', { name: /Thêm buổi thi/ }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.change(within(dialog).getByLabelText('Tên học phần'), {
      target: { value: 'Đại số' },
    });
    fireEvent.change(within(dialog).getByLabelText('Ngày thi'), {
      target: { value: '01/12/2026' },
    });
    fireEvent.change(within(dialog).getByLabelText('Giờ bắt đầu'), { target: { value: '07:30' } });
    fireEvent.change(within(dialog).getByLabelText('Giờ kết thúc'), { target: { value: '08:30' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Lưu' }));
    await waitFor(() => expect(api.calls('POST', '/exams')).toHaveLength(1));
    const body = JSON.parse(api.calls('POST', '/exams')[0][1]!.body as string);
    expect(body).toMatchObject({
      course_name: 'Đại số',
      date: '2026-12-01',
      start_time: '07:30',
      end_time: '08:30',
      room: null,
      is_important: true,
      reminder_offsets: null,
    });
  });

  it('trang Hôm nay có khối "Buổi thi" phía trên buổi học', async () => {
    mockApi({
      'GET /today': {
        date: '2026-11-20',
        exams: [
          makeExam({ id: 1, conflicts: [{ kind: 'exam', id: 9, title: 'X', start_at: '' }] }),
        ],
        sessions: [],
        tasks_due_today: [],
        overdue_tasks: [],
        notices: [],
      },
    });
    wrap(<TodaySchedule />);
    const row = await screen.findByTestId('today-exam');
    expect(within(row).getByText('Cơ sở dữ liệu')).toBeTruthy();
    expect(within(row).getByText(/Chưa có phòng/)).toBeTruthy();
    expect(within(row).getByText(/SBD 125/)).toBeTruthy();
    expect(within(row).getByText('Trùng giờ')).toBeTruthy();
  });
});
