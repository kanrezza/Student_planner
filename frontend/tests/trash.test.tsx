import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TasksScreen } from '../src/features/tasks/TasksScreen';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeTask } from './fixtures';

const LISTS = [
  { id: 1, name: 'Học tập', color: 'c01', is_default_study: true, open_task_count: 1, emoji: null },
];
const COUNTS = { today: 1, tomorrow: 0, next7: 1, all: 1, lists: { '1': 1 } };

function renderAt(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/cong-viec/*" element={<TasksScreen />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('Thùng rác (US7)', () => {
  it('⌘⌫ chuyển task đang chọn vào Thùng rác, Hoàn tác gọi khôi phục', async () => {
    const task = makeTask({ id: 7, title: 'Nộp tiểu luận', due_date: '2099-01-01' });
    const api = mockApi({
      'GET /lists': LISTS,
      'GET /task-counts': COUNTS,
      'GET /tasks': [task],
      'DELETE /tasks/7': { ...task, deleted_at: '2026-11-09T09:00:00+07:00' },
      'POST /tasks/7/restore': { task, warnings: [] },
    });
    renderAt('/cong-viec/tat-ca');
    await screen.findByText('Nộp tiểu luận');
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    fireEvent.keyDown(window, { key: 'Backspace', metaKey: true });

    await waitFor(() => expect(api.calls('DELETE', '/tasks/7')).toHaveLength(1));
    const toast = await screen.findByText('Đã chuyển “Nộp tiểu luận” vào Thùng rác');
    fireEvent.click(within(toast.parentElement!).getByText('Hoàn tác'));
    await waitFor(() => expect(api.calls('POST', '/tasks/7/restore')).toHaveLength(1));
  });

  it('Thùng rác hiện "Còn N ngày", Khôi phục; Xoá vĩnh viễn và Dọn sạch hỏi xác nhận', async () => {
    const trashed = makeTask({
      id: 9,
      title: 'Bài cũ',
      deleted_at: '2026-11-01T10:00:00+07:00',
      days_left_in_trash: 22,
    });
    const api = mockApi({
      'GET /lists': LISTS,
      'GET /task-counts': COUNTS,
      'GET /tasks': [trashed],
      'POST /tasks/9/restore': { task: trashed, warnings: [] },
      'DELETE /tasks/9': null,
      'DELETE /trash': { deleted: 1 },
    });
    renderAt('/cong-viec/thung-rac');
    await screen.findByText('Bài cũ');
    expect(screen.getByText('Còn 22 ngày')).toBeTruthy();
    expect(screen.queryByRole('textbox', { name: 'Thêm công việc mới' })).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Khôi phục' }));
    await waitFor(() => expect(api.calls('POST', '/tasks/9/restore')).toHaveLength(1));

    fireEvent.click(screen.getByRole('button', { name: 'Xoá vĩnh viễn' }));
    const dialog = await screen.findByRole('dialog');
    expect(within(dialog).getByText('Xoá vĩnh viễn “Bài cũ”? Không thể khôi phục.')).toBeTruthy();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Xoá vĩnh viễn' }));
    await waitFor(() =>
      expect(api.fetchMock.mock.calls.some(([url]) => url === '/api/tasks/9?permanent=true')).toBe(
        true,
      ),
    );

    fireEvent.click(screen.getByRole('button', { name: 'Dọn sạch Thùng rác' }));
    const confirmEmpty = await screen.findByRole('dialog');
    fireEvent.click(within(confirmEmpty).getByRole('button', { name: 'Dọn sạch Thùng rác' }));
    await waitFor(() => expect(api.calls('DELETE', '/trash')).toHaveLength(1));
  });

  it('Thùng rác rỗng hiện "Thùng rác trống"', async () => {
    mockApi({ 'GET /lists': LISTS, 'GET /task-counts': COUNTS, 'GET /tasks': [] });
    renderAt('/cong-viec/thung-rac');
    expect(await screen.findByText('Thùng rác trống')).toBeTruthy();
  });
});
