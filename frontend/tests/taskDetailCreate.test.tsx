import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  NewTaskPanel,
  parseNewTaskParams,
  type NewTaskDefaults,
} from '../src/features/tasks/TaskDetailPanel';
import { ToastProvider } from '../src/ui/Toast';
import { mockApi } from './apiMock';
import { makeTask } from './fixtures';

const LISTS = [
  {
    id: 4,
    name: 'Cá nhân',
    color: 'c03',
    is_default_study: false,
    open_task_count: 0,
    emoji: null,
  },
  { id: 1, name: 'Học tập', color: 'c01', is_default_study: true, open_task_count: 0, emoji: null },
];

function renderPanel(defaults: NewTaskDefaults) {
  const api = mockApi({
    'GET /lists': LISTS,
    'POST /tasks': (_url: string, init?: RequestInit) =>
      makeTask({ id: 42, ...JSON.parse(String(init?.body)) }),
  });
  const onCreated = vi.fn();
  const onClose = vi.fn();
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <MemoryRouter>
          <NewTaskPanel defaults={defaults} onCreated={onCreated} onClose={onClose} />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  return { api, onCreated, onClose };
}

const ONLY_DUE: NewTaskDefaults = {
  due_date: '2026-11-18',
  work_date: null,
  work_start: null,
  work_end: null,
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('parseNewTaskParams', () => {
  it('đọc due và khung giờ làm; bỏ giá trị sai hoặc thiếu', () => {
    expect(
      parseNewTaskParams(
        new URLSearchParams(
          'task=new&due=2026-11-18&work_date=2026-11-18&work_start=10:00&work_end=11:30',
        ),
      ),
    ).toEqual({
      due_date: '2026-11-18',
      work_date: '2026-11-18',
      work_start: '10:00',
      work_end: '11:30',
    });
    expect(parseNewTaskParams(new URLSearchParams('due=hôm-nay&work_date=2026-11-18'))).toEqual({
      due_date: null,
      work_date: null,
      work_start: null,
      work_end: null,
    });
  });
});

describe('NewTaskPanel — chế độ tạo mới (T068)', () => {
  it('con trỏ ở ô tiêu đề; các trường trống trừ giá trị truyền vào', async () => {
    renderPanel(ONLY_DUE);
    const input = screen.getByLabelText('Tiêu đề');
    expect(document.activeElement).toBe(input);
    expect((input as HTMLInputElement).value).toBe('');
    expect(screen.getByText('Thứ Tư, 18/11')).toBeTruthy();
  });

  it('Enter với tiêu đề → POST một lần (danh sách Học tập, hạn đã chọn) rồi onCreated', async () => {
    const { api, onCreated } = renderPanel({
      due_date: '2026-11-18',
      work_date: '2026-11-18',
      work_start: '10:00',
      work_end: '11:30',
    });
    await screen.findByText(/Học tập/);
    const input = screen.getByLabelText('Tiêu đề');
    fireEvent.change(input, { target: { value: '  Ôn tập chương 3 ' } });
    fireEvent.keyDown(input, { key: 'Enter' });
    fireEvent.blur(input);

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(42));
    const posts = api.calls('POST', '/tasks');
    expect(posts).toHaveLength(1);
    expect(JSON.parse(String(posts[0][1]?.body))).toMatchObject({
      title: 'Ôn tập chương 3',
      list_id: 1,
      due_date: '2026-11-18',
      due_time: null,
      work_date: '2026-11-18',
      work_start: '10:00',
      work_end: '11:30',
    });
  });

  it('rời ô tiêu đề khi còn trống thì không tạo gì', async () => {
    const { api } = renderPanel(ONLY_DUE);
    await screen.findByText(/Học tập/);
    fireEvent.blur(screen.getByLabelText('Tiêu đề'));
    expect(api.calls('POST', '/tasks')).toHaveLength(0);
  });

  it('Esc khi tiêu đề trống → đóng, không tạo gì', async () => {
    const { api, onClose } = renderPanel(ONLY_DUE);
    await screen.findByText(/Học tập/);
    fireEvent.keyDown(screen.getByLabelText('Tiêu đề'), { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
    expect(api.calls('POST', '/tasks')).toHaveLength(0);
  });

  it('Esc khi đã có tiêu đề → tạo rồi đóng', async () => {
    const { api, onClose, onCreated } = renderPanel(ONLY_DUE);
    await screen.findByText(/Học tập/);
    const input = screen.getByLabelText('Tiêu đề');
    fireEvent.change(input, { target: { value: 'Mua giấy thi' } });
    fireEvent.keyDown(input, { key: 'Escape' });
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(api.calls('POST', '/tasks')).toHaveLength(1);
    expect(onCreated).not.toHaveBeenCalled();
  });
});
